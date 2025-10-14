#Dependecias (get_current_user, get_db, etc)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.core.database import get_db

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    cursor = Depends(get_db)
):
    """
    Dependency para pegar o usuário atual autenticado
    Verifica o token JWT e retorna os dados do usuário
    """
    token = credentials.credentials
    
    # Decodificar token
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )
    
    user_id = payload.get("sub")
    tipo_usuario = payload.get("tipo")
    
    if not user_id or not tipo_usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # Buscar usuário no banco
    if tipo_usuario == "user":
        cursor.execute(
            "SELECT id, nome_completo, email, email_verificado, ativo FROM users WHERE id = %s",
            (user_id,)
        )
    else:  # empresa
        cursor.execute(
            "SELECT id, nome_empresa as nome_completo, email_corporativo as email, email_verificado, ativo FROM empresas WHERE id = %s",
            (user_id,)
        )
    
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    if not user['ativo']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada"
        )
    
    # Adicionar tipo ao objeto user
    user['tipo_usuario'] = tipo_usuario
    
    return user

def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """
    Dependency que requer usuário com email verificado
    """
    if not current_user['email_verificado']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não verificado. Verifique seu email."
        )
    return current_user

def get_current_empresa(current_user: dict = Depends(get_current_user)):
    """
    Dependency que requer que o usuário seja uma empresa
    """
    if current_user['tipo_usuario'] != 'empresa':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a empresas"
        )
    return current_user