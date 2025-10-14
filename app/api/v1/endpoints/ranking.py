#GET rankings
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db

router = APIRouter()

# ==================== SCHEMAS ====================

class RankingUser(BaseModel):
    """Schema para usuário no ranking"""
    posicao: int
    id: int
    nome_completo: str
    foto_perfil: Optional[str] = None
    pontos_totais: int
    nivel_atual: int
    patente: str
    total_solucoes: int
    media_pontuacao: Optional[float] = None

class RankingMensal(BaseModel):
    """Schema para ranking mensal"""
    posicao: int
    id: int
    nome_completo: str
    foto_perfil: Optional[str] = None
    pontos_mes: int
    problemas_resolvidos: int
    mes: int
    ano: int

# ==================== RANKING GLOBAL ====================

@router.get("/global", response_model=List[dict])
def get_ranking_global(
    limit: int = Query(100, le=500),
    offset: int = 0,
    cursor = Depends(get_db)
):
    """
    Ranking global de todos os usuários
    Ordenado por pontos totais
    """
    
    query = """
    SELECT 
        ROW_NUMBER() OVER (ORDER BY u.pontos_totais DESC) as posicao,
        u.id,
        u.nome_completo,
        u.foto_perfil,
        u.pontos_totais,
        u.nivel_atual,
        u.patente,
        COUNT(DISTINCT s.id) as total_solucoes,
        AVG(s.pontuacao_final) as media_pontuacao
    FROM users u
    LEFT JOIN solucoes s ON u.id = s.user_id AND s.status = 'aprovada'
    WHERE u.ativo = TRUE
    GROUP BY u.id
    ORDER BY u.pontos_totais DESC
    LIMIT %s OFFSET %s
    """
    
    cursor.execute(query, (limit, offset))
    return cursor.fetchall()

# ==================== RANKING POR ÁREA ====================

@router.get("/por-area/{area}", response_model=List[dict])
def get_ranking_por_area(
    area: str,
    limit: int = Query(50, le=200),
    cursor = Depends(get_db)
):
    """
    Ranking de usuários por área específica
    Baseado em soluções aprovadas em problemas dessa área
    """
    
    query = """
    SELECT 
        ROW_NUMBER() OVER (ORDER BY SUM(s.pontos_ganhos) DESC) as posicao,
        u.id,
        u.nome_completo,
        u.foto_perfil,
        u.pontos_totais,
        u.nivel_atual,
        u.patente,
        SUM(s.pontos_ganhos) as pontos_area,
        COUNT(DISTINCT s.id) as solucoes_area,
        AVG(s.pontuacao_final) as media_pontuacao_area
    FROM users u
    INNER JOIN solucoes s ON u.id = s.user_id
    INNER JOIN problemas p ON s.problema_id = p.id
    WHERE u.ativo = TRUE 
        AND s.status = 'aprovada'
        AND p.area = %s
    GROUP BY u.id
    ORDER BY pontos_area DESC
    LIMIT %s
    """
    
    cursor.execute(query, (area, limit))
    return cursor.fetchall()

# ==================== RANKING MENSAL ====================

@router.get("/mensal", response_model=List[dict])
def get_ranking_mensal(
    mes: Optional[int] = None,
    ano: Optional[int] = None,
    limit: int = Query(100, le=500),
    cursor = Depends(get_db)
):
    """
    Ranking mensal baseado em pontos ganhos no mês
    Se não especificar mês/ano, usa o mês atual
    """
    
    from datetime import datetime
    
    if not mes or not ano:
        now = datetime.now()
        mes = now.month
        ano = now.year
    
    query = """
    SELECT 
        ROW_NUMBER() OVER (ORDER BY rm.pontos_mes DESC) as posicao,
        u.id,
        u.nome_completo,
        u.foto_perfil,
        rm.pontos_mes,
        rm.problemas_resolvidos,
        rm.mes,
        rm.ano
    FROM ranking_mensal rm
    INNER JOIN users u ON rm.user_id = u.id
    WHERE rm.mes = %s AND rm.ano = %s AND u.ativo = TRUE
    ORDER BY rm.pontos_mes DESC
    LIMIT %s
    """
    
    cursor.execute(query, (mes, ano, limit))
    return cursor.fetchall()

# ==================== RANKING SEMANAL ====================

