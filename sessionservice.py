import json
import os
from flask import jsonify, request, make_response

SESSION_SERVICE_FILE = "session_service.json"

# Default initial state of SessionService
default_service_state = {
    "ServiceEnabled": True,
    "SessionTimeout": 600,
    "Status": {
        "Health": "OK",
        "State": "Enabled"
    }
}

# Function to load SessionService state
def load_session_service():
    """
    Loads the SessionService state from a JSON file.

    Returns:
        dict: Dictionary with SessionService state loaded from file or default state if file doesn't exist or is invalid.
    """
    if os.path.exists(SESSION_SERVICE_FILE):
        try:
            with open(SESSION_SERVICE_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error loading JSON: {e}")
    return default_service_state.copy()


# Function to save SessionService state
def save_session_service(state):
    """
    Saves the SessionService state to a JSON file.

    Args:
        state (dict): Dictionary with SessionService state to be saved.
    """
    with open(SESSION_SERVICE_FILE, "w") as file:
        json.dump(state, file, indent=4)

# Load initial SessionService state
session_service_state = load_session_service()

def get_session_service():
    """
    Returns SessionService data in Redfish format.

    Returns:
        flask.Response: JSON response with SessionService data.
    """
    response = {
        #"@odata.context": "/redfish/v1/$metadata#SessionService.SessionService",
        "@odata.id": f"/redfish/v1/SessionService",
        "@odata.type": "#SessionService.v1_2_0.SessionService",
        "Id": "SessionService",
        "Name": "Session Service",
        "Description": "Session Service",
        "ServiceEnabled": session_service_state["ServiceEnabled"],
        "SessionTimeout": session_service_state["SessionTimeout"],
        "Sessions": {
            "@odata.id": f"/redfish/v1/SessionService/Sessions"
        },
        "Status": session_service_state["Status"]
    }
    return jsonify(response)

def update_session_service(data):
    """
    Updates SessionService properties such as ServiceEnabled and SessionTimeout.

    Args:
        data (dict): Dictionary with properties to be updated.

    Returns:
        flask.Response: Success message if updated or 400 error if invalid properties.
    """
    updated = False

    if "ServiceEnabled" in data:
        session_service_state["ServiceEnabled"] = bool(data["ServiceEnabled"])
        updated = True

    if "SessionTimeout" in data:
        session_service_state["SessionTimeout"] = int(data["SessionTimeout"])
        updated = True

    if updated:
        save_session_service(session_service_state)
        return make_response({"message": "SessionService updated successfully."}, 200)
    
    return make_response({"error": "Invalid properties in request."}, 400)
