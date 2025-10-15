# #Integração com openAI/Claude
# import json
# from typing import Dict
# from app.core.config import settings

# async def analisar_solucao(problema: dict, solucao_texto: str) -> Dict:
#     """
#     Analisa a solução usando AI (OpenAI ou Claude)
    
#     Args:
#         problema: Dicionário com dados do problema
#         solucao_texto: Texto da solução submetida
    
#     Returns:
#         Dict com pontuação, feedback e critérios atendidos
#     """
    
#     if settings.AI_PROVIDER == "openai":
#         return await analisar_com_openai(problema, solucao_texto)
#     elif settings.AI_PROVIDER == "anthropic":
#         return await analisar_com_claude(problema, solucao_texto)
#     else:
#         raise ValueError(f"AI Provider inválido: {settings.AI_PROVIDER}")

# # ==================== OPENAI ====================

# async def analisar_com_openai(problema: dict, solucao_texto: str) -> Dict:
#     """Análise usando OpenAI GPT-4"""
    
#     from openai import AsyncOpenAI
    
#     client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
#     # Montar prompt
#     prompt = f"""
# Você é um avaliador especializado em analisar soluções de problemas práticos de empresas.

# **PROBLEMA:**
# Título: {problema['titulo']}
# Descrição: {problema['descricao']}
# Área: {problema['area']}
# Nível: {problema['nivel_dificuldade']}
# Objetivos: {problema.get('objetivos', 'Não especificado')}
# Requisitos: {problema.get('requisitos', 'Não especificado')}

# **SOLUÇÃO SUBMETIDA:**
# {solucao_texto}

# **TAREFA:**
# Avalie esta solução em uma escala de 0 a 100, considerando:
# 1. Compreensão do problema (0-25 pontos)
# 2. Qualidade da solução proposta (0-25 pontos)
# 3. Criatividade e inovação (0-20 pontos)
# 4. Viabilidade de implementação (0-15 pontos)
# 5. Clareza na explicação (0-15 pontos)

# **FORMATO DE RESPOSTA (JSON):**
# {{
#     "pontuacao": 85,
#     "feedback": "Análise detalhada da solução...",
#     "pontos_fortes": ["ponto1", "ponto2"],
#     "pontos_fracos": ["ponto1", "ponto2"],
#     "sugestoes_melhoria": ["sugestao1", "sugestao2"],
#     "criterios": {{
#         "compreensao_problema": 22,
#         "qualidade_solucao": 20,
#         "criatividade": 18,
#         "viabilidade": 13,
#         "clareza": 12
#     }}
# }}

# Retorne APENAS o JSON, sem texto adicional.
# """
    
#     try:
#         response = await client.chat.completions.create(
#             model="gpt-4-turbo-preview",
#             messages=[
#                 {"role": "system", "content": "Você é um avaliador especializado e justo."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.3,
#             response_format={"type": "json_object"}
#         )
        
#         resultado = json.loads(response.choices[0].message.content)
        
#         return {
#             "pontuacao": resultado.get("pontuacao", 0),
#             "feedback": resultado.get("feedback", ""),
#             "detalhes": resultado
#         }
        
#    except Exception as e:
#         print(f"Erro ao analisar com OpenAI: {e}")
#         raise

# # ==================== ANTHROPIC CLAUDE ====================

# async def analisar_com_claude(problema: dict, solucao_texto: str) -> Dict:
#     """Análise usando Anthropic Claude"""
    
#     from anthropic import AsyncAnthropic
    
#     client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
#     # Montar prompt
#     prompt = f"""
# Você é um avaliador especializado em analisar soluções de problemas práticos de empresas.

# **PROBLEMA:**
# Título: {problema['titulo']}
# Descrição: {problema['descricao']}
# Área: {problema['area']}
# Nível: {problema['nivel_dificuldade']}
# Objetivos: {problema.get('objetivos', 'Não especificado')}
# Requisitos: {problema.get('requisitos', 'Não especificado')}

