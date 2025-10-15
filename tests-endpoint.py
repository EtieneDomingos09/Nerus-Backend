"""
Script de Testes Automatizados - NERUS Platform
Execute este script para testar todos os endpoints da API
"""

import requests
import json
from datetime import datetime, timedelta

# Configurações
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, status, message=""):
    """Imprime resultado do teste"""
    if status:
        print(f"{Colors.GREEN}✅ {name}{Colors.END}")
        if message:
            print(f"   {Colors.BLUE}{message}{Colors.END}")
    else:
        print(f"{Colors.RED}❌ {name}{Colors.END}")
        if message:
            print(f"   {Colors.YELLOW}{message}{Colors.END}")

def test_health():
    """Teste 1: Health Check"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 1: HEALTH CHECK")
    print(f"{'='*60}{Colors.END}\n")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        success = response.status_code == 200
        data = response.json() if success else {}
        
        print_test(
            "GET /", 
            success,
            f"Resposta: {data.get('message', 'N/A')}"
        )
        
        response = requests.get(f"{BASE_URL}/health")
        success = response.status_code == 200
        data = response.json() if success else {}
        
        print_test(
            "GET /health", 
            success,
            f"Status: {data.get('status', 'N/A')}"
        )
        
        return True
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False

def test_user_registration():
    """Teste 2: Registro de Usuário"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 2: REGISTRO DE USUÁRIO")
    print(f"{'='*60}{Colors.END}\n")
    
    # Usar timestamp para email único
    timestamp = datetime.now().timestamp()
    email = f"teste_user_{timestamp}@email.com"
    senha = "teste123"
    
    user_data = {
        "nome_completo": "Teste Automático User",
        "email": email,
        "senha": senha,
        "telefone": "+244923456789",
        "area_interesse": "Tecnologia",
        "nivel_educacao": "superior_em_curso"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/auth/register/user",
            json=user_data
        )
        
        success = response.status_code == 201
        data = response.json() if success else response.text
        
        print_test(
            "POST /auth/register/user",
            success,
            f"User ID: {data.get('user_id')} | Token: {data.get('verification_token', 'N/A')[:20]}..." if success else data
        )
        
        # Retornar credenciais para usar no login
        if success:
            return {
                "email": email,
                "senha": senha,
                "data": data
            }
        return None
    except Exception as e:
        print_test("Registro de Usuário", False, str(e))
        return None

def test_empresa_registration():
    """Teste 3: Registro de Empresa"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 3: REGISTRO DE EMPRESA")
    print(f"{'='*60}{Colors.END}\n")
    
    # Usar timestamp para email único
    timestamp = datetime.now().timestamp()
    email = f"teste_empresa_{timestamp}@empresa.ao"
    senha = "empresa123"
    
    empresa_data = {
        "nome_empresa": "Teste Automático Empresa Lda",
        "email_corporativo": email,
        "senha": senha,
        "nif": f"{int(timestamp)}",
        "telefone": "+244912345678",
        "setor_atuacao": "Tecnologia",
        "tamanho_empresa": "media"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/auth/register/empresa",
            json=empresa_data
        )
        
        success = response.status_code == 201
        data = response.json() if success else response.text
        
        print_test(
            "POST /auth/register/empresa",
            success,
            f"Empresa ID: {data.get('empresa_id')} | Token: {data.get('verification_token', 'N/A')[:20]}..." if success else data
        )
        
        # Retornar credenciais para usar no login
        if success:
            return {
                "email": email,
                "senha": senha,
                "data": data
            }
        return None
    except Exception as e:
        print_test("Registro de Empresa", False, str(e))
        return None

def test_user_login(email, senha):
    """Teste 4: Login de Usuário"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 4: LOGIN DE USUÁRIO")
    print(f"{'='*60}{Colors.END}\n")
    
    login_data = {
        "email": email,
        "senha": senha,
        "tipo_usuario": "user"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json=login_data
        )
        
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "POST /auth/login (user)",
            success,
            f"Token: {data.get('access_token', 'N/A')[:30]}... | Nome: {data.get('nome', 'N/A')}" if success else data
        )
        
        return data.get('access_token') if success else None
    except Exception as e:
        print_test("Login de Usuário", False, str(e))
        return None

