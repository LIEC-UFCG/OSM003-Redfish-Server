import bcrypt
import json
import os
from flask import jsonify, request, make_response
import bcrypt
from accountservice import account_service_state
import re
import logging

ACCOUNTS_FILE = "accounts.json"

def senha_valida(password):
    """
    Verifica se a senha atende aos critérios de comprimento mínimo e máximo.
    Args:
        password (str): Senha a ser verificada.
    Returns:
        bool: True se a senha for válida, False caso contrário.
    """
    min_len = account_service_state.get("MinPasswordLength", 8)
    max_len = account_service_state.get("MaxPasswordLength", 32)
    if not isinstance(password, str):
        return False
    if not (min_len <= len(password) <= max_len):
        return False
    # Complexidade: pelo menos 1 maiúscula, 1 minúscula, 1 número, 1 símbolo
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    # Blacklist de senhas fracas
    blacklist = ["admin", "123456", "password", "senha", "admin123"]
    if password.lower() in blacklist:
        return False
    return True





# Função para gerar um hash de senha
def hash_password(password):
    """
    Gera um hash seguro para a senha fornecida.

    Args:
        password (str): Senha em texto puro.

    Returns:
        str: Hash da senha.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

# Estado inicial - Contas baseadas no ManagerAccount
default_accounts = {
    "1": {
        "Id": "1",
        "UserName": "admin",
        "RoleId": "Administrator",
        "Enabled": True,
        "Locked": False,
        "PasswordChangeRequired": False,
        "Password": hash_password("@Admin123")
    },
    "2": {
        "Id": "2",
        "UserName": "user",
        "RoleId": "Operator",
        "Enabled": True,
        "Locked": False,
        "PasswordChangeRequired": False,
        "Password": hash_password("@User123")
    },
    "3": {
        "Id": "3",
        "UserName": "teste",
        "RoleId": "ReadOnly",
        "Enabled": True,
        "Locked": False,
        "PasswordChangeRequired": False,
        "Password": hash_password("@Teste123")
    }
}

# Função para carregar contas do JSON
def load_accounts():
    """
    Carrega contas do arquivo JSON, se houver erro retorna as contas padrão.

    Returns:
        dict: Dicionário de contas carregadas ou padrão.
    """
    """Carrega contas do arquivo JSON, se houver erro, retorna as contas padrão."""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Erro: Formato inválido em accounts.json. Usando contas padrão.")
        except Exception as e:
            print(f"Erro inesperado: {e}. Usando contas padrão.")
    return default_accounts.copy()

# Função para salvar contas no JSON
def save_accounts(accounts):
    """
    Salva as contas no arquivo JSON.

    Args:
        accounts (dict): Dicionário de contas a serem salvas.
    """
    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(accounts, file, indent=4)

accounts = load_accounts()

def verify_password(hashed_password, user_password):
    """
    Verifica se a senha fornecida corresponde ao hash armazenado.

    Args:
        hashed_password (str): Hash da senha armazenada.
        user_password (str): Senha fornecida pelo usuário.

    Returns:
        bool: True se a senha corresponder, False caso contrário.
    """
    return bcrypt.checkpw(user_password.encode(), hashed_password.encode())


def get_account(account_id):
    """
    Retorna os detalhes de um ManagerAccount.

    Args:
        account_id (str): ID da conta.

    Returns:
        flask.Response: JSON com os detalhes da conta ou erro 404 se não encontrada.
    """
    if account_id in accounts:
        account_data = accounts[account_id]
        response = {
            "@odata.id": f"/redfish/v1/AccountService/Accounts/{account_id}",
            "@odata.type": "#ManagerAccount.v1_13_0.ManagerAccount",
            "Id": account_data["Id"],
            "Name": "User Account",
            "AccountTypes": ["Redfish"],
            "UserName": account_data["UserName"],
            "RoleId": account_data["RoleId"],
            "Enabled": account_data["Enabled"],
            "Locked": account_data["Locked"],
            "PasswordChangeRequired": account_data["PasswordChangeRequired"],
            "Links": {
                "Role": {
                    "@odata.id": f"/redfish/v1/AccountService/Roles/{account_data['RoleId']}"
                }
            }
        }
        return jsonify(response)

    return make_response({"error": "Account not found"}, 404)

def create_account():
    try:
        global accounts

        accounts = load_accounts()
        data = request.json
        username = data.get("UserName")  # 🔹 Define o nome de usuário antes de tudo

        if not username or "RoleId" not in data or "Password" not in data:
            return {"error": "Missing required fields (UserName, RoleId, Password)"}, 400

        # Validação de senha
        if not senha_valida(data["Password"]):
            return {
                "error": f"Password must be between {account_service_state['MinPasswordLength']} and {account_service_state['MaxPasswordLength']} characters."
            }, 400

        # 🔍 Logs de depuração
        logging.debug(f"Existing accounts: {[a['UserName'] for a in accounts.values()]}")
        logging.debug(f"Requested username: {username}")

        # Verifica duplicidade de nome de usuário
        if any(acc["UserName"].lower() == username.lower() for acc in accounts.values()):
            logging.warning(f"Tentativa de criar usuário duplicado: {username}")
            return {"error": "UserName already exists"}, 400

        # Gera novo ID incremental
        if accounts:
            new_id = str(max(map(int, accounts.keys())) + 1)
        else:
            new_id = "1"

        # Criptografa a senha
        hashed_password = bcrypt.hashpw(data["Password"].encode(), bcrypt.gensalt()).decode()

        # Cria o dicionário da nova conta
        new_account = {
            "Id": new_id,
            "UserName": username,
            "RoleId": data["RoleId"],
            "Enabled": data.get("Enabled", True),
            "Locked": data.get("Locked", False),
            "PasswordChangeRequired": data.get("PasswordChangeRequired", False),
            "Password": hashed_password
        }

        # Salva no banco local (ou arquivo)
        accounts[new_id] = new_account
        save_accounts(accounts)

        # Retorno padrão Redfish
        return {
            "@odata.id": f"/redfish/v1/AccountService/Accounts/{new_id}",
            "UserName": username
        }, 201

    except Exception as e:
        logging.error(f"Erro ao criar conta: {e}")
        return {"error": f"Internal server error: {e}"}, 500




def update_account(account_id):
    """
    Atualiza propriedades de um ManagerAccount.

    Args:
        account_id (str): ID da conta a ser atualizada.

    Returns:
        tuple: (dict, status_code)
    """
    try:
        if account_id not in accounts:
            return {"error": "Account not found"}, 404

        data = request.json or {}
        if not isinstance(data, dict):
            return {"error": "Invalid JSON payload"}, 400

        # Verifica duplicidade de UserName
        if "UserName" in data:
            if any(acc["UserName"] == data["UserName"] and acc["Id"] != account_id for acc in accounts.values()):
                return {"error": "UserName already exists"}, 400
            accounts[account_id]["UserName"] = data["UserName"]

        # Atualiza campos booleanos permitidos
        for key in ["Enabled", "Locked", "PasswordChangeRequired"]:
            if key in data:
                accounts[account_id][key] = data[key]

        # Atualiza senha
        if "Password" in data:
            if not senha_valida(data["Password"]):
                return {
                    "error": f"Password must be between {account_service_state['MinPasswordLength']} and {account_service_state['MaxPasswordLength']} characters."
                }, 400
            hashed = bcrypt.hashpw(data["Password"].encode(), bcrypt.gensalt()).decode()
            accounts[account_id]["Password"] = hashed
            accounts[account_id]["PasswordChangeRequired"] = False

        save_accounts(accounts)
        return {"message": "Account updated successfully"}, 200

    except Exception as e:
        print("Erro ao atualizar conta:", e)
        return {"error": f"Internal server error: {e}"}, 500


def delete_account(account_id):
    """
    Remove um ManagerAccount.
    """
    try:
        if account_id not in accounts:
            return {"error": "Account not found"}, 404

        if accounts[account_id]["UserName"].lower() == "admin":
            return {"error": "Cannot delete default admin account"}, 403

        del accounts[account_id]
        save_accounts(accounts)
        return {"message": "Account deleted successfully"}, 200

    except Exception as e:
        print("Erro ao deletar conta:", e)
        return {"error": f"Internal server error: {e}"}, 500

def get_accounts():
    """
    Retorna a coleção de contas (ManagerAccount Collection).

    Returns:
        flask.Response: JSON com a coleção de contas.
    """
    response = {
        #"@odata.context": "/redfish/v1/$metadata#ManagerAccountCollection.ManagerAccountCollection",
        "@odata.id": "/redfish/v1/AccountService/Accounts",
        "@odata.type": "#ManagerAccountCollection.ManagerAccountCollection",
        "Name": "Accounts Collection",
        "Members": [{"@odata.id": f"/redfish/v1/AccountService/Accounts/{account_id}"} for account_id in accounts.keys()],
        "Members@odata.count": len(accounts)
    }
    return jsonify(response)


# Inicializa a lista de contas
accounts = load_accounts()

# Se o arquivo não existia, salva o padrão com senhas criptografadas
if not os.path.exists(ACCOUNTS_FILE):
    save_accounts(accounts)
