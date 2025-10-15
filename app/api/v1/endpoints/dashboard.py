from fastapi import APIRouter, Depends
from typing import Dict, List
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_empresa

router = APIRouter()

# ==================== DASHBOARD GERAL DA PLATAFORMA ====================

@router.get("/stats", response_model=Dict)
def get_platform_stats(cursor = Depends(get_db)):
    """
    Estatísticas gerais da plataforma (público)
    """
    
    # Total de usuários ativos
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM users
        WHERE ativo = TRUE
    """)
    total_users = cursor.fetchone()
    
    # Total de empresas ativas
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM empresas
        WHERE ativo = TRUE
    """)
    total_empresas = cursor.fetchone()
    
    # Total de problemas
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'ativo' THEN 1 ELSE 0 END) as ativos
        FROM problemas
    """)
    stats_problemas = cursor.fetchone()
    
    # Total de soluções
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'aprovada' THEN 1 ELSE 0 END) as aprovadas
        FROM solucoes
    """)
    stats_solucoes = cursor.fetchone()
    
    # Certificados emitidos
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM certificados
    """)
    total_certificados = cursor.fetchone()
    
    return {
        "usuarios_ativos": total_users['total'],
        "empresas_ativas": total_empresas['total'],
        "problemas_publicados": stats_problemas['total'],
        "problemas_ativos": stats_problemas['ativos'],
        "solucoes_submetidas": stats_solucoes['total'],
        "solucoes_aprovadas": stats_solucoes['aprovadas'],
        "certificados_emitidos": total_certificados['total']
    }

# ==================== DASHBOARD DO USUÁRIO ====================

@router.get("/user/overview", response_model=Dict)
def get_user_dashboard(
    current_user = Depends(get_current_user),
    cursor = Depends(get_db)
):
    """
    Dashboard completo do usuário logado
    """
    
    # Dados básicos do usuário
    cursor.execute("""
        SELECT 
            pontos_totais,
            nivel_atual,
            patente,
            created_at
        FROM users
        WHERE id = %s
    """, (current_user['id'],))
    user_data = cursor.fetchone()
    
    # Estatísticas de soluções
    cursor.execute("""
        SELECT 
            COUNT(*) as total_solucoes,
            SUM(CASE WHEN status = 'aprovada' THEN 1 ELSE 0 END) as aprovadas,
            SUM(CASE WHEN status = 'em_analise' THEN 1 ELSE 0 END) as pendentes,
            SUM(CASE WHEN status = 'reprovada' THEN 1 ELSE 0 END) as reprovadas,
            AVG(pontuacao_final) as media_pontuacao,
            SUM(pontos_ganhos) as total_pontos_ganhos
        FROM solucoes
        WHERE user_id = %s
    """, (current_user['id'],))
    stats_solucoes = cursor.fetchone()
    
    # Posição no ranking global
    cursor.execute("""
        SELECT COUNT(*) + 1 as posicao_global
        FROM users
        WHERE pontos_totais > %s AND ativo = TRUE
    """, (user_data['pontos_totais'],))
    ranking = cursor.fetchone()
    
    # Certificados obtidos
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM certificados
        WHERE user_id = %s
    """, (current_user['id'],))
    certificados = cursor.fetchone()
    
    # Atividade recente (últimas 5 ações)
    cursor.execute("""
        SELECT 
            acao,
            detalhes,
            created_at
        FROM logs_atividade
        WHERE user_id = %s AND tipo_usuario = 'user'
        ORDER BY created_at DESC
        LIMIT 5
    """, (current_user['id'],))
    atividades_recentes = cursor.fetchall()
    
    # Próximos problemas recomendados (baseado em área de interesse)
    cursor.execute("""
        SELECT 
            p.id,
            p.titulo,
            p.area,
            p.nivel_dificuldade,
            p.pontos_recompensa,
            p.data_fim,
            e.nome_empresa,
            e.logo_url
        FROM problemas p
        INNER JOIN empresas e ON p.empresa_id = e.id
        LEFT JOIN solucoes s ON p.id = s.problema_id AND s.user_id = %s
        WHERE p.status = 'ativo' 
            AND s.id IS NULL
            AND (p.area = %s OR %s IS NULL)
        ORDER BY p.created_at DESC
        LIMIT 5
    """, (current_user['id'], current_user.get('area_interesse'), current_user.get('area_interesse')))
    problemas_recomendados = cursor.fetchall()
    
    # Progresso semanal (últimos 7 dias)
    cursor.execute("""
        SELECT 
            DATE(created_at) as data,
            COUNT(*) as atividades
        FROM logs_atividade
        WHERE user_id = %s 
            AND tipo_usuario = 'user'
            AND created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY data
    """, (current_user['id'],))
    progresso_semanal = cursor.fetchall()
    
    return {
        "usuario": {
            "pontos_totais": user_data['pontos_totais'],
            "nivel_atual": user_data['nivel_atual'],
            "patente": user_data['patente'],
            "posicao_ranking": ranking['posicao_global'],
            "membro_desde": user_data['created_at']
        },
        "solucoes": {
            "total": stats_solucoes['total_solucoes'] or 0,
            "aprovadas": stats_solucoes['aprovadas'] or 0,
            "pendentes": stats_solucoes['pendentes'] or 0,
            "reprovadas": stats_solucoes['reprovadas'] or 0,
            "media_pontuacao": float(stats_solucoes['media_pontuacao']) if stats_solucoes['media_pontuacao'] else 0,
            "pontos_ganhos": stats_solucoes['total_pontos_ganhos'] or 0
        },
        "certificados_obtidos": certificados['total'],
        "atividades_recentes": atividades_recentes,
        "problemas_recomendados": problemas_recomendados,
        "progresso_semanal": progresso_semanal
    }

