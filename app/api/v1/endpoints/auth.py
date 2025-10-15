from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth import (
    UserRegister, EmpresaRegister, LoginRequest, LoginResponse,
    EmailVerification, EmailVerificationResponse
)
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_verification_token
from app.api.deps import get_current_user
from mysql.connector import IntegrityError

router = APIRouter()
security = HTTPBearer()

# ==================== REGISTER USER ====================

@router.post("/register/user", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, cursor = Depends(get_db)):
    """Registrar novo estudante/profissional"""
    
    # Hash da senha
    senha_hash = hash_password(user_data.senha)
    
    # Token de verificação
    token_verificacao = create_verification_token()
    
    try:
        query = """
        INSERT INTO users (
            nome_completo, email, senha_hash, telefone, data_nascimento,
            area_interesse, nivel_educacao, token_verificacao
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            user_data.nome_completo,
            user_data.email,
            senha_hash,
            user_data.telefone,
            user_data.data_nascimento,
            user_data.area_interesse,
            user_data.nivel_educacao,
            token_verificacao
        ))
        
        user_id = cursor.lastrowid
        
        # TODO: Enviar email de verificação aqui
        # send_verification_email(user_data.email, token_verificacao)
        
        return {
            "message": "Usuário criado com sucesso! Verifique seu email.",
            "user_id": user_id,
            "verification_token": token_verificacao  # Remover em produção
        }
        
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )

# ==================== REGISTER EMPRESA ====================

@router.post("/register/empresa", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_empresa(empresa_data: EmpresaRegister, cursor = Depends(get_db)):
    """Registrar nova empresa"""
    
    senha_hash = hash_password(empresa_data.senha)
    token_verificacao = create_verification_token()
    
    try:
        query = """
        INSERT INTO empresas (
            nome_empresa, email_corporativo, senha_hash, nif, telefone,
            setor_atuacao, tamanho_empresa, token_verificacao
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            empresa_data.nome_empresa,
            empresa_data.email_corporativo,
            senha_hash,
            empresa_data.nif,
            empresa_data.telefone,
            empresa_data.setor_atuacao,
            empresa_data.tamanho_empresa,
            token_verificacao
        ))
        
        empresa_id = cursor.lastrowid
        
        return {
            "message": "Empresa criada com sucesso! Verifique seu email.",
            "empresa_id": empresa_id,
            "verification_token": token_verificacao
        }
        
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ou NIF já cadastrado"
        )

# ==================== LOGIN ====================

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, cursor = Depends(get_db)):
    """Login de usuário ou empresa"""
    
    # Determinar tabela baseado no tipo
    if credentials.tipo_usuario == "user":
        query = """
        SELECT id, nome_completo as nome, email, senha_hash, email_verificado
        FROM users WHERE email = %s AND ativo = TRUE
        """
    else:
        query = """
        SELECT id, nome_empresa as nome, email_corporativo as email, senha_hash, email_verificado
        FROM empresas WHERE email_corporativo = %s AND ativo = TRUE
        """
    
    cursor.execute(query, (credentials.email,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    # Verificar senha
    if not verify_password(credentials.senha, user['senha_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    # Criar token JWT
    token_data = {
        "sub": str(user['id']),  # ✅ Converter para string
        "email": user['email'],
        "tipo": credentials.tipo_usuario
    }
    access_token = create_access_token(token_data)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user['id'],
        nome=user['nome'],
        email=user['email'],
        tipo_usuario=credentials.tipo_usuario,
        email_verificado=user['email_verificado']
    )

# ==================== VERIFY EMAIL ====================

@router.post("/verify-email", response_model=EmailVerificationResponse)
def verify_email(verification: EmailVerification, cursor = Depends(get_db)):
    """Verificar email do usuário"""
    
    # Tentar em users
    cursor.execute(
        "SELECT id, email FROM users WHERE token_verificacao = %s",
        (verification.token,)
    )
    user = cursor.fetchone()
    
    if user:
        cursor.execute(
            "UPDATE users SET email_verificado = TRUE, token_verificacao = NULL WHERE id = %s",
            (user['id'],)
        )
        return EmailVerificationResponse(
            message="Email verificado com sucesso!",
            email_verificado=True
        )
    
    # Tentar em empresas
    cursor.execute(
        "SELECT id, email_corporativo FROM empresas WHERE token_verificacao = %s",
        (verification.token,)
    )
    empresa = cursor.fetchone()
    
    if empresa:
        cursor.execute(
            "UPDATE empresas SET email_verificado = TRUE, token_verificacao = NULL WHERE id = %s",
            (empresa['id'],)
        )
        return EmailVerificationResponse(
            message="Email verificado com sucesso!",
            email_verificado=True
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token de verificação inválido ou expirado"
    )

# ==================== ME ====================

@router.get("/me")
def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Obter informações do usuário atual (requer autenticação)"""
    
    return {
        "user_id": current_user['id'],
        "nome": current_user.get('nome_completo'),
        "email": current_user['email'],
        "tipo": current_user['tipo_usuario'],
        "email_verificado": current_user['email_verificado']
    }

# ==================== DEBUG TOKEN (TEMPORÁRIO) ====================

# @router.get("/debug-token")
# def debug_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """Debug do token - REMOVER EM PRODUÇÃO"""
#     from app.core.security import decode_access_token
    
#     token = credentials.credentials
#     payload = decode_access_token(token)
    
#     return {
#         "token_recebido": token[:50] + "...",
#         "payload_decodificado": payload,
#         "token_valido": payload is not None
#     }