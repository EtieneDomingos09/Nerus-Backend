#Integração com openAI/Claude
import json
from typing import Dict
from app.core.config import settings

async def analisar_solucao(problema: dict, solucao_texto: str) -> Dict:
    """
    Analisa a solução usando AI (OpenAI ou Claude)
    
    Args:
        problema: Dicionário com dados do problema
        solucao_texto: Texto da solução submetida
    
    Returns:
        Dict com pontuação, feedback e critérios atendidos
    """
    
    if settings.AI_PROVIDER == "openai":
        return await analisar_com_openai(problema, solucao_texto)
    elif settings.AI_PROVIDER == "anthropic":
        return await analisar_com_claude(problema, solucao_texto)
    else:
        raise ValueError(f"AI Provider inválido: {settings.AI_PROVIDER}")

# ==================== OPENAI ====================

async def analisar_com_openai(problema: dict, solucao_texto: str) -> Dict:
    """Análise usando OpenAI GPT-4"""
    
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Montar prompt
    prompt = f"""
Você é um avaliador especializado em analisar soluções de problemas práticos de empresas.

**PROBLEMA:**
Título: {problema['titulo']}
Descrição: {problema['descricao']}
Área: {problema['area']}
Nível: {problema['nivel_dificuldade']}
Objetivos: {problema.get('objetivos', 'Não especificado')}
Requisitos: {problema.get('requisitos', 'Não especificado')}

**SOLUÇÃO SUBMETIDA:**
{solucao_texto}

**TAREFA:**
Avalie esta solução em uma escala de 0 a 100, considerando:
1. Compreensão do problema (0-25 pontos)
2. Qualidade da solução proposta (0-25 pontos)
3. Criatividade e inovação (0-20 pontos)
4. Viabilidade de implementação (0-15 pontos)
5. Clareza na explicação (0-15 pontos)

**FORMATO DE RESPOSTA (JSON):**
{{
    "pontuacao": 85,
    "feedback": "Análise detalhada da solução...",
    "pontos_fortes": ["ponto1", "ponto2"],
    "pontos_fracos": ["ponto1", "ponto2"],
    "sugestoes_melhoria": ["sugestao1", "sugestao2"],
    "criterios": {{
        "compreensao_problema": 22,
        "qualidade_solucao": 20,
        "criatividade": 18,
        "viabilidade": 13,
        "clareza": 12
    }}
}}

Retorne APENAS o JSON, sem texto adicional.
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Você é um avaliador especializado e justo."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        resultado = json.loads(response.choices[0].message.content)
        
        return {
            "pontuacao": resultado.get("pontuacao", 0),
            "feedback": resultado.get("feedback", ""),
            "detalhes": resultado
        }
        
    except Exception as e:
        print(f"Erro ao analisar com OpenAI: {e}")