# ==================== DASHBOARD DA EMPRESA ====================

@router.get("/empresa/overview", response_model=Dict)
def get_empresa_dashboard(
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """
    Dashboard completo da empresa logada
    """
    
    # Dados básicos da empresa
    cursor.execute("""
        SELECT 
            nome_empresa,
            created_at
        FROM empresas
        WHERE id = %s
    """, (current_empresa['id'],))
    empresa_data = cursor.fetchone()
    
    # Estatísticas de problemas
    cursor.execute("""
        SELECT 
            COUNT(*) as total_problemas,
            SUM(CASE WHEN status = 'ativo' THEN 1 ELSE 0 END) as ativos,
            SUM(CASE WHEN status = 'fechado' THEN 1 ELSE 0 END) as fechados,
            SUM(visualizacoes) as total_visualizacoes
        FROM problemas
        WHERE empresa_id = %s
    """, (current_empresa['id'],))
    stats_problemas = cursor.fetchone()
    
    # Estatísticas de soluções recebidas
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT s.id) as total_solucoes,
            SUM(CASE WHEN s.status = 'em_analise' THEN 1 ELSE 0 END) as pendentes,
            SUM(CASE WHEN s.status = 'aprovada' THEN 1 ELSE 0 END) as aprovadas,
            SUM(CASE WHEN s.status = 'reprovada' THEN 1 ELSE 0 END) as reprovadas,
            COUNT(DISTINCT s.user_id) as usuarios_participantes,
            AVG(s.pontuacao_final) as media_qualidade
        FROM solucoes s
        INNER JOIN problemas p ON s.problema_id = p.id
        WHERE p.empresa_id = %s
    """, (current_empresa['id'],))
    stats_solucoes = cursor.fetchone()
    
    # Certificados emitidos
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM certificados
        WHERE empresa_id = %s
    """, (current_empresa['id'],))
    certificados = cursor.fetchone()
    
    # Top 5 problemas mais populares
    cursor.execute("""
        SELECT 
            p.id,
            p.titulo,
            p.area,
            p.visualizacoes,
            COUNT(DISTINCT s.id) as total_solucoes
        FROM problemas p
        LEFT JOIN solucoes s ON p.id = s.problema_id
        WHERE p.empresa_id = %s
        GROUP BY p.id
        ORDER BY p.visualizacoes DESC, total_solucoes DESC
        LIMIT 5
    """, (current_empresa['id'],))
    top_problemas = cursor.fetchall()
    
    # Top 5 melhores solucionadores (usuários com melhores pontuações)
    cursor.execute("""
        SELECT 
            u.id,
            u.nome_completo,
            u.foto_perfil,
            u.patente,
            COUNT(DISTINCT s.id) as solucoes_submetidas,
            AVG(s.pontuacao_final) as media_pontuacao
        FROM users u
        INNER JOIN solucoes s ON u.id = s.user_id
        INNER JOIN problemas p ON s.problema_id = p.id
        WHERE p.empresa_id = %s AND s.status = 'aprovada'
        GROUP BY u.id
        ORDER BY media_pontuacao DESC, solucoes_submetidas DESC
        LIMIT 5
    """, (current_empresa['id'],))
    top_solucionadores = cursor.fetchall()
    
    # Atividade mensal (soluções por mês nos últimos 6 meses)
    cursor.execute("""
        SELECT 
            DATE_FORMAT(s.data_submissao, '%Y-%m') as mes,
            COUNT(*) as total_solucoes
        FROM solucoes s
        INNER JOIN problemas p ON s.problema_id = p.id
        WHERE p.empresa_id = %s
            AND s.data_submissao >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY mes
        ORDER BY mes
    """, (current_empresa['id'],))
    atividade_mensal = cursor.fetchall()
    
    # Distribuição por área
    cursor.execute("""
        SELECT 
            p.area,
            COUNT(DISTINCT p.id) as total_problemas,
            COUNT(DISTINCT s.id) as total_solucoes
        FROM problemas p
        LEFT JOIN solucoes s ON p.id = s.problema_id
        WHERE p.empresa_id = %s
        GROUP BY p.area
        ORDER BY total_problemas DESC
    """, (current_empresa['id'],))
    distribuicao_areas = cursor.fetchall()
    
    return {
        "empresa": {
            "nome": empresa_data['nome_empresa'],
            "membro_desde": empresa_data['created_at']
        },
        "problemas": {
            "total": stats_problemas['total_problemas'] or 0,
            "ativos": stats_problemas['ativos'] or 0,
            "fechados": stats_problemas['fechados'] or 0,
            "total_visualizacoes": stats_problemas['total_visualizacoes'] or 0
        },
        "solucoes": {
            "total_recebidas": stats_solucoes['total_solucoes'] or 0,
            "pendentes_analise": stats_solucoes['pendentes'] or 0,
            "aprovadas": stats_solucoes['aprovadas'] or 0,
            "reprovadas": stats_solucoes['reprovadas'] or 0,
            "media_qualidade": float(stats_solucoes['media_qualidade']) if stats_solucoes['media_qualidade'] else 0
        },
        "engajamento": {
            "usuarios_participantes": stats_solucoes['usuarios_participantes'] or 0,
            "certificados_emitidos": certificados['total']
        },
        "top_problemas": top_problemas,
        "top_solucionadores": top_solucionadores,
        "atividade_mensal": atividade_mensal,
        "distribuicao_areas": distribuicao_areas
    }