# **SOLUÇÃO SUBMETIDA:**
# {solucao_texto}

# **TAREFA:**
# Avalie esta solução em uma escala de 0 a 100, considerando:
# 1. Compreensão do problema (0-25 pontos)
# 2. Qualidade da solução proposta (0-25 pontos)
# 3. Criatividade e inovação (0-20 pontos)
# 4. Viabilidade de implementação (0-15 pontos)
# 5. Clareza na explicação (0-15 pontos)

# Retorne um JSON com a seguinte estrutura:
# {{
#     "pontuacao": 85,
#     "feedback": "Análise detalhada da solução...",
#     "pontos_fortes": ["ponto1", "ponto2"],
#     "pontos_fracos": ["ponto1", "ponto2"],
#     "sugestoes_melhoria": ["sugestao1", "sugestao2"],
#     "criterios": {{
#         "compreensao_problema": 22,
#         "qualidade_solucao": 20,
#         "criatividade": 18,
#         "viabilidade": 13,
#         "clareza": 12
#     }}
# }}
# """
    
#     try:
#         response = await client.messages.create(
#             model="claude-3-5-sonnet-20241022",
#             max_tokens=2000,
#             temperature=0.3,
#             messages=[
#                 {"role": "user", "content": prompt}
#             ]
#         )
        
#         # Extrair JSON do texto da resposta
#         content = response.content[0].text
        
#         # Tentar encontrar JSON no conteúdo
#         import re
#         json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
#         if json_match:
#             resultado = json.loads(json_match.group())
#         else:
#             # Fallback se não encontrar JSON válido
#             resultado = {
#                 "pontuacao": 70,
#                 "feedback": content,
#                 "pontos_fortes": ["Solução apresentada"],
#                 "pontos_fracos": ["Necessita mais detalhes"],
#                 "sugestoes_melhoria": ["Expandir explicação"],
#                 "criterios": {
#                     "compreensao_problema": 18,
#                     "qualidade_solucao": 17,
#                     "criatividade": 14,
#                     "viabilidade": 11,
#                     "clareza": 10
#                 }
#             }
        
#         return {
#             "pontuacao": resultado.get("pontuacao", 0),
#             "feedback": resultado.get("feedback", ""),
#             "detalhes": resultado
#         }
        
#     except Exception as e:
#         print(f"Erro ao analisar com Claude: {e}")
#         raise

# # ==================== FUNÇÃO AUXILIAR ====================

# def gerar_feedback_resumido(analise: dict) -> str:
#     """
#     Gera um feedback resumido e amigável baseado na análise
#     """
#     pontuacao = analise.get('pontuacao', 0)
    
#     if pontuacao >= 90:
#         nivel = "Excepcional! 🌟"
#     elif pontuacao >= 80:
#         nivel = "Excelente! 🎯"
#     elif pontuacao >= 70:
#         nivel = "Muito Bom! 👍"
#     elif pontuacao >= 60:
#         nivel = "Bom! ✓"
#     else:
#         nivel = "Precisa Melhorar 📚"
    
#     feedback = f"**Avaliação: {nivel}**\n\n"
#     feedback += f"**Pontuação: {pontuacao}/100**\n\n"
    
#     detalhes = analise.get('detalhes', {})
    
#     if detalhes.get('pontos_fortes'):
#         feedback += "**Pontos Fortes:**\n"
#         for ponto in detalhes['pontos_fortes'][:3]:
#             feedback += f"✓ {ponto}\n"
#         feedback += "\n"
    
#     if detalhes.get('pontos_fracos'):
#         feedback += "**Pontos a Melhorar:**\n"
#         for ponto in detalhes['pontos_fracos'][:3]:
#             feedback += f"• {ponto}\n"
#         feedback += "\n"
    
#     if detalhes.get('sugestoes_melhoria'):
#         feedback += "**Sugestões:**\n"
#         for sugestao in detalhes['sugestoes_melhoria'][:3]:
#             feedback += f"→ {sugestao}\n"
    
#     return feedback