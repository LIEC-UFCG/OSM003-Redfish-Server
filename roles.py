import json
import os
from flask import jsonify, make_response

ROLES_FILE = "roles.json"

# Definição inicial dos papéis (Roles) disponíveis no sistema
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

# Função para carregar roles
def load_roles():
    """
    Carrega os papéis (roles) do arquivo JSON.

    Returns:
        dict: Dicionário com os papéis carregados do arquivo ou os papéis padrão se o arquivo não existir.
    """
    if os.path.exists(ROLES_FILE):
        with open(ROLES_FILE, "r") as file:
            return json.load(file)
    return default_roles.copy()

# Função para salvar roles
def save_roles(roles):
    """
    Salva os papéis (roles) no arquivo JSON.

    Args:
        roles (dict): Dicionário de papéis a serem salvos.
    """
    with open(ROLES_FILE, "w") as file:
        json.dump(roles, file, indent=4)

# Inicializa a lista de roles
roles = load_roles()

def get_roles():
    """
    Retorna a coleção de roles disponíveis.

    Returns:
        flask.Response: JSON com a coleção de roles no formato Redfish.
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
    Retorna detalhes de um Role específico.

    Args:
        role_id (str): ID do papel (role) a ser retornado.

    Returns:
        flask.Response: JSON com os detalhes do role ou erro 404 se não encontrado.
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
