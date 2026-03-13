from functools import wraps
from flask import request, make_response, jsonify
import base64
import bcrypt
import json
import os
from session import save_sessions
import time
from config import SESSION_TIMEOUT
from roles import default_roles
from privilegeregistry import priv
from accountservice import account_service_state, save_account_service
from manageraccount import save_accounts
from logservice import add_auth_log_entry, add_audit_log_entry, add_error_log_entry
import readings

PRIVILEGE_REGISTRY_FILE = "privilege_registry.json"

SESSIONS_FILE = "sessions.json"
ACCOUNTS_FILE = "accounts.json"

def load_privilege_registry():
    """
    Carrega o arquivo privilege_registry.json e retorna o conteúdo.

    Returns:
        dict: Conteúdo do privilege_registry.json.
    """
    if os.path.exists(PRIVILEGE_REGISTRY_FILE):
        with open(PRIVILEGE_REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {}

def load_sessions():
    """
    Carrega as sessões salvas do arquivo JSON.

    Returns:
        dict: Dicionário com as sessões ativas. Retorna {} se o arquivo não existir ou estiver corrompido.
    """
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}

def load_accounts():
    """
    Carrega as contas de usuário do arquivo JSON.

    Returns:
        dict: Dicionário com as contas de usuário. Retorna {} se o arquivo não existir.
    """
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as file:
            return json.load(file)
    return {}