@router.get("/semanal", response_model=List[dict])
def get_ranking_semanal(
    limit: int = Query(50, le=200),
    cursor = Depends(get_db)
):
    """
    Ranking dos últimos 7 dias
    Baseado em soluções aprovadas na última semana
    """
    
    query = """
    SELECT 
        ROW_NUMBER() OVER (ORDER BY SUM(s.pontos_ganhos) DESC) as posicao,
        u.id,
        u.nome_completo,
        u.foto_perfil,
        u.pontos_totais,
        u.patente,
        SUM(s.pontos_ganhos) as pontos_semana,
        COUNT(DISTINCT s.id) as solucoes_semana,
        AVG(s.pontuacao_final) as media_pontuacao
    FROM users u
    INNER JOIN solucoes s ON u.id = s.user_id
    WHERE u.ativo = TRUE 
        AND s.status = 'aprovada'
        AND s.data_avaliacao >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    GROUP BY u.id
    ORDER BY pontos_semana DESC
    LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    return cursor.fetchall()

# ==================== RANKING POR PATENTE ====================

@router.get("/por-patente/{patente}", response_model=List[dict])
def get_ranking_por_patente(
    patente: str,
    limit: int = Query(50, le=200),
    cursor = Depends(get_db)
):
    """
    Ranking de usuários dentro de uma patente específica
    """
    
    patentes_validas = ['iniciante', 'bronze', 'prata', 'ouro', 'platina', 'diamante']
    
    if patente not in patentes_validas:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patente inválida. Use: {', '.join(patentes_validas)}"
        )
    
    query = """
    SELECT 
        ROW_NUMBER() OVER (ORDER BY u.pontos_totais DESC) as posicao_patente,
        u.id,
        u.nome_completo,
        u.foto_perfil,
        u.pontos_totais,
        u.nivel_atual,
        u.patente,
        COUNT(DISTINCT s.id) as total_solucoes,
        AVG(s.pontuacao_final) as media_pontuacao
    FROM users u
    LEFT JOIN solucoes s ON u.id = s.user_id AND s.status = 'aprovada'
    WHERE u.ativo = TRUE AND u.patente = %s
    GROUP BY u.id
    ORDER BY u.pontos_totais DESC
    LIMIT %s
    """
    
    cursor.execute(query, (patente, limit))
    return cursor.fetchall()

# ==================== MINHA POSIÇÃO NO RANKING ====================

@router.get("/minha-posicao", response_model=dict)
def get_minha_posicao(cursor = Depends(get_db)):
    """
    Obter posição do usuário logado em diversos rankings
    """
    from app.api.deps import get_current_user
    from fastapi import Depends as FastAPIDepends
    
    current_user = FastAPIDepends(get_current_user)
    
    # Posição global
    cursor.execute("""
        SELECT COUNT(*) + 1 as posicao_global
        FROM users
        WHERE pontos_totais > (
            SELECT pontos_totais FROM users WHERE id = %s
        ) AND ativo = TRUE
    """, (current_user['id'],))
    
    global_rank = cursor.fetchone()
    
    # Posição mensal
    from datetime import datetime
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    
    cursor.execute("""
        SELECT pontos_mes, posicao_ranking
        FROM ranking_mensal
        WHERE user_id = %s AND mes = %s AND ano = %s
    """, (current_user['id'], mes_atual, ano_atual))
    
    mensal_rank = cursor.fetchone()
    
    # Dados do usuário
    cursor.execute("""
        SELECT pontos_totais, nivel_atual, patente
        FROM users WHERE id = %s
    """, (current_user['id'],))
    
    user_data = cursor.fetchone()
    
    return {
        "posicao_global": global_rank['posicao_global'],
        "posicao_mensal": mensal_rank['posicao_ranking'] if mensal_rank else None,
        "pontos_totais": user_data['pontos_totais'],
        "pontos_mes": mensal_rank['pontos_mes'] if mensal_rank else 0,
        "nivel_atual": user_data['nivel_atual'],
        "patente": user_data['patente']
    }

# ==================== TOP PERFORMERS ====================

@router.get("/top-performers", response_model=dict)
def get_top_performers(cursor = Depends(get_db)):
    """
    Estatísticas dos top performers da plataforma
    """
    
    # Top 3 global
    cursor.execute("""
        SELECT 
            u.id, u.nome_completo, u.foto_perfil, 
            u.pontos_totais, u.patente
        FROM users u
        WHERE u.ativo = TRUE
        ORDER BY u.pontos_totais DESC
        LIMIT 3
    """)
    top_3_global = cursor.fetchall()
    
    # Maior streak (mais dias consecutivos com atividade)
    cursor.execute("""
        SELECT 
            u.id, u.nome_completo, u.foto_perfil,
            COUNT(DISTINCT DATE(l.created_at)) as dias_ativos
        FROM users u
        INNER JOIN logs_atividade l ON u.id = l.user_id
        WHERE u.ativo = TRUE 
            AND l.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY u.id
        ORDER BY dias_ativos DESC
        LIMIT 3
    """)
    mais_consistentes = cursor.fetchall()
    
    # Melhor média de pontuação
    cursor.execute("""
        SELECT 
            u.id, u.nome_completo, u.foto_perfil,
            AVG(s.pontuacao_final) as media_pontuacao,
            COUNT(s.id) as total_solucoes
        FROM users u
        INNER JOIN solucoes s ON u.id = s.user_id
        WHERE u.ativo = TRUE 
            AND s.status = 'aprovada'
        GROUP BY u.id
        HAVING COUNT(s.id) >= 3
        ORDER BY media_pontuacao DESC
        LIMIT 3
    """)
    melhor_qualidade = cursor.fetchall()
    
    return {
        "top_3_global": top_3_global,
        "mais_consistentes": mais_consistentes,
        "melhor_qualidade": melhor_qualidade
    }

# ==================== ESTATÍSTICAS GERAIS ====================

@router.get("/estatisticas", response_model=dict)
def get_estatisticas_ranking(cursor = Depends(get_db)):
    """
    Estatísticas gerais dos rankings
    """
    
    # Total de usuários ativos
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE ativo = TRUE")
    total_users = cursor.fetchone()
    
    # Distribuição por patente
    cursor.execute("""
        SELECT patente, COUNT(*) as total
        FROM users
        WHERE ativo = TRUE
        GROUP BY patente
        ORDER BY 
            FIELD(patente, 'iniciante', 'bronze', 'prata', 'ouro', 'platina', 'diamante')
    """)
    por_patente = cursor.fetchall()
    
    # Média de pontos
    cursor.execute("""
        SELECT 
            AVG(pontos_totais) as media_pontos,
            MAX(pontos_totais) as max_pontos,
            MIN(pontos_totais) as min_pontos
        FROM users
        WHERE ativo = TRUE
    """)
    stats_pontos = cursor.fetchone()
    
    return {
        "total_usuarios_ativos": total_users['total'],
        "distribuicao_patentes": por_patente,
        "media_pontos": float(stats_pontos['media_pontos']) if stats_pontos['media_pontos'] else 0,
        "max_pontos": stats_pontos['max_pontos'],
        "min_pontos": stats_pontos['min_pontos']
    }