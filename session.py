import json
import os
from flask import jsonify, request, make_response
import bcrypt
import secrets
import time
from datetime import datetime
from uuid import uuid4
from config import SESSION_TIMEOUT
from logservice import add_auth_log_entry, add_audit_log_entry, add_error_log_entry
import readings

SESSIONS_FILE = "sessions.json"
ACCOUNTS_FILE = "accounts.json"

# Função para carregar sessões do JSON
def load_sessions():
    """
    Carrega as sessões do arquivo JSON.

    Returns:
        dict: Dicionário de sessões carregadas ou vazio se não houver sessões ou em caso de erro.
    """
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as file:
                data = file.read().strip()
                if not data:
                    return {}  # Se o arquivo estiver vazio, retorna um dicionário vazio
                return json.loads(data)
        except json.JSONDecodeError:
            return {}  # Se o conteúdo for inválido, retorna um dicionário vazio
    return {}

# Função para salvar sessões no JSON
def save_sessions(sessions):
    """
    Salva as sessões no arquivo JSON.

    Args:
        sessions (dict): Dicionário de sessões a serem salvas.
    """
    with open(SESSIONS_FILE, "w") as file:
        json.dump(sessions, file, indent=4)

# Inicializa a lista de sessões
sessions = load_sessions()

# Função para carregar contas de usuários do JSON
def load_accounts():
    """
    Carrega as contas de usuários do arquivo JSON.

    Returns:
        dict: Dicionário de contas carregadas ou vazio se não houver contas.
    """
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as file:
            return json.load(file)
    return {}

accounts = load_accounts()



def create_session():
    """
    Cria uma nova sessão autenticada para um usuário válido.

    Valida o usuário e senha, impede múltiplas sessões simultâneas para o mesmo usuário,
    gera um token seguro e salva a sessão.

    Returns:
        flask.Response: Resposta com os dados da sessão criada, cabeçalho X-Auth-Token e status 201,
                        ou erro 401/409 em caso de falha.
    """
    data = request.json
    username = data.get("UserName")
    password = data.get("Password")

    # Verifica se o usuário existe e a senha é válida
    user = next((acc for acc in accounts.values() if acc["UserName"] == username), None)
    
    # Verifica se o usuário existe
    if not user:
        add_auth_log_entry(
            system_id=readings.machine_id(),
            logservice_id="Log1",
            message=f"Failed login attempt for user {username} (user not found)",
            user_name=username,
            severity="Warning",
            message_id="Auth.Login.Failure"
        )
        return make_response({"error": "Invalid username or password"}, 401)

    # Verifica se a senha está correta
    hash_salvo = user["Password"].encode() if isinstance(user["Password"], str) else user["Password"]
    senha_correta = bcrypt.checkpw(password.encode(), hash_salvo)

    if not senha_correta:
        add_auth_log_entry(
            system_id=readings.machine_id(),
            logservice_id="Log1",
            message=f"Failed login attempt for user {username} (wrong password)",
            user_name=username,
            severity="Warning",
            message_id="Auth.Login.Failure"
        )
        return make_response({"error": "Invalid username or password"}, 401)

    sessions = load_sessions()

    # Limpa sessões expiradas
    current_time = time.time()
    expired_sessions = [sid for sid, sess in sessions.items()
                        if sess.get("ExpirationTime", 0) < current_time]
    for sid in expired_sessions:
        print(f"Removendo sessão expirada: {sid}")
        del sessions[sid]
    save_sessions(sessions)

    # Importante: recarrega sessões após limpeza
    # (ou continua usando `sessions` limpo diretamente, como abaixo)

    # Verifica se o usuário já tem uma sessão ativa
    for sid, sess in sessions.items():
        if sess["UserName"] == username:
            return make_response({
                "error": f"User '{username}' already has an active session.",
                "existing_session": {
                    "@odata.id": f"/redfish/v1/SessionService/Sessions/{sid}",
                    "Id": sid,
                    "UserName": username,
                    "CreatedTime": sess["CreatedTime"],
                    "ExpirationTime": sess["ExpirationTime"]
                }
            }, 409)

    # Gera um token seguro
    token = secrets.token_hex(32)
    #session_id = str(len(sessions) + 1)
    session_id = str(uuid4())  # Gera um UUID único para a sessão

    current_time = time.time()
    expiration_time = current_time + SESSION_TIMEOUT

    sessions[session_id] = {
        "UserName": username,
        "Token": token,
        "RoleId": user.get("RoleId", "ReadOnly"),
        "CreatedTime": current_time,
        "ExpirationTime": expiration_time
    }
    save_sessions(sessions)

    session_uri = f"/redfish/v1/SessionService/Sessions/{session_id}"
    response_body = {
        "@odata.id": session_uri,
        "Id": session_id,
        "Name": "User Session",
        "UserName": username,
        "Password": None,
        "CreatedTime": datetime.fromtimestamp(current_time).isoformat(),
        "ExpirationTime": datetime.fromtimestamp(expiration_time).isoformat()
    }

    response = make_response(response_body, 201)
    response.headers["X-Auth-Token"] = token
    response.headers["Location"] = session_uri
    response.headers["Access-Control-Expose-Headers"] = "X-Auth-Token"

    add_auth_log_entry(
        system_id=readings.machine_id(),
        logservice_id="Log1",
        message=f"User {username} logged in",
        user_name=username,
        severity="OK",
        message_id="Auth.Login.Success"
    )
    return response


def get_sessions():
    """
    Retorna a coleção de sessões (Session Collection).

    Returns:
        flask.Response: JSON com a coleção de sessões ativas.
    """
    sessions = load_sessions()
    response = {
        "@odata.id": "/redfish/v1/SessionService/Sessions",
        "@odata.type": "#SessionCollection.SessionCollection",
        "Name": "Session Collection",
        "Members": [{"@odata.id": f"/redfish/v1/SessionService/Sessions/{session_id}"} for session_id in sessions.keys()],
        "Members@odata.count": len(sessions)
    }
    return jsonify(response)

def get_session(session_id):
    """
    Retorna os detalhes de uma sessão específica, se o token for válido.

    Args:
        session_id (str): ID da sessão.

    Returns:
        flask.Response: JSON com os detalhes da sessão ou erro 403/404.
    """
    sessions = load_sessions()  # Certifica-se de carregar as sessões mais recentes
    
    if session_id not in sessions:
        return make_response({"error": "Session not found"}, 404)

    session_data = sessions.get(session_id)

    # Recupera o token da requisição
    request_token = request.headers.get("X-Auth-Token")

    # Garante que o token seja o mesmo da sessão solicitada
    if session_data["Token"] != request_token:
        return make_response({"error": "Access denied to this session"}, 403)

    current_time = time.time()
    expiration_time = current_time + SESSION_TIMEOUT

    if session_data:
        response = {
            "@odata.id": f"/redfish/v1/SessionService/Sessions/{session_id}",
            "@odata.type": "#Session.v1_8_0.Session",
            "Id": session_id,
            "Name": "User Session",
            "UserName": session_data["UserName"],
            "CreatedTime": datetime.fromtimestamp(current_time).isoformat(),
            "ExpirationTime": datetime.fromtimestamp(expiration_time).isoformat(),
        }
        return jsonify(response), 200

    return jsonify({"error": "Session not found."}), 404

def delete_session(session_id):
    """
    Remove uma sessão, se o token do request for o dono da sessão.

    Args:
        session_id (str): ID da sessão a ser removida.

    Returns:
        flask.Response: Mensagem de sucesso ou erro 403/404.
    """
    sessions = load_sessions()  # garante que estamos lendo do arquivo
    data = request.get_json(silent=True) or {}
    username = data.get("UserName", "")
    
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    session_data = sessions[session_id]
    request_token = request.headers.get("X-Auth-Token")

    # Verifica se o token do request é o dono da sessão
    if session_data["Token"] != request_token:
        return jsonify({"error": "Access denied to delete this session"}), 403

    del sessions[session_id]
    save_sessions(sessions)
    add_auth_log_entry(
        system_id=readings.machine_id(),
        logservice_id="Log1",
        message=f"User {session_data['UserName']} logged out",
        user_name=username,
        severity="OK",
        message_id="Auth.Logout.Success"
    )
    return jsonify({"message": "Session deleted successfully"}), 200