def requires_authentication(func):
    """
    Decorador que exige autenticação para acessar a rota protegida.

    O usuário pode se autenticar via token de sessão (X-Auth-Token) ou via autenticação básica HTTP.
    Se a sessão expirar, ela é removida. Se a autenticação for bem-sucedida, a função decorada é executada.

    Args:
        func (callable): Função de rota Flask a ser protegida.

    Returns:
        callable: Função wrapper que exige autenticação.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        sessions = load_sessions()
        current_time = time.time()

        # --- Autenticação por token ---
        auth_token = request.headers.get("X-Auth-Token")
        for sid, session in list(sessions.items()):
            if auth_token == session.get("Token"):
                # Verifica se expirou
                if current_time > session["ExpirationTime"]:
                    del sessions[sid]
                    save_sessions(sessions)
                    add_auth_log_entry(
                        system_id=readings.machine_id(),
                        logservice_id="Log1",
                        message=f"Session expired for user {session.get('UserName')}",
                        user_name=session.get('UserName'),
                        severity="Warning",
                        message_id="Auth.Session.Expired"
                    )
                    return make_response({"error": "Session expired"}, 401)

                accounts = load_accounts()
                username = session.get("UserName")
                user = next((acc for acc in accounts.values() if acc["UserName"] == username), None)
                if user:
                    # Checagem padrão: desabilitada ou bloqueada manualmente
                    if not user.get("Enabled", True):
                        return make_response({"error": "Service disabled"}, 401)


                    # BLOQUEIO AUTOMÁTICO
                    threshold = account_service_state.get("AccountLockoutThreshold", 5)
                    duration = account_service_state.get("AccountLockoutDuration", 600)
                    reset_after = account_service_state.get("AccountLockoutCounterResetAfter", 300)
                    reset_enabled = account_service_state.get("AccountLockoutCounterResetEnabled", True)
                    now = time.time()

                    user.setdefault("_failed_attempts", 0)
                    user.setdefault("_last_failed_attempt", 0)
                    user.setdefault("_locked_until", 0)
                    user.setdefault("Locked", False)

                    # Se está bloqueado automaticamente, verifica se já pode desbloquear
                    if user.get("Locked", False):
                        if user["_locked_until"] and now >= user["_locked_until"]:
                            # Desbloqueio automático após o tempo
                            user["Locked"] = False
                            user["_failed_attempts"] = 0
                            user["_locked_until"] = 0
                            save_accounts(accounts)
                        else:
                            add_auth_log_entry(
                                system_id=readings.machine_id(),
                                logservice_id="Log1",
                                message=f"Blocked login attempt for locked account {username}",
                                user_name=username,
                                severity="Critical",
                                message_id="Auth.Account.Locked"
                            )
                            return make_response({"error": "Account locked"}, 401)

                    if user.get("PasswordChangeRequired", False):
                        add_auth_log_entry(
                            system_id=readings.machine_id(),
                            logservice_id="Log1",
                            message=f"Login attempt for {username} with password change required",
                            user_name=username,
                            severity="Warning",
                            message_id="Auth.Login.Failure"
                        )
                        return make_response({"error": "Password must be changed"}, 401)
                    
                    # Reset automático do contador se habilitado
                    if reset_enabled and now - user["_last_failed_attempt"] > reset_after:
                        user["_failed_attempts"] = 0


                # Estende a sessão
                session["ExpirationTime"] = current_time + SESSION_TIMEOUT
                sessions[sid] = session
                save_sessions(sessions)
                return func(*args, **kwargs)

        # --- Autenticação básica ---
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            encoded_credentials = auth_header.split(" ")[1]
            try:
                decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
                username, password = decoded_credentials.split(":", 1)
                accounts = load_accounts()
                user = next((acc for acc in accounts.values() if acc["UserName"] == username), None)
                if user:
                    # Checagem padrão: desabilitada ou bloqueada manualmente
                    if not user.get("Enabled", True):
                        return make_response({"error": "Service disabled"}, 401)

                    # BLOQUEIO AUTOMÁTICO
                    threshold = account_service_state.get("AccountLockoutThreshold", 5)
                    duration = account_service_state.get("AccountLockoutDuration", 600)
                    reset_after = account_service_state.get("AccountLockoutCounterResetAfter", 300)
                    reset_enabled = account_service_state.get("AccountLockoutCounterResetEnabled", True)
                    now = time.time()

                    user.setdefault("_failed_attempts", 0)
                    user.setdefault("_last_failed_attempt", 0)
                    user.setdefault("_locked_until", 0)
                    user.setdefault("Locked", False)

                    # Se está bloqueado, verifica se já pode desbloquear
                    if user.get("Locked", False):
                        if user["_locked_until"] and now >= user["_locked_until"]:
                            user["Locked"] = False
                            user["_failed_attempts"] = 0
                            user["_locked_until"] = 0
                            save_accounts(accounts)
                        else:
                            return make_response({"error": "Account locked"}, 401)


                    if user.get("PasswordChangeRequired", False):
                        add_auth_log_entry(
                            system_id=readings.machine_id(),
                            logservice_id="Log1",
                            message=f"Login attempt for {username} with password change required",
                            user_name=username,
                            severity="Warning",
                            message_id="Auth.Login.Failure"
                        )
                        return make_response({"error": "Password must be changed"}, 401)

                    # Reset automático do contador se habilitado
                    if reset_enabled and now - user["_last_failed_attempt"] > reset_after:
                        user["_failed_attempts"] = 0

                    # Validação da senha
                    if bcrypt.checkpw(password.encode(), user["Password"].encode()):
                        user["_failed_attempts"] = 0
                        user["_last_failed_attempt"] = 0
                        save_accounts(accounts)
                        return func(*args, **kwargs)
                    else:
                        user["_failed_attempts"] += 1
                        user["_last_failed_attempt"] = now
                        if user["_failed_attempts"] >= threshold:
                            user["Locked"] = True
                            user["_locked_until"] = now + duration
                            add_auth_log_entry(
                                system_id=readings.machine_id(),
                                logservice_id="Log1",
                                message=f"Blocked login attempt for locked account {username}",
                                user_name=username,
                                severity="Critical",
                                message_id="Auth.Account.Locked"
                            )
                        save_accounts(accounts)
                        return make_response({"error": "Invalid credentials."}, 401)
            except Exception:
                add_error_log_entry(
                    system_id=readings.machine_id(),
                    logservice_id="Log1",
                    message=f"Exception in authentication: {str(e)}",
                    user_name=username if 'username' in locals() else None,
                    severity="Critical",
                    message_id="Error.Auth.Exception"
                )

        return make_response({"error": "Unauthorized"}, 401)

    return wrapper




def get_user_role_id():
    """
    Obtém o RoleId do usuário autenticado na requisição.

    Verifica o token de sessão (X-Auth-Token) ou as credenciais de autenticação básica HTTP.
    Retorna o RoleId associado ao usuário autenticado, se válido.

    Returns:
        str or None: RoleId do usuário autenticado, ou None se não autenticado.
    """
    sessions = load_sessions()
    token = request.headers.get("X-Auth-Token")
    current_time = time.time()

    # Checa sessão via token
    for sid, session in sessions.items():
        if session.get("Token") == token and current_time < session["ExpirationTime"]:
            return session["RoleId"]

    # Checa autenticação básica
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        import base64
        decoded = base64.b64decode(auth_header.split()[1]).decode()
        username, _ = decoded.split(":", 1)

        accounts = load_accounts()
        user = next((u for u in accounts.values() if u["UserName"] == username), None)
        if user:
            return user["RoleId"]

    return None

def requires_privilege(entity):
    """
    Decorador que exige privilégios específicos para acessar uma rota.

    Verifica se o usuário autenticado possui os privilégios necessários para a entidade e método HTTP
    solicitados, conforme o Privilege Registry. Considera também SubordinateOverrides se definidos.

    Args:
        entity (str): Nome da entidade Redfish para checagem de privilégio.

    Returns:
        callable: Função decoradora que protege a rota.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            method = request.method.upper()
            role_id = get_user_role_id()
            if not role_id:
                return make_response({"error": "Unauthorized"}, 401)

            role = default_roles.get(role_id)
            if not role:
                return make_response({"error": "Role not found"}, 403)

            assigned_privs = set(role.get("AssignedPrivileges", []))
            privilege_registry = load_privilege_registry()
            mappings = privilege_registry.get("Mappings", [])

            for mapping in mappings:
                if mapping.get("Entity") == entity:
                    # Verifica SubordinateOverrides
                    sub_overrides = mapping.get("SubordinateOverrides", [])
                    found_override = False
                    for override in sub_overrides:
                        for target in override.get("Targets", []):
                            target_variants = [
                                target.lower(),
                                target.lower() + "s",
                                target.lower().replace("collection", "s"),
                                target.lower().replace("collection", "")
                            ]
                            if any(variant in request.path.lower() for variant in target_variants):
                                override_map = override.get("OperationMap", {})
                                if method in override_map:
                                    required_privs = override_map.get(method, [])
                                    for item in required_privs:
                                        if any(priv in assigned_privs for priv in item.get("Privilege", [])):
                                            return func(*args, **kwargs)
                                    found_override = True
                    # Se encontrou override mas não tinha privilégio, bloqueia
                    if found_override:
                        return make_response({"error": "Insufficient privileges (subordinate)"}, 403)

                    # Caso não tenha override, segue o padrão
                    operation_map = mapping.get("OperationMap", {})
                    required_privs = operation_map.get(method, [])
                    for item in required_privs:
                        if any(priv in assigned_privs for priv in item.get("Privilege", [])):
                            return func(*args, **kwargs)

                    return make_response({"error": "Insufficient privileges"}, 403)

            return make_response({"error": "Entity or method not found in privilege registry"}, 403)

        return wrapper
    return decorator