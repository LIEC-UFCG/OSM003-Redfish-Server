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

# Function to load sessions from JSON
def load_sessions():
    """Load sessions from JSON file.
    
    Returns:
        dict: Dictionary of loaded sessions or empty if no sessions or error occurred.
    """
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as file:
                data = file.read().strip()
                if not data:
                    return {}  # If file is empty, return empty dictionary
                return json.loads(data)
        except json.JSONDecodeError:
            return {}  # If content is invalid, return empty dictionary
    return {}

# Function to save sessions to JSON
def save_sessions(sessions):
    """Save sessions to JSON file.
    
    Args:
        sessions (dict): Dictionary of sessions to be saved.
    """
    with open(SESSIONS_FILE, "w") as file:
        json.dump(sessions, file, indent=4)

# Initialize session list
sessions = load_sessions()

# Function to load user accounts from JSON
def load_accounts():
    """Load user accounts from JSON file.
    
    Returns:
        dict: Dictionary of loaded accounts or empty if no accounts.
    """
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
        except Exception:
            return {}
    return {}

accounts = load_accounts()



def create_session():
    """Create a new authenticated session for a valid user.
    
    Validates user and password, prevents multiple simultaneous sessions for same user,
    generates a secure token and saves the session.
    
    Returns:
        flask.Response: Response with session data, X-Auth-Token header and 201 status,
                        or 401/409 errors on failure.
    """
    data = request.json
    username = data.get("UserName")
    password = data.get("Password")

    # Check if user exists and password is valid
    user = next((acc for acc in accounts.values() if acc["UserName"] == username), None)
    
    # Check if user exists
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

    # Check if password is correct
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

    # Clean expired sessions
    current_time = time.time()
    expired_sessions = [sid for sid, sess in sessions.items()
                        if sess.get("ExpirationTime", 0) < current_time]
    for sid in expired_sessions:
        print(f"Removing expired session: {sid}")
        del sessions[sid]
    save_sessions(sessions)

    # Important: reload sessions after cleanup
    # (or continue using cleaned `sessions` directly, as below)

    # Check if user already has an active session
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

    # Generate a secure token
    token = secrets.token_hex(32)
    #session_id = str(len(sessions) + 1)
    session_id = str(uuid4())  # Generate unique UUID for session

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
    """Return the collection of sessions (Session Collection).
    
    Returns:
        flask.Response: JSON with active sessions collection.
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
    """Return details of a specific session if token is valid.
    
    Args:
        session_id (str): Session ID.
    
    Returns:
        flask.Response: JSON with session details or 403/404 error.
    """
    sessions = load_sessions()  # Ensure to load most recent sessions
    
    if session_id not in sessions:
        return make_response({"error": "Session not found"}, 404)

    session_data = sessions.get(session_id)

    # Retrieve token from request
    request_token = request.headers.get("X-Auth-Token")

    # Ensure token is same as session being requested
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
    """Remove a session if request token is the session owner.
    
    Args:
        session_id (str): ID of session to be removed.
    
    Returns:
        flask.Response: Success message or 403/404 error.
    """
    sessions = load_sessions()  # ensure we're reading from file
    data = request.get_json(silent=True) or {}
    username = data.get("UserName", "")
    
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    session_data = sessions[session_id]
    request_token = request.headers.get("X-Auth-Token")

    # Check if request token is the session owner
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