# ==================== ESTATÍSTICAS POR PERÍODO ====================

@router.get("/stats/periodo", response_model=Dict)
def get_stats_periodo(
    dias: int = 30,
    cursor = Depends(get_db)
):
    """
    Estatísticas da plataforma em um período específico
    """
    
    # Novos usuários
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM users
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    """, (dias,))
    novos_usuarios = cursor.fetchone()
    
    # Novos problemas
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM problemas
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    """, (dias,))
    novos_problemas = cursor.fetchone()
    
    # Novas soluções
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM solucoes
        WHERE data_submissao >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    """, (dias,))
    novas_solucoes = cursor.fetchone()
    
    # Taxa de aprovação
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'aprovada' THEN 1 ELSE 0 END) as aprovadas
        FROM solucoes
        WHERE data_submissao >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    """, (dias,))
    taxa_aprovacao = cursor.fetchone()
    
    taxa = 0
    if taxa_aprovacao['total'] and taxa_aprovacao['total'] > 0:
        taxa = (taxa_aprovacao['aprovadas'] / taxa_aprovacao['total']) * 100
    
    return {
        "periodo_dias": dias,
        "novos_usuarios": novos_usuarios['total'],
        "novos_problemas": novos_problemas['total'],
        "novas_solucoes": novas_solucoes['total'],
        "taxa_aprovacao": round(taxa, 2)
    }

# ==================== ÁREAS MAIS POPULARES ====================

@router.get("/stats/areas-populares", response_model=List[Dict])
def get_areas_populares(cursor = Depends(get_db)):
    """
    Áreas mais populares da plataforma
    """
    
    cursor.execute("""
        SELECT 
            p.area,
            COUNT(DISTINCT p.id) as total_problemas,
            COUNT(DISTINCT s.id) as total_solucoes,
            COUNT(DISTINCT s.user_id) as usuarios_participantes
        FROM problemas p
        LEFT JOIN solucoes s ON p.id = s.problema_id
        WHERE p.area IS NOT NULL
        GROUP BY p.area
        ORDER BY total_problemas DESC, total_solucoes DESC
        LIMIT 10
    """)
    
    return cursor.fetchall()