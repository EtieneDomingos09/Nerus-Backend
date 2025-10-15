#GET/CREATE certificados
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_empresa

router = APIRouter()

# ==================== SCHEMAS ====================

class CertificadoResponse(BaseModel):
    """Schema de resposta do certificado"""
    id: int
    codigo_verificacao: str
    titulo: str
    descricao: Optional[str] = None
    url_certificado: Optional[str] = None
    data_emissao: str
    user_nome: Optional[str] = None
    empresa_nome: Optional[str] = None
    problema_titulo: Optional[str] = None

class CertificadoCreate(BaseModel):
    """Schema para criar certificado"""
    solucao_id: int
    titulo: str
    descricao: Optional[str] = None

class CertificadoVerify(BaseModel):
    """Schema para verificar certificado"""
    codigo_verificacao: str

# ==================== GERAR CERTIFICADO (EMPRESA) ====================

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def gerar_certificado(
    certificado_data: CertificadoCreate,
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """
    Gerar certificado para solução aprovada
    Apenas a empresa dona do problema pode emitir
    """
    
    # Verificar se solução existe e pertence à empresa
    cursor.execute("""
        SELECT 
            s.id,
            s.user_id,
            s.problema_id,
            s.status,
            p.empresa_id,
            p.titulo as problema_titulo,
            p.oferece_certificado
        FROM solucoes s
        INNER JOIN problemas p ON s.problema_id = p.id
        WHERE s.id = %s
    """, (certificado_data.solucao_id,))
    
    solucao = cursor.fetchone()
    
    if not solucao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solução não encontrada"
        )
    
    if solucao['empresa_id'] != current_empresa['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para emitir certificado para esta solução"
        )
    
    if solucao['status'] != 'aprovada':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas soluções aprovadas podem receber certificados"
        )
    
    if not solucao['oferece_certificado']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este problema não oferece certificado"
        )
    
    # Verificar se já existe certificado
    cursor.execute("""
        SELECT id FROM certificados 
        WHERE solucao_id = %s
    """, (certificado_data.solucao_id,))
    
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificado já emitido para esta solução"
        )
    
    # Gerar código de verificação único
    import secrets
    codigo_verificacao = f"CERT-{secrets.token_urlsafe(16).upper()}"
    
    # Inserir certificado
    query = """
    INSERT INTO certificados (
        solucao_id, user_id, problema_id, empresa_id,
        codigo_verificacao, titulo, descricao
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(query, (
        certificado_data.solucao_id,
        solucao['user_id'],
        solucao['problema_id'],
        current_empresa['id'],
        codigo_verificacao,
        certificado_data.titulo,
        certificado_data.descricao
    ))
    
    certificado_id = cursor.lastrowid
    
    # Atualizar solução
    cursor.execute("""
        UPDATE solucoes 
        SET certificado_emitido = TRUE
        WHERE id = %s
    """, (certificado_data.solucao_id,))
    
    # TODO: Chamar serviço de geração de PDF do certificado
    # url_certificado = certificado_service.gerar_pdf(certificado_id)
    
    # Criar notificação para o usuário
    cursor.execute("""
        INSERT INTO notificacoes (
            user_id, tipo_destinatario, tipo, titulo, mensagem, link
        ) VALUES (%s, 'user', 'certificado', %s, %s, %s)
    """, (
        solucao['user_id'],
        'Certificado Emitido! 🎓',
        f'Parabéns! Você recebeu um certificado: {certificado_data.titulo}',
        f'/certificados/{certificado_id}'
    ))
    
    return {
        "message": "Certificado emitido com sucesso!",
        "certificado_id": certificado_id,
        "codigo_verificacao": codigo_verificacao
    }

# ==================== MEUS CERTIFICADOS (USUÁRIO) ====================

@router.get("/meus-certificados", response_model=List[CertificadoResponse])
def meus_certificados(
    current_user = Depends(get_current_user),
    cursor = Depends(get_db)
):
    """Listar todos os certificados do usuário logado"""
    
    query = """
    SELECT 
        c.*,
        u.nome_completo as user_nome,
        e.nome_empresa as empresa_nome,
        p.titulo as problema_titulo
    FROM certificados c
    INNER JOIN users u ON c.user_id = u.id
    INNER JOIN empresas e ON c.empresa_id = e.id
    INNER JOIN problemas p ON c.problema_id = p.id
    WHERE c.user_id = %s
    ORDER BY c.data_emissao DESC
    """
    
    cursor.execute(query, (current_user['id'],))
    return cursor.fetchall()

# ==================== DETALHES DO CERTIFICADO ====================

@router.get("/{certificado_id}", response_model=CertificadoResponse)
def get_certificado(
    certificado_id: int,
    cursor = Depends(get_db)
):
    """Obter detalhes de um certificado específico"""
    
    query = """
    SELECT 
        c.*,
        u.nome_completo as user_nome,
        e.nome_empresa as empresa_nome,
        p.titulo as problema_titulo
    FROM certificados c
    INNER JOIN users u ON c.user_id = u.id
    INNER JOIN empresas e ON c.empresa_id = e.id
    INNER JOIN problemas p ON c.problema_id = p.id
    WHERE c.id = %s
    """
    
    cursor.execute(query, (certificado_id,))
    certificado = cursor.fetchone()
    
    if not certificado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificado não encontrado"
        )
    
    return certificado

# ==================== VERIFICAR AUTENTICIDADE ====================

@router.post("/verificar", response_model=dict)
def verificar_certificado(
    verificacao: CertificadoVerify,
    cursor = Depends(get_db)
):
    """
    Verificar autenticidade de um certificado pelo código
    Endpoint público para validação externa
    """
    
    query = """
    SELECT 
        c.*,
        u.nome_completo as user_nome,
        u.email as user_email,
        e.nome_empresa as empresa_nome,
        p.titulo as problema_titulo,
        p.area,
        s.pontuacao_final
    FROM certificados c
    INNER JOIN users u ON c.user_id = u.id
    INNER JOIN empresas e ON c.empresa_id = e.id
    INNER JOIN problemas p ON c.problema_id = p.id
    INNER JOIN solucoes s ON c.solucao_id = s.id
    WHERE c.codigo_verificacao = %s
    """
    
    cursor.execute(query, (verificacao.codigo_verificacao,))
    certificado = cursor.fetchone()
    
    if not certificado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificado não encontrado. Código inválido."
        )
    
    return {
        "valido": True,
        "certificado": {
            "codigo": certificado['codigo_verificacao'],
            "titulo": certificado['titulo'],
            "descricao": certificado['descricao'],
            "data_emissao": certificado['data_emissao'],
            "beneficiario": certificado['user_nome'],
            "email_beneficiario": certificado['user_email'],
            "empresa_emissora": certificado['empresa_nome'],
            "problema": certificado['problema_titulo'],
            "area": certificado['area'],
            "pontuacao_obtida": certificado['pontuacao_final']
        }
    }

# ==================== CERTIFICADOS EMITIDOS (EMPRESA) ====================

@router.get("/empresa/emitidos", response_model=List[dict])
def certificados_emitidos(
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """Listar certificados emitidos pela empresa logada"""
    
    query = """
    SELECT 
        c.*,
        u.nome_completo as user_nome,
        u.email as user_email,
        p.titulo as problema_titulo
    FROM certificados c
    INNER JOIN users u ON c.user_id = u.id
    INNER JOIN problemas p ON c.problema_id = p.id
    WHERE c.empresa_id = %s
    ORDER BY c.data_emissao DESC
    """
    
    cursor.execute(query, (current_empresa['id'],))
    return cursor.fetchall()

# ==================== ESTATÍSTICAS DE CERTIFICADOS ====================

@router.get("/stats/geral", response_model=dict)
def stats_certificados(cursor = Depends(get_db)):
    """Estatísticas gerais de certificados da plataforma"""
    
    # Total de certificados
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM certificados
    """)
    total = cursor.fetchone()
    
    # Por área
    cursor.execute("""
        SELECT 
            p.area,
            COUNT(c.id) as total_certificados
        FROM certificados c
        INNER JOIN problemas p ON c.problema_id = p.id
        GROUP BY p.area
        ORDER BY total_certificados DESC
        LIMIT 5
    """)
    por_area = cursor.fetchall()
    
    # Empresas que mais emitiram
    cursor.execute("""
        SELECT 
            e.nome_empresa,
            e.logo_url,
            COUNT(c.id) as total_emitidos
        FROM certificados c
        INNER JOIN empresas e ON c.empresa_id = e.id
        GROUP BY e.id
        ORDER BY total_emitidos DESC
        LIMIT 5
    """)
    top_empresas = cursor.fetchall()
    
    # Certificados emitidos por mês (últimos 6 meses)
    cursor.execute("""
        SELECT 
            DATE_FORMAT(data_emissao, '%Y-%m') as mes,
            COUNT(*) as total
        FROM certificados
        WHERE data_emissao >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY mes
        ORDER BY mes
    """)
    por_mes = cursor.fetchall()
    
    return {
        "total_certificados": total['total'],
        "por_area": por_area,
        "top_empresas_emissoras": top_empresas,
        "emissoes_mensais": por_mes
    }

