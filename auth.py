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
    """Load privilege_registry.json file and return content.
    
    Returns:
        dict: Content of privilege_registry.json.
    """
    if os.path.exists(PRIVILEGE_REGISTRY_FILE):
        with open(PRIVILEGE_REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {}

def load_sessions():
    """Load saved sessions from JSON file.
    
    Returns:
        dict: Dictionary with active sessions. Returns {} if file doesn't exist or is corrupted.
    """
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}

def load_accounts():
    """Load user accounts from JSON file.
    
    Returns:
        dict: Dictionary with user accounts. Returns {} if file doesn't exist.
    """
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as file:
            return json.load(file)
    return {}



def requires_authentication(func):
    """Decorator that requires authentication to access protected route.
    
    User can authenticate via session token (X-Auth-Token) or HTTP Basic Authentication.
    If session expires, it is removed. If authentication succeeds, decorated function is executed.
    
    Args:
        func (callable): Flask route function to be protected.
    
    Returns:
        callable: Wrapper function that requires authentication.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        sessions = load_sessions()
        current_time = time.time()

        # --- Authentication via token ---
        auth_token = request.headers.get("X-Auth-Token")
        for sid, session in list(sessions.items()):
            if auth_token == session.get("Token"):
                # Check if expired
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
                    # Default check: disabled or manually blocked
                    if not user.get("Enabled", True):
                        return make_response({"error": "Service disabled"}, 401)


                    # AUTOMATIC LOCKOUT
                    threshold = account_service_state.get("AccountLockoutThreshold", 5)
                    duration = account_service_state.get("AccountLockoutDuration", 600)
                    reset_after = account_service_state.get("AccountLockoutCounterResetAfter", 300)
                    reset_enabled = account_service_state.get("AccountLockoutCounterResetEnabled", True)
                    now = time.time()

                    user.setdefault("_failed_attempts", 0)
                    user.setdefault("_last_failed_attempt", 0)
                    user.setdefault("_locked_until", 0)
                    user.setdefault("Locked", False)

                    # If locked automatically, check if can unlock now
                    if user.get("Locked", False):
                        if user["_locked_until"] and now >= user["_locked_until"]:
                            # Automatic unlock after time
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
                    
                    # Automatic counter reset if enabled
                    if reset_enabled and now - user["_last_failed_attempt"] > reset_after:
                        user["_failed_attempts"] = 0


                # Extend session
                session["ExpirationTime"] = current_time + SESSION_TIMEOUT
                sessions[sid] = session
                save_sessions(sessions)
                return func(*args, **kwargs)

        # --- Basic Authentication ---
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            encoded_credentials = auth_header.split(" ")[1]
            try:
                decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
                username, password = decoded_credentials.split(":", 1)
                accounts = load_accounts()
                user = next((acc for acc in accounts.values() if acc["UserName"] == username), None)
                if user:
                    # Default check: disabled or manually blocked
                    if not user.get("Enabled", True):
                        return make_response({"error": "Service disabled"}, 401)

                    # AUTOMATIC LOCKOUT
                    threshold = account_service_state.get("AccountLockoutThreshold", 5)
                    duration = account_service_state.get("AccountLockoutDuration", 600)
                    reset_after = account_service_state.get("AccountLockoutCounterResetAfter", 300)
                    reset_enabled = account_service_state.get("AccountLockoutCounterResetEnabled", True)
                    now = time.time()

                    user.setdefault("_failed_attempts", 0)
                    user.setdefault("_last_failed_attempt", 0)
                    user.setdefault("_locked_until", 0)
                    user.setdefault("Locked", False)

                    # If locked, check if can unlock now
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

                    # Automatic counter reset if enabled
                    if reset_enabled and now - user["_last_failed_attempt"] > reset_after:
                        user["_failed_attempts"] = 0

                    # Password validation
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
    """Get RoleId of the authenticated user in the request.
    
    Checks session token (X-Auth-Token) or HTTP Basic Authentication credentials.
    Returns the RoleId associated with the authenticated user if valid.
    
    Returns:
        str or None: RoleId of authenticated user, or None if not authenticated.
    """
    sessions = load_sessions()
    token = request.headers.get("X-Auth-Token")
    current_time = time.time()

    # Check session via token
    for sid, session in sessions.items():
        if session.get("Token") == token and current_time < session["ExpirationTime"]:
            return session["RoleId"]

    # Check basic authentication
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
    """Decorator that requires specific privileges to access a route.
    
    Checks if authenticated user has necessary privileges for the requested entity and HTTP method,
    according to Privilege Registry. Also considers SubordinateOverrides if defined.
    
    Args:
        entity (str): Name of Redfish entity for privilege check.
    
    Returns:
        callable: Decorator function that protects the route.
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
                    # Check SubordinateOverrides
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
                    # If found override but no privilege, block
                    if found_override:
                        return make_response({"error": "Insufficient privileges (subordinate)"}, 403)

                    # If no override, follow standard
                    operation_map = mapping.get("OperationMap", {})
                    required_privs = operation_map.get(method, [])
                    for item in required_privs:
                        if any(priv in assigned_privs for priv in item.get("Privilege", [])):
                            return func(*args, **kwargs)

                    return make_response({"error": "Insufficient privileges"}, 403)

            return make_response({"error": "Entity or method not found in privilege registry"}, 403)

        return wrapper
    return decorator