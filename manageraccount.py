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
    """Check if password meets minimum and maximum length criteria.
    
    Args:
        password (str): Password to be checked.
    
    Returns:
        bool: True if password is valid, False otherwise.
    """
    min_len = account_service_state.get("MinPasswordLength", 8)
    max_len = account_service_state.get("MaxPasswordLength", 32)
    if not isinstance(password, str):
        return False
    if not (min_len <= len(password) <= max_len):
        return False
    # Complexity: at least 1 uppercase, 1 lowercase, 1 number, 1 symbol
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    # Blacklist of weak passwords
    blacklist = ["admin", "123456", "password", "senha", "admin123"]
    if password.lower() in blacklist:
        return False
    return True





# Function to generate password hash
def hash_password(password):
    """Generate secure hash for provided password.
    
    Args:
        password (str): Plain text password.
    
    Returns:
        str: Password hash.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

# Default initial state - Accounts based on ManagerAccount
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

# Function to load accounts from JSON
def load_accounts():
    """Load accounts from JSON file, if error return default accounts.
    
    Returns:
        dict: Dictionary of loaded or default accounts.
    """
    """Load accounts from JSON file, if error, return default accounts."""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error: Invalid format in accounts.json. Using default accounts.")
        except Exception as e:
            print(f"Unexpected error: {e}. Using default accounts.")
    return default_accounts.copy()

# Function to save accounts to JSON
def save_accounts(accounts):
    """Save accounts to JSON file.
    
    Args:
        accounts (dict): Dictionary of accounts to be saved.
    """
    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(accounts, file, indent=4)

accounts = load_accounts()

def verify_password(hashed_password, user_password):
    """Check if provided password matches stored hash.
    
    Args:
        hashed_password (str): Hash of stored password.
        user_password (str): Password provided by user.
    
    Returns:
        bool: True if password matches, False otherwise.
    """
    return bcrypt.checkpw(user_password.encode(), hashed_password.encode())


def get_account(account_id):
    """Return details of a ManagerAccount.
    
    Args:
        account_id (str): Account ID.
    
    Returns:
        flask.Response: JSON with account details or 404 error if not found.
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
        logging.error(f"Error creating account: {e}")
        return {"error": f"Internal server error: {e}"}, 500




def update_account(account_id):
    """Update properties of a ManagerAccount.
    
    Args:
        account_id (str): ID of account to be updated.
    
    Returns:
        tuple: (dict, status_code)
    """
    try:
        if account_id not in accounts:
            return {"error": "Account not found"}, 404

        data = request.json or {}
        if not isinstance(data, dict):
            return {"error": "Invalid JSON payload"}, 400

        # Check for duplicate UserName
        if "UserName" in data:
            if any(acc["UserName"] == data["UserName"] and acc["Id"] != account_id for acc in accounts.values()):
                return {"error": "UserName already exists"}, 400
            accounts[account_id]["UserName"] = data["UserName"]

        # Update allowed boolean fields
        for key in ["Enabled", "Locked", "PasswordChangeRequired"]:
            if key in data:
                accounts[account_id][key] = data[key]

        # Update password
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
        print("Error updating account:", e)
        return {"error": f"Internal server error: {e}"}, 500


def delete_account(account_id):
    """Remove a ManagerAccount.
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
        print("Error deleting account:", e)
        return {"error": f"Internal server error: {e}"}, 500

def get_accounts():
    """Return the collection of accounts (ManagerAccount Collection).
    
    Returns:
        flask.Response: JSON with account collection.
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


# Initialize account list
accounts = load_accounts()

# If file didn't exist, save default with encrypted passwords
if not os.path.exists(ACCOUNTS_FILE):
    save_accounts(accounts)