# ==================== REVOGAR CERTIFICADO (EMPRESA) ====================

@router.delete("/{certificado_id}", response_model=dict)
def revogar_certificado(
    certificado_id: int,
    motivo: str,
    current_empresa = Depends(get_current_empresa),
    cursor = Depends(get_db)
):
    """
    Revogar certificado (apenas empresa emissora)
    IMPORTANTE: Use com cuidado!
    """
    
    # Verificar se certificado pertence à empresa
    cursor.execute("""
        SELECT c.*, u.nome_completo
        FROM certificados c
        INNER JOIN users u ON c.user_id = u.id
        WHERE c.id = %s
    """, (certificado_id,))
    
    certificado = cursor.fetchone()
    
    if not certificado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificado não encontrado"
        )
    
    if certificado['empresa_id'] != current_empresa['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para revogar este certificado"
        )
    
    # Deletar certificado
    cursor.execute("""
        DELETE FROM certificados
        WHERE id = %s
    """, (certificado_id,))
    
    # Atualizar solução
    cursor.execute("""
        UPDATE solucoes 
        SET certificado_emitido = FALSE
        WHERE id = %s
    """, (certificado['solucao_id'],))
    
    # Notificar usuário
    cursor.execute("""
        INSERT INTO notificacoes (
            user_id, tipo_destinatario, tipo, titulo, mensagem
        ) VALUES (%s, 'user', 'certificado_revogado', %s, %s)
    """, (
        certificado['user_id'],
        'Certificado Revogado',
        f'Seu certificado "{certificado["titulo"]}" foi revogado. Motivo: {motivo}'
    ))
    
    # Log da ação
    import json
    cursor.execute("""
        INSERT INTO logs_atividade (
            empresa_id, tipo_usuario, acao, detalhes
        ) VALUES (%s, 'empresa', 'revogar_certificado', %s)
    """, (
        current_empresa['id'],
        json.dumps({
            "certificado_id": certificado_id,
            "user_afetado": certificado['nome_completo'],
            "motivo": motivo
        })
    ))
    
    return {
        "message": "Certificado revogado com sucesso",
        "motivo": motivo
    }