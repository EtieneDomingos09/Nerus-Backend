#CRUD e soluções + avaliacoes AI
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_empresa
import json

router = APIRouter()

# ==================== SCHEMAS ====================

class SolucaoCreate(BaseModel):
    """Schema para submeter solução"""
    problema_id: int
    descricao_solucao: str = Field(..., min_length=100)
    link_repositorio: Optional[str] = None
    link_demo: Optional[str] = None

class SolucaoResponse(BaseModel):
    """Schema de resposta da solução"""
    id: int
    problema_id: int
    user_id: int
    descricao_solucao: str
    pontuacao_final: Optional[float] = None
    pontos_ganhos: int
    status: str
    feedback_ai: Optional[str] = None

# ==================== SUBMETER SOLUÇÃO ====================

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def submeter_solucao(
    solucao: SolucaoCreate,
    current_user = Depends(get_current_user),
    cursor = Depends(get_db)
):
    """Submeter solução para um problema"""
    
    # Verificar se problema existe e está ativo
    cursor.execute(
        "SELECT * FROM problemas WHERE id = %s AND status = 'ativo'",
        (solucao.problema_id,)
    )
    problema = cursor.fetchone()
    
    if not problema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problema não encontrado ou não está mais ativo"
        )
    
    # Verificar se usuário já submeteu solução para este problema
    cursor.execute(
        "SELECT id FROM solucoes WHERE user_id = %s AND problema_id = %s",
        (current_user['id'], solucao.problema_id)
    )
    
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você já submeteu uma solução para este problema"
        )
    
    # Inserir solução
    query = """
    INSERT INTO solucoes (
        problema_id, user_id, descricao_solucao,
        link_repositorio, link_demo, status
    ) VALUES (%s, %s, %s, %s, %s, 'em_analise')
    """
    
    cursor.execute(query, (
        solucao.problema_id,
        current_user['id'],
        solucao.descricao_solucao,
        solucao.link_repositorio,
        solucao.link_demo
    ))
    
    solucao_id = cursor.lastrowid
    
    # ========== ANÁLISE POR AI (Assíncrono) ==========
    try:
        from app.services.ai_service import analisar_solucao
        
        # Analisar com AI
        analise = await analisar_solucao(
            problema=problema,
            solucao_texto=solucao.descricao_solucao
        )
        
        # Atualizar solução com análise da AI
        update_query = """
        UPDATE solucoes SET
            analise_ai = %s,
            pontuacao_ai = %s,
            feedback_ai = %s,
            pontos_ganhos = %s,
            pontuacao_final = %s,
            status = %s,
            data_avaliacao = NOW()
        WHERE id = %s
        """
        
        status_final = 'aprovada' if analise['pontuacao'] >= 60 else 'reprovada'
        pontos = problema['pontos_recompensa'] if status_final == 'aprovada' else 0
        
        cursor.execute(update_query, (
            json.dumps(analise),
            analise['pontuacao'],
            analise['feedback'],
            pontos,
            analise['pontuacao'],
            status_final,
            solucao_id
        ))
        
        return {
            "message": "Solução submetida e avaliada com sucesso!",
            "solucao_id": solucao_id,
            "status": status_final,
            "pontuacao": analise['pontuacao'],
            "pontos_ganhos": pontos,
            "feedback": analise['feedback']
        }
        
    except Exception as e:
        # Se AI falhar, apenas marca como pendente de análise
        print(f"Erro na análise AI: {e}")
        return {
            "message": "Solução submetida! Aguardando análise.",
            "solucao_id": solucao_id,
            "status": "em_analise"
        }

# ==================== MINHAS SOLUÇÕES ====================

