from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Union
from app.core.config import settings

# 🔥 MUDANÇA IMPORTANTE: Usando argon2 em vez de bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash de senha com argon2 (NÃO TEM LIMITE DE TAMANHO)
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha plain corresponde ao hash
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Cria um JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # print(f"🔍 DEBUG - Criando token com dados: {to_encode}")
    # print(f"🔍 DEBUG - SECRET_KEY (primeiros 20 chars): {settings.SECRET_KEY[:20]}...")
    # print(f"🔍 DEBUG - ALGORITHM: {settings.ALGORITHM}")
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # print(f"🔍 DEBUG - Token criado: {encoded_jwt[:50]}...")
    
    return encoded_jwt

def create_verification_token(email: str = None):
    """
    Cria um token de verificação (para email, etc.)
    """
    to_encode = {"type": "verification"}
    if email:
        to_encode["email"] = email
        
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """
    Verifica e decodifica um JWT token
    """
    try:
        # print(f"🔍 DEBUG - Tentando decodificar token: {token[:50]}...")
        # print(f"🔍 DEBUG - SECRET_KEY (primeiros 20 chars): {settings.SECRET_KEY[:20]}...")
        # print(f"🔍 DEBUG - ALGORITHM: {settings.ALGORITHM}")
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # print(f"🔍 DEBUG - Token decodificado com sucesso: {payload}")
        
        return payload
    except JWTError as e:
        print(f"❌ DEBUG - Erro ao decodificar token: {type(e).__name__}: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ DEBUG - Erro inesperado ao decodificar token: {type(e).__name__}: {str(e)}")
        return None

def decode_access_token(token: str):
    """Alias para verify_token"""
    return verify_token(token)

def get_password_hash(password: str) -> str:
    """Alias para hash_password"""
    return hash_password(password)