def test_empresa_login(email, senha):
    """Teste 5: Login de Empresa"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 5: LOGIN DE EMPRESA")
    print(f"{'='*60}{Colors.END}\n")
    
    login_data = {
        "email": email,
        "senha": senha,
        "tipo_usuario": "empresa"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json=login_data
        )
        
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "POST /auth/login (empresa)",
            success,
            f"Token: {data.get('access_token', 'N/A')[:30]}... | Nome: {data.get('nome', 'N/A')}" if success else data
        )
        
        return data.get('access_token') if success else None
    except Exception as e:
        print_test("Login de Empresa", False, str(e))
        return None

def test_protected_endpoints(token):
    """Teste 6: Endpoints Protegidos"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 6: ENDPOINTS PROTEGIDOS (COM TOKEN)")
    print(f"{'='*60}{Colors.END}\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 6.1: /auth/me
    try:
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /auth/me",
            success,
            f"User ID: {data.get('user_id')} | Email: {data.get('email')}" if success else data
        )
    except Exception as e:
        print_test("GET /auth/me", False, str(e))
    
    # 6.2: /users/me
    try:
        response = requests.get(f"{API_URL}/users/me", headers=headers)
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /users/me",
            success,
            f"Nome: {data.get('nome_completo')} | Pontos: {data.get('pontos_totais')}" if success else data
        )
    except Exception as e:
        print_test("GET /users/me", False, str(e))
    
    # 6.3: /users/me/stats
    try:
        response = requests.get(f"{API_URL}/users/me/stats", headers=headers)
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /users/me/stats",
            success,
            f"Soluções: {data.get('total_solucoes')} | Ranking: #{data.get('ranking_posicao')}" if success else data
        )
    except Exception as e:
        print_test("GET /users/me/stats", False, str(e))

def test_problema_creation(token):
    """Teste 7: Criação de Problema"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 7: CRIAÇÃO DE PROBLEMA (EMPRESA)")
    print(f"{'='*60}{Colors.END}\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    hoje = datetime.now().date()
    fim = (datetime.now() + timedelta(days=30)).date()
    
    problema_data = {
        "titulo": "Sistema de Gestão - Teste Automático",
        "descricao": "Este é um problema criado automaticamente durante os testes. Precisamos desenvolver um sistema completo de gestão com funcionalidades modernas.",
        "area": "Tecnologia",
        "nivel_dificuldade": "intermediario",
        "tipo": "free",
        "prazo_dias": 30,
        "pontos_recompensa": 500,
        "oferece_certificado": True,
        "data_inicio": str(hoje),
        "data_fim": str(fim)
    }
    
    try:
        response = requests.post(
            f"{API_URL}/problemas/",
            json=problema_data,
            headers=headers
        )
        
        success = response.status_code == 201
        data = response.json() if success else response.text
        
        print_test(
            "POST /problemas/",
            success,
            f"Problema ID: {data.get('problema_id')}" if success else data
        )
        
        return data.get('problema_id') if success else None
    except Exception as e:
        print_test("Criação de Problema", False, str(e))
        return None

def test_list_problemas():
    """Teste 8: Listar Problemas"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 8: LISTAR PROBLEMAS")
    print(f"{'='*60}{Colors.END}\n")
    
    try:
        response = requests.get(f"{API_URL}/problemas/")
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /problemas/",
            success,
            f"Total de problemas: {len(data) if isinstance(data, list) else 0}" if success else data
        )
        
        return data if success else []
    except Exception as e:
        print_test("Listar Problemas", False, str(e))
        return []

def test_ranking():
    """Teste 9: Rankings"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 9: RANKINGS")
    print(f"{'='*60}{Colors.END}\n")
    
    # 9.1: Ranking Global
    try:
        response = requests.get(f"{API_URL}/ranking/global")
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /ranking/global",
            success,
            f"Total no ranking: {len(data) if isinstance(data, list) else 0}" if success else data
        )
    except Exception as e:
        print_test("GET /ranking/global", False, str(e))
    
    # 9.2: Ranking Mensal
    try:
        response = requests.get(f"{API_URL}/ranking/mensal")
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /ranking/mensal",
            success,
            f"Total no ranking mensal: {len(data) if isinstance(data, list) else 0}" if success else data
        )
    except Exception as e:
        print_test("GET /ranking/mensal", False, str(e))
    
    # 9.3: Estatísticas
    try:
        response = requests.get(f"{API_URL}/ranking/estatisticas")
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /ranking/estatisticas",
            success,
            f"Usuários ativos: {data.get('total_usuarios_ativos')}" if success else data
        )
    except Exception as e:
        print_test("GET /ranking/estatisticas", False, str(e))

def test_habilidades(token):
    """Teste 10: Sistema de Habilidades"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 10: SISTEMA DE HABILIDADES")
    print(f"{'='*60}{Colors.END}\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 10.1: Listar habilidades disponíveis
    try:
        response = requests.get(f"{API_URL}/users/habilidades-disponiveis")
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /users/habilidades-disponiveis",
            success,
            f"Total de habilidades: {len(data) if isinstance(data, list) else 0}" if success else data
        )
        
        habilidade_id = data[0]['id'] if isinstance(data, list) and len(data) > 0 else 1
        
    except Exception as e:
        print_test("GET /users/habilidades-disponiveis", False, str(e))
        habilidade_id = 1
    
    # 10.2: Adicionar habilidade
    try:
        habilidade_data = {
            "habilidade_id": habilidade_id,
            "nivel_proficiencia": "intermediario"
        }
        
        response = requests.post(
            f"{API_URL}/users/me/habilidades",
            json=habilidade_data,
            headers=headers
        )
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "POST /users/me/habilidades",
            success,
            f"Habilidade adicionada" if success else data
        )
    except Exception as e:
        print_test("POST /users/me/habilidades", False, str(e))
    
    # 10.3: Listar minhas habilidades
    try:
        response = requests.get(f"{API_URL}/users/me/habilidades", headers=headers)
        success = response.status_code == 200
        data = response.json() if success else response.text
        
        print_test(
            "GET /users/me/habilidades",
            success,
            f"Total de habilidades do usuário: {len(data) if isinstance(data, list) else 0}" if success else data
        )
    except Exception as e:
        print_test("GET /users/me/habilidades", False, str(e))

