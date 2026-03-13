import json
import os
from flask import jsonify, request, make_response

# Nome do arquivo onde o estado do AccountService será salvo
ACCOUNT_SERVICE_FILE = "account_service.json"



# Estado inicial com apenas os campos obrigatórios
default_account_service_state = {
    "ServiceEnabled": True,
    "Accounts": "/redfish/v1/AccountService/Accounts",
    "MinPasswordLength": 8,
    "MaxPasswordLength": 32,
    "AccountLockoutThreshold": 5,
    "AccountLockoutDuration": 600,  # 10 minutos
    "AccountLockoutCounterResetAfter": 300,  # 5 minutos
    "AccountLockoutCounterResetEnabled": True,
}

# Função para carregar o estado do AccountService a partir de um arquivo JSON
def load_account_service():
    """
    Carrega o estado do AccountService a partir de um arquivo JSON.

    Returns:
        dict: Estado atual do AccountService. Se o arquivo não existir, retorna o estado padrão.
    """
    if os.path.exists(ACCOUNT_SERVICE_FILE):            # Verifica se o arquivo existe
        with open(ACCOUNT_SERVICE_FILE, "r") as file:
            return json.load(file)                      # Carrega o estado do arquivo JSON
    return default_account_service_state.copy()         # Retorna uma cópia do estado padrão

# Função para salvar o estado do AccountService em um arquivo JSON
def save_account_service(state):
    """
    Salva o estado do AccountService em um arquivo JSON.

    Args:
        state (dict): Estado do AccountService a ser salvo.
    """
    with open(ACCOUNT_SERVICE_FILE, "w") as file:
        json.dump(state, file, indent=4)

# Inicializa o estado do AccountService ao carregar o módulo
account_service_state = load_account_service()

# Função para obter os dados do AccountService
def get_account_service():
    """
    Retorna os dados do AccountService no formato Redfish.

    Returns:
        flask.Response: Resposta JSON com os dados do AccountService.
    """
    response = {
        "@odata.id": "/redfish/v1/AccountService",
        "@odata.type": "#AccountService.v1_17_0.AccountService",
        "Id": "AccountService",
        "Name": "Account Service",
        "Description": "Local Manager Account Service",
        "ServiceEnabled": account_service_state["ServiceEnabled"],
        "Accounts": {
            "@odata.id": account_service_state["Accounts"]
        },
        "Roles": {
            "@odata.id": "/redfish/v1/AccountService/Roles"
        },
        "MinPasswordLength": account_service_state["MinPasswordLength"],
        "MaxPasswordLength": account_service_state["MaxPasswordLength"]
    }
    return jsonify(response)

# Função para atualizar o estado do AccountService
def update_account_service(data):
    """
    Atualiza apenas o campo obrigatório 'ServiceEnabled' do AccountService.

    Args:
        data (dict): Dicionário contendo o campo 'ServiceEnabled' a ser atualizado.

    Returns:
        flask.Response: Mensagem de sucesso ou erro.
    """
    if "ServiceEnabled" in data:        # Verifica se o campo 'ServiceEnabled' está presente nos dados
        account_service_state["ServiceEnabled"] = bool(data["ServiceEnabled"])  # Atualiza o estado
        save_account_service(account_service_state)     # Salva o estado atualizado no arquivo
        return make_response({"message": "AccountService updated successfully."}, 200)      # Retorna sucesso
        
        # Retorna erro se os dados fornecidos não forem válidos
    return make_response({"error": "Invalid properties in request."}, 400)
  
# Função para autenticar um usuário
def authenticate(username, password):
    """
    Verifica se o usuário e senha são válidos.

    Args:
        username (str): Nome do usuário.
        password (str): Senha do usuário.

    Returns:
        bool: True se as credenciais forem válidas, False caso contrário.
    """
    accounts = load_account_service()["Users"]      # Carrega a lista de usuários do estado do AccountService
    for user in accounts:       # Itera sobre os usuários
        if user["UserName"] == username and user["Password"] == password:       # Verifica se o nome de usuário e senha correspondem
            return True  # Retorna True se as credenciais forem válidas
    return False        # Retorna False se as credenciais forem inválidas

