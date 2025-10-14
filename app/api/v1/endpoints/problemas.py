#CRUD de problemas
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_empresa

router = APIRouter()

# ==================== SCHEMAS ====================

class ProblemaCreate(BaseModel):
    """Schema para criar problema"""
    titulo: str = Field(..., min_length=10, max_length=255)
    descricao: str = Field(..., min_length=50)
    contexto_empresa: Optional[str] = None
    area: str
    nivel_dificuldade: str = Field(..., pattern="^(iniciante|intermediario|avancado)$")
    tipo: str = Field("free", pattern="^(free|premium)$")
    objetivos: Optional[str] = None
    requisitos: Optional[str] = None
    recursos_fornecidos: Optional[str] = None
    prazo_dias: int = Field(30, ge=1, le=365)
    pontos_recompensa: int = Field(100, ge=50, le=10000)
    oferece_certificado: bool = False
    premio_descricao: Optional[str] = None
    data_inicio: date
    data_fim: date

class ProblemaResponse(BaseModel):
    """Schema de resposta do problema"""
    id: int
    empresa_id: int
    titulo: str
    descricao: str
    area: str
    nivel_dificuldade: str
    tipo: str
    pontos_recompensa: int
    oferece_certificado: bool
    status: str
    data_inicio: date
    data_fim: date
    visualizacoes: int
    nome_empresa: Optional[str] = None
    total_solucoes: Optional[int] = 0

# ==================== CRIAR PROBLEMA ====================

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def criar_problema(
    problema: ProblemaCreate,
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Criar novo problema/desafio (apenas empresas)"""
    
    # Verificar se empresa tem plano premium se problema for premium
    if problema.tipo == "premium":
        cursor.execute(
            "SELECT plano FROM empresas WHERE id = %s",
            (current_empresa['id'],)
        )
        empresa = cursor.fetchone()
        
        if empresa['plano'] != 'premium':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas empresas Premium podem criar problemas Premium"
            )
    
    # Inserir problema
    query = """
    INSERT INTO problemas (
        empresa_id, titulo, descricao, contexto_empresa, area,
        nivel_dificuldade, tipo, objetivos, requisitos, recursos_fornecidos,
        prazo_dias, pontos_recompensa, oferece_certificado, premio_descricao,
        data_inicio, data_fim
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(query, (
        current_empresa['id'],
        problema.titulo,
        problema.descricao,
        problema.contexto_empresa,
        problema.area,
        problema.nivel_dificuldade,
        problema.tipo,
        problema.objetivos,
        problema.requisitos,
        problema.recursos_fornecidos,
        problema.prazo_dias,
        problema.pontos_recompensa,
        problema.oferece_certificado,
        problema.premio_descricao,
        problema.data_inicio,
        problema.data_fim
    ))
    
    problema_id = cursor.lastrowid
    
    return {
        "message": "Problema criado com sucesso!",
        "problema_id": problema_id
    }

# ==================== LISTAR PROBLEMAS ====================

@router.get("/", response_model=List[dict])
def listar_problemas(
    area: Optional[str] = None,
    nivel: Optional[str] = None,
    tipo: Optional[str] = None,
    status_problema: str = "ativo",
    limit: int = Query(50, le=100),
    offset: int = 0,
    cursor = Depends(get_db)
):
    """Listar problemas ativos com filtros"""
    
    # Base query
    query = """
    SELECT 
        p.*,
        e.nome_empresa,
        e.logo_url as empresa_logo,
        COUNT(DISTINCT s.id) as total_solucoes
    FROM problemas p
    INNER JOIN empresas e ON p.empresa_id = e.id
    LEFT JOIN solucoes s ON p.id = s.problema_id
    WHERE p.status = %s
    """
    params = [status_problema]
    
    # Adicionar filtros
    if area:
        query += " AND p.area = %s"
        params.append(area)
    
    if nivel:
        query += " AND p.nivel_dificuldade = %s"
        params.append(nivel)
    
    if tipo:
        query += " AND p.tipo = %s"
        params.append(tipo)
    
    query += " GROUP BY p.id ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    problemas = cursor.fetchall()
    
    return problemas

# ==================== DETALHES DO PROBLEMA ====================

@router.get("/{problema_id}", response_model=dict)
def get_problema(
    problema_id: int,
    current_user = Depends(get_current_user),
    cursor = Depends(get_db)
):
    """Obter detalhes de um problema específico"""
    
    query = """
    SELECT 
        p.*,
        e.nome_empresa,
        e.logo_url as empresa_logo,
        e.descricao as empresa_descricao,
        COUNT(DISTINCT s.id) as total_solucoes,
        AVG(s.pontuacao_final) as media_pontuacao
    FROM problemas p
    INNER JOIN empresas e ON p.empresa_id = e.id
    LEFT JOIN solucoes s ON p.id = s.problema_id
    WHERE p.id = %s
    GROUP BY p.id
    """
    
    cursor.execute(query, (problema_id,))
    problema = cursor.fetchone()
    
    if not problema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problema não encontrado"
        )
    
    # Registrar visualização
    log_query = """
    INSERT INTO logs_atividade (user_id, tipo_usuario, acao, detalhes)
    VALUES (%s, %s, 'visualizar_problema', %s)
    """
    import json
    cursor.execute(log_query, (
        current_user['id'],
        current_user['tipo_usuario'],
        json.dumps({"problema_id": problema_id})
    ))
    
    return problema

# ==================== PROBLEMAS DA EMPRESA ====================

@router.get("/empresa/meus-problemas", response_model=List[dict])
def meus_problemas(
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Listar problemas da empresa logada"""
    
    query = """
    SELECT 
        p.*,
        COUNT(DISTINCT s.id) as total_solucoes,
        COUNT(DISTINCT CASE WHEN s.status = 'em_analise' THEN s.id END) as solucoes_pendentes,
        COUNT(DISTINCT CASE WHEN s.status = 'aprovada' THEN s.id END) as solucoes_aprovadas
    FROM problemas p
    LEFT JOIN solucoes s ON p.id = s.problema_id
    WHERE p.empresa_id = %s
    GROUP BY p.id
    ORDER BY p.created_at DESC
    """
    
    cursor.execute(query, (current_empresa['id'],))
    return cursor.fetchall()

# ==================== ATUALIZAR PROBLEMA ====================

@router.put("/{problema_id}", response_model=dict)
def atualizar_problema(
    problema_id: int,
    problema_update: ProblemaCreate,
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Atualizar problema (apenas pela empresa dona)"""
    
    # Verificar se problema pertence à empresa
    cursor.execute(
        "SELECT empresa_id FROM problemas WHERE id = %s",
        (problema_id,)
    )
    problema = cursor.fetchone()
    
    if not problema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problema não encontrado"
        )
    
    if problema['empresa_id'] != current_empresa['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar este problema"
        )
    
    # Atualizar
    query = """
    UPDATE problemas SET
        titulo = %s, descricao = %s, contexto_empresa = %s,
        area = %s, nivel_dificuldade = %s, objetivos = %s,
        requisitos = %s, recursos_fornecidos = %s,
        pontos_recompensa = %s, oferece_certificado = %s,
        premio_descricao = %s, data_fim = %s
    WHERE id = %s
    """
    
    cursor.execute(query, (
        problema_update.titulo,
        problema_update.descricao,
        problema_update.contexto_empresa,
        problema_update.area,
        problema_update.nivel_dificuldade,
        problema_update.objetivos,
        problema_update.requisitos,
        problema_update.recursos_fornecidos,
        problema_update.pontos_recompensa,
        problema_update.oferece_certificado,
        problema_update.premio_descricao,
        problema_update.data_fim,
        problema_id
    ))
    
    return {"message": "Problema atualizado com sucesso!"}

# ==================== FECHAR PROBLEMA ====================

@router.patch("/{problema_id}/fechar", response_model=dict)
def fechar_problema(
    problema_id: int,
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Fechar problema para novas submissões"""
    
    cursor.execute(
        "SELECT empresa_id FROM problemas WHERE id = %s",
        (problema_id,)
    )
    problema = cursor.fetchone()
    
    if not problema or problema['empresa_id'] != current_empresa['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    cursor.execute(
        "UPDATE problemas SET status = 'fechado' WHERE id = %s",
        (problema_id,)
    )
    
    return {"message": "Problema fechado com sucesso!"}