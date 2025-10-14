#Configuracoes (DB, secrets, etc)
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    
    """Configurações da aplicação"""
    
    # Ambiente
    ENVIRONMENT: str = "development"
    
    # Database
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # Segurança JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 dias
    
    # AI
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "openai"  # openai ou anthropic
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@plataforma.ao"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "NERUS - Plataforma de Capacitação"
    
    # Logs
    LOG_LEVEL: str = "INFO"
    
    @property
    def DATABASE_URL(self) -> str:
        """Retorna URL de conexão com o MySQL"""
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instância global das configurações
settings = Settings()