def test_submeter_solucao(token, problema_id):
    """Teste 11: Submeter Solução"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TESTE 11: SUBMETER SOLUÇÃO")
    print(f"{'='*60}{Colors.END}\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    solucao_data = {
        "problema_id": problema_id,
        "descricao_solucao": """
        Esta é uma solução completa para o problema proposto. 
        
        ## Análise do Problema
        Após análise detalhada, identifiquei os principais requisitos e desafios.
        
        ## Solução Proposta
        Desenvolvi uma abordagem modular que atende todos os requisitos:
        
        1. **Arquitetura**: Utilizei uma arquitetura MVC moderna
        2. **Tecnologias**: React + Node.js + MySQL
        3. **Funcionalidades**: Sistema completo de gestão com dashboard
        """ 
    }
    
    try:
        response = requests.post(
            f"{API_URL}/solucoes/",
            json=solucao_data,
            headers=headers
        )
        
        success = response.status_code == 201
        data = response.json() if success else response.text
        
        print_test(
            "POST /solucoes/",
            success,
            f"Solução ID: {data.get('solucao_id')}" if success else data
        )
        
        return success
    except Exception as e:
        print_test("Submeter Solução", False, str(e))
        return False

def main():
    """Executar todos os testes"""
    print(f"\n{Colors.GREEN}{'='*60}")
    print(f"🧪 NERUS PLATFORM - TESTES AUTOMATIZADOS")
    print(f"{'='*60}{Colors.END}\n")
    
    print(f"{Colors.YELLOW}Iniciando testes...{Colors.END}\n")
    
    # Teste 1: Health Check
    if not test_health():
        print(f"\n{Colors.RED}⚠️  API não está respondendo! Verifique se está rodando.{Colors.END}")
        return
    
    # Teste 2: Registro de Usuário
    user_credentials = test_user_registration()
    
    # Teste 3: Registro de Empresa  
    empresa_credentials = test_empresa_registration()
    
    # Teste 4: Login de Usuário - AGORA USA AS CREDENCIAIS DO REGISTRO
    user_token = None
    if user_credentials:
        user_token = test_user_login(
            user_credentials["email"], 
            user_credentials["senha"]
        )
    
    # Teste 5: Login de Empresa - AGORA USA AS CREDENCIAIS DO REGISTRO
    empresa_token = None
    if empresa_credentials:
        empresa_token = test_empresa_login(
            empresa_credentials["email"], 
            empresa_credentials["senha"]
        )
    
    # Teste 6: Endpoints Protegidos
    if user_token:
        test_protected_endpoints(user_token)
    
    # Teste 7: Criação de Problema
    problema_id = None
    if empresa_token:
        problema_id = test_problema_creation(empresa_token)
    
    # Teste 8: Listar Problemas
    test_list_problemas()
    
    # Teste 9: Rankings
    test_ranking()
    
    # Teste 10: Habilidades
    if user_token:
        test_habilidades(user_token)
    
    # Teste 11: Submeter Solução
    if user_token and problema_id:
        test_submeter_solucao(user_token, problema_id)
    
    # Relatório Final
    print(f"\n{Colors.GREEN}{'='*60}")
    print(f"✅ TESTES CONCLUÍDOS!")
    print(f"{'='*60}{Colors.END}\n")
    
    print(f"{Colors.BLUE}📊 RESUMO:{Colors.END}")
    print(f"   - Script de testes executado com sucesso")
    print(f"   - Verifique os resultados acima")
    
    if user_token:
        print(f"\n{Colors.GREEN}🔑 Token de Usuário:{Colors.END}")
        print(f"   {user_token[:50]}...")
    
    if empresa_token:
        print(f"\n{Colors.GREEN}🔑 Token de Empresa:{Colors.END}")
        print(f"   {empresa_token[:50]}...")

# ✅ Executa o script
if __name__ == "__main__":
    main()