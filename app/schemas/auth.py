#Login Resgistro e Tokens 
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

# ==================== REGISTER ====================

class UserRegister(BaseModel):
    """Schema para registro de usuário"""
    nome_completo: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    senha: str = Field(..., min_length=6)
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None
    area_interesse: Optional[str] = None
    nivel_educacao: Optional[str] = "medio"

class EmpresaRegister(BaseModel):
    """Schema para registro de empresa"""
    nome_empresa: str = Field(..., min_length=3, max_length=255)
    email_corporativo: EmailStr
    senha: str = Field(..., min_length=6)
    nif: Optional[str] = None
    telefone: Optional[str] = None
    setor_atuacao: Optional[str] = None
    tamanho_empresa: Optional[str] = "pequena"

# ==================== LOGIN ====================

class LoginRequest(BaseModel):
    """Schema para login"""
    email: EmailStr
    senha: str
    tipo_usuario: str = Field(..., pattern="^(user|empresa)$")  # user ou empresa

class LoginResponse(BaseModel):
    """Schema de resposta do login"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    nome: str
    email: str
    tipo_usuario: str
    email_verificado: bool

# ==================== TOKEN ====================

class TokenPayload(BaseModel):
    """Payload do JWT Token"""
    sub: int  # user_id ou empresa_id
    email: str
    tipo: str  # user ou empresa
    exp: Optional[int] = None

# ==================== EMAIL VERIFICATION ====================

class EmailVerification(BaseModel):
    """Schema para verificação de email"""
    token: str

class EmailVerificationResponse(BaseModel):
    """Resposta da verificação"""
    message: str
    email_verificado: bool