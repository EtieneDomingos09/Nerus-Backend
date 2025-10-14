#Router principal V1
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, empresas, problemas, solucoes, ranking

# Router principal da API v1
api_router = APIRouter()

# Incluir todos os endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(users.router, prefix="/users", tags=["Usuários"])
api_router.include_router(empresas.router, prefix="/empresas", tags=["Empresas"])
api_router.include_router(problemas.router, prefix="/problemas", tags=["Problemas"])
api_router.include_router(solucoes.router, prefix="/solucoes", tags=["Soluções"])
api_router.include_router(ranking.router, prefix="/ranking", tags=["Rankings"])