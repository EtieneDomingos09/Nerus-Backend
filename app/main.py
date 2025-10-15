#Arquivo Principal da API
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=" Nerus - API para Plataforma de Capacitação de Estudantes Angolanos",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas da API v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Rota de health check
@app.get("/")
def root():
    """Rota raiz - Health check"""
    return {
        "message": " Nerus - API da Plataforma de Capacitação está rodando! 🚀",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Executado quando a API inicia"""
    print(f"🚀 API iniciada no ambiente: {settings.ENVIRONMENT}")
    print(f"📚 Documentação disponível em: /docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Executado quando a API desliga"""
    print("🛑 API desligada")