@router.get("/minhas-solucoes", response_model=List[dict])
def minhas_solucoes(
    current_user = Depends(get_current_user),
    cursor = Depends(get_db)
):
    """Listar soluções do usuário logado"""
    
    query = """
    SELECT 
        s.*,
        p.titulo as problema_titulo,
        p.area,
        p.pontos_recompensa,
        e.nome_empresa
    FROM solucoes s
    INNER JOIN problemas p ON s.problema_id = p.id
    INNER JOIN empresas e ON p.empresa_id = e.id
    WHERE s.user_id = %s
    ORDER BY s.data_submissao DESC
    """
    
    cursor.execute(query, (current_user['id'],))
    return cursor.fetchall()

# ==================== DETALHES DA SOLUÇÃO ====================

@router.get("/{solucao_id}", response_model=dict)
def get_solucao(
    solucao_id: int,
    current_user = Depends(get_current_user),
    cursor = Depends(get_db)
):
    """Obter detalhes de uma solução específica"""
    
    query = """
    SELECT 
        s.*,
        p.titulo as problema_titulo,
        p.descricao as problema_descricao,
        p.area,
        u.nome_completo as solucionador_nome,
        e.nome_empresa
    FROM solucoes s
    INNER JOIN problemas p ON s.problema_id = p.id
    INNER JOIN users u ON s.user_id = u.id
    INNER JOIN empresas e ON p.empresa_id = e.id
    WHERE s.id = %s
    """
    
    cursor.execute(query, (solucao_id,))
    solucao = cursor.fetchone()
    
    if not solucao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solução não encontrada"
        )
    
    # Verificar permissão (só pode ver: autor, empresa dona do problema, ou admin)
    if current_user['tipo_usuario'] == 'user':
        if solucao['user_id'] != current_user['id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para ver esta solução"
            )
    elif current_user['tipo_usuario'] == 'empresa':
        cursor.execute(
            "SELECT empresa_id FROM problemas WHERE id = %s",
            (solucao['problema_id'],)
        )
        problema = cursor.fetchone()
        if problema['empresa_id'] != current_user['id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para ver esta solução"
            )
    
    return solucao

# ==================== SOLUÇÕES DE UM PROBLEMA (EMPRESA) ====================

@router.get("/problema/{problema_id}/solucoes", response_model=List[dict])
def solucoes_do_problema(
    problema_id: int,
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Listar todas as soluções de um problema (apenas empresa dona)"""
    
    # Verificar se problema pertence à empresa
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
    
    # Buscar soluções
    query = """
    SELECT 
        s.*,
        u.nome_completo,
        u.email,
        u.pontos_totais,
        u.nivel_atual,
        u.patente
    FROM solucoes s
    INNER JOIN users u ON s.user_id = u.id
    WHERE s.problema_id = %s
    ORDER BY s.pontuacao_final DESC, s.data_submissao ASC
    """
    
    cursor.execute(query, (problema_id,))
    return cursor.fetchall()

# ==================== AVALIAR MANUALMENTE (EMPRESA) ====================

@router.patch("/{solucao_id}/avaliar", response_model=dict)
def avaliar_solucao(
    solucao_id: int,
    avaliacao: str,
    pontuacao: float = Field(..., ge=0, le=100),
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Empresa pode adicionar avaliação manual (complementar à AI)"""
    
    # Verificar permissões
    cursor.execute("""
        SELECT s.*, p.empresa_id, p.pontos_recompensa
        FROM solucoes s
        INNER JOIN problemas p ON s.problema_id = p.id
        WHERE s.id = %s
    """, (solucao_id,))
    
    solucao = cursor.fetchone()
    
    if not solucao or solucao['empresa_id'] != current_empresa['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão"
        )
    
    # Atualizar com avaliação da empresa
    query = """
    UPDATE solucoes SET
        avaliacao_empresa = %s,
        pontuacao_empresa = %s,
        pontuacao_final = (COALESCE(pontuacao_ai, 0) + %s) / 2
    WHERE id = %s
    """
    
    cursor.execute(query, (avaliacao, pontuacao, pontuacao, solucao_id))
    
    return {"message": "Avaliação registrada com sucesso!"}