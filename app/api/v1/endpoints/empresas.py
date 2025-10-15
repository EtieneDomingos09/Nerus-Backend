#CRUD empresas 
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from app.core.database import get_db
from app.api.deps import get_current_empresa, get_current_user
from app.core.security import hash_password, verify_password

router = APIRouter()

# ==================== SCHEMAS ====================

class EmpresaProfile(BaseModel):
    """Schema do perfil da empresa"""
    id: int
    nome_empresa: str
    email_corporativo: str
    nif: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    provincia: Optional[str] = None
    municipio: Optional[str] = None
    setor_atuacao: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    logo_url: Optional[str] = None
    email_verificado: bool
    ativo: bool
    created_at: str

class EmpresaUpdate(BaseModel):
    """Schema para atualizar empresa"""
    nome_empresa: Optional[str] = Field(None, min_length=3, max_length=255)
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    provincia: Optional[str] = None
    municipio: Optional[str] = None
    setor_atuacao: Optional[str] = None
    website: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None
    descricao: Optional[str] = Field(None, max_length=2000)

class EmpresaStats(BaseModel):
    """Estatísticas da empresa"""
    total_problemas: int
    problemas_ativos: int
    problemas_fechados: int
    total_solucoes_recebidas: int
    solucoes_pendentes: int
    solucoes_aprovadas: int
    total_certificados_emitidos: int
    total_usuarios_participantes: int

class EmpresaPublic(BaseModel):
    """Perfil público da empresa (para usuários)"""
    id: int
    nome_empresa: str
    logo_url: Optional[str] = None
    setor_atuacao: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    descricao: Optional[str] = None
    total_problemas_ativos: int
    created_at: str

# ==================== PERFIL DA EMPRESA ====================

@router.get("/me", response_model=EmpresaProfile)
def get_my_profile(
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Obter perfil completo da empresa logada"""
    
    cursor.execute(
        "SELECT * FROM empresas WHERE id = %s",
        (current_empresa['id'],)
    )
    
    empresa = cursor.fetchone()
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    return empresa

@router.get("/{empresa_id}", response_model=EmpresaPublic)
def get_empresa_profile(
    empresa_id: int,
    cursor = Depends(get_db)
):
    """Obter perfil público de uma empresa"""
    
    query = """
    SELECT 
        e.*,
        COUNT(DISTINCT p.id) as total_problemas_ativos
    FROM empresas e
    LEFT JOIN problemas p ON e.id = p.empresa_id AND p.status = 'ativo'
    WHERE e.id = %s AND e.ativo = TRUE
    GROUP BY e.id
    """
    
    cursor.execute(query, (empresa_id,))
    empresa = cursor.fetchone()
    
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    return empresa

# ==================== ATUALIZAR PERFIL ====================

@router.put("/me", response_model=dict)
def update_my_profile(
    empresa_update: EmpresaUpdate,
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Atualizar perfil da empresa logada"""
    
    update_fields = []
    values = []
    
    if empresa_update.nome_empresa:
        update_fields.append("nome_empresa = %s")
        values.append(empresa_update.nome_empresa)
    
    if empresa_update.telefone:
        update_fields.append("telefone = %s")
        values.append(empresa_update.telefone)
    
    if empresa_update.endereco:
        update_fields.append("endereco = %s")
        values.append(empresa_update.endereco)
    
    if empresa_update.provincia:
        update_fields.append("provincia = %s")
        values.append(empresa_update.provincia)
    
    if empresa_update.municipio:
        update_fields.append("municipio = %s")
        values.append(empresa_update.municipio)
    
    if empresa_update.setor_atuacao:
        update_fields.append("setor_atuacao = %s")
        values.append(empresa_update.setor_atuacao)
    
    if empresa_update.website:
        update_fields.append("website = %s")
        values.append(str(empresa_update.website))
    
    if empresa_update.linkedin_url:
        update_fields.append("linkedin_url = %s")
        values.append(str(empresa_update.linkedin_url))
    
    if empresa_update.descricao:
        update_fields.append("descricao = %s")
        values.append(empresa_update.descricao)
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar"
        )
    
    values.append(current_empresa['id'])
    
    query = f"UPDATE empresas SET {', '.join(update_fields)} WHERE id = %s"
    cursor.execute(query, values)
    
    return {"message": "Perfil da empresa atualizado com sucesso!"}

# ==================== ESTATÍSTICAS DA EMPRESA ====================

@router.get("/me/stats", response_model=EmpresaStats)
def get_my_stats(
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Obter estatísticas completas da empresa"""
    
    # Estatísticas de problemas
    cursor.execute("""
        SELECT 
            COUNT(*) as total_problemas,
            SUM(CASE WHEN status = 'ativo' THEN 1 ELSE 0 END) as ativos,
            SUM(CASE WHEN status = 'fechado' THEN 1 ELSE 0 END) as fechados
        FROM problemas
        WHERE empresa_id = %s
    """, (current_empresa['id'],))
    
    stats_problemas = cursor.fetchone()
    
    # Estatísticas de soluções
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT s.id) as total_solucoes,
            SUM(CASE WHEN s.status = 'em_analise' THEN 1 ELSE 0 END) as pendentes,
            SUM(CASE WHEN s.status = 'aprovada' THEN 1 ELSE 0 END) as aprovadas,
            COUNT(DISTINCT s.user_id) as usuarios_participantes
        FROM solucoes s
        INNER JOIN problemas p ON s.problema_id = p.id
        WHERE p.empresa_id = %s
    """, (current_empresa['id'],))
    
    stats_solucoes = cursor.fetchone()
    
    # Certificados emitidos
    cursor.execute("""
        SELECT COUNT(*) as total_certificados
        FROM certificados
        WHERE empresa_id = %s
    """, (current_empresa['id'],))
    
    stats_certificados = cursor.fetchone()
    
    return {
        "total_problemas": stats_problemas['total_problemas'] or 0,
        "problemas_ativos": stats_problemas['ativos'] or 0,
        "problemas_fechados": stats_problemas['fechados'] or 0,
        "total_solucoes_recebidas": stats_solucoes['total_solucoes'] or 0,
        "solucoes_pendentes": stats_solucoes['pendentes'] or 0,
        "solucoes_aprovadas": stats_solucoes['aprovadas'] or 0,
        "total_certificados_emitidos": stats_certificados['total_certificados'] or 0,
        "total_usuarios_participantes": stats_solucoes['usuarios_participantes'] or 0
    }

# ==================== LISTAR EMPRESAS (PÚBLICO) ====================

@router.get("/", response_model=List[EmpresaPublic])
def listar_empresas(
    setor: Optional[str] = None,
    provincia: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    cursor = Depends(get_db)
):
    """Listar empresas ativas na plataforma"""
    
    query = """
    SELECT 
        e.*,
        COUNT(DISTINCT p.id) as total_problemas_ativos
    FROM empresas e
    LEFT JOIN problemas p ON e.id = p.empresa_id AND p.status = 'ativo'
    WHERE e.ativo = TRUE
    """
    params = []
    
    if setor:
        query += " AND e.setor_atuacao = %s"
        params.append(setor)
    
    if provincia:
        query += " AND e.provincia = %s"
        params.append(provincia)
    
    query += " GROUP BY e.id ORDER BY total_problemas_ativos DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    return cursor.fetchall()

# ==================== TOP EMPRESAS ====================

@router.get("/top/ativas", response_model=List[dict])
def get_top_empresas(
    limit: int = Query(10, le=50),
    cursor = Depends(get_db)
):
    """Top empresas mais ativas (mais problemas publicados)"""
    
    query = """
    SELECT 
        e.id,
        e.nome_empresa,
        e.logo_url,
        e.setor_atuacao,
        COUNT(DISTINCT p.id) as total_problemas,
        COUNT(DISTINCT s.id) as total_solucoes,
        COUNT(DISTINCT s.user_id) as usuarios_engajados
    FROM empresas e
    LEFT JOIN problemas p ON e.id = p.empresa_id
    LEFT JOIN solucoes s ON p.id = s.problema_id
    WHERE e.ativo = TRUE
    GROUP BY e.id
    ORDER BY total_problemas DESC, total_solucoes DESC
    LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    return cursor.fetchall()

# ==================== MUDAR SENHA ====================

@router.post("/me/change-password", response_model=dict)
def change_password(
    senha_atual: str,
    senha_nova: str = Field(..., min_length=6),
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Alterar senha da empresa"""
    
    # Buscar senha atual
    cursor.execute(
        "SELECT senha_hash FROM empresas WHERE id = %s",
        (current_empresa['id'],)
    )
    
    empresa = cursor.fetchone()
    
    # Verificar senha atual
    if not verify_password(senha_atual, empresa['senha_hash']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Atualizar senha
    nova_senha_hash = hash_password(senha_nova)
    
    cursor.execute(
        "UPDATE empresas SET senha_hash = %s WHERE id = %s",
        (nova_senha_hash, current_empresa['id'])
    )
    
    return {"message": "Senha alterada com sucesso!"}

# ==================== DESATIVAR CONTA ====================

@router.delete("/me/deactivate", response_model=dict)
def deactivate_account(
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Desativar conta da empresa"""
    
    cursor.execute(
        "UPDATE empresas SET ativo = FALSE WHERE id = %s",
        (current_empresa['id'],)
    )
    
    return {"message": "Conta desativada. Entre em contato com o suporte para reativar."}

# ==================== SETORES DISPONÍVEIS ====================

@router.get("/setores", response_model=List[dict])
def get_setores_disponiveis(cursor = Depends(get_db)):
    """Listar setores de atuação com quantidade de empresas"""
    
    cursor.execute("""
        SELECT 
            setor_atuacao,
            COUNT(*) as total_empresas
        FROM empresas
        WHERE ativo = TRUE AND setor_atuacao IS NOT NULL
        GROUP BY setor_atuacao
        ORDER BY total_empresas DESC
    """)
    
    return cursor.fetchall()