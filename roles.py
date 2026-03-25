import json
import os
from flask import jsonify, make_response

ROLES_FILE = "roles.json"

# Initial definition of roles available in the system
default_roles = {
    "Administrator": {
        "Id": "Administrator",
        "RoleId": "Administrator",
        "Name": "Administrator Role",
        "AssignedPrivileges": ["Login", "ConfigureManager", "ConfigureUsers", "ConfigureComponents", "ConfigureSelf"],
        "IsPredefined": True
    },
    "Operator": {
        "Id": "Operator",
        "RoleId": "Operator",
        "Name": "Operator Role",
        "AssignedPrivileges": ["Login", "ConfigureComponents", "ConfigureSelf"],
        "IsPredefined": True
    },
    "ReadOnly": {
        "Id": "ReadOnly",
        "RoleId": "ReadOnly",
        "Name": "Read-Only Role",
        "AssignedPrivileges": ["Login", "ConfigureSelf"],
        "IsPredefined": True
    }
}

# Function to load roles
def load_roles():
    """
    Loads the roles from JSON file.

    Returns:
        dict: Dictionary with roles loaded from file or default roles if file does not exist.
    """
    if os.path.exists(ROLES_FILE):
        with open(ROLES_FILE, "r") as file:
            return json.load(file)
    return default_roles.copy()

# Function to save roles
def save_roles(roles):
    """
    Saves the roles to JSON file.

    Args:
        roles (dict): Dictionary of roles to be saved.
    """
    with open(ROLES_FILE, "w") as file:
        json.dump(roles, file, indent=4)

# Initialize the roles list
roles = load_roles()

def get_roles():
    """
    Returns the collection of available roles.

    Returns:
        flask.Response: JSON with the roles collection in Redfish format.
    """
    response = {
        "@odata.id": "/redfish/v1/AccountService/Roles",
        "@odata.type": "#RoleCollection.RoleCollection",
        "Name": "Roles Collection",
        "Description": "Collection of all available roles",
        "Members": [{"@odata.id": f"/redfish/v1/AccountService/Roles/{role_id}"} for role_id in roles.keys()],
        "Members@odata.count": len(roles)
    }
    return jsonify(response)

def get_role(role_id):
    """
    Returns details of a specific role.

    Args:
        role_id (str): ID of the role to be returned.

    Returns:
        flask.Response: JSON with role details or 404 error if not found.
    """
    if role_id in roles:
        role_data = roles[role_id]
        response = {
            "@odata.id": f"/redfish/v1/AccountService/Roles/{role_id}",
            "@odata.type": "#Role.v1_3_3.Role",
            "Id": role_data["Id"],
            "RoleId": role_data["RoleId"],
            "Name": role_data["Name"],
            "AssignedPrivileges": role_data["AssignedPrivileges"],
            "IsPredefined": role_data["IsPredefined"]
        }
        return jsonify(response)

    return make_response({"error": "Role not found"}, 404)
