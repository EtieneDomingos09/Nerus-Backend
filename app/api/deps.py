#Dependencias (get_current_user, get_db, etc)
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
    
    # DEBUG: Imprimir token recebido
    # print(f"🔍 DEBUG - Token recebido: {token[:50]}...")
    
    # Decodificar token
    payload = decode_access_token(token)
    
    # # DEBUG: Imprimir payload
    # print(f"🔍 DEBUG - Payload decodificado: {payload}")
    
    if payload is None:
        print("❌ DEBUG - Token inválido ou expirado!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )
    
    user_id = payload.get("sub")
    tipo_usuario = payload.get("tipo")
    
    # Converter user_id de string para int
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        print("❌ DEBUG - user_id inválido!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # print(f"🔍 DEBUG - User ID: {user_id}, Tipo: {tipo_usuario}")
    
    if not user_id or not tipo_usuario:
        print("❌ DEBUG - Token sem user_id ou tipo_usuario!")
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
    
    # print(f"🔍 DEBUG - Usuário encontrado no banco: {user}")
    
    if not user:
        print("❌ DEBUG - Usuário não encontrado no banco!")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    if not user['ativo']:
        print("❌ DEBUG - Conta desativada!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada"
        )
    
    # Adicionar tipo ao objeto user
    user['tipo_usuario'] = tipo_usuario
    
    # print(f"✅ DEBUG - Autenticação bem-sucedida para user_id: {user_id}")
    
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