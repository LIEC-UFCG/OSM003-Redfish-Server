import json
import os
from flask import jsonify, request, make_response
import readings

SESSION_SERVICE_FILE = "session_service.json"
system_id = readings.machine_id()

# Estado inicial padrão do SessionService
default_service_state = {
    "ServiceEnabled": True,
    "SessionTimeout": 600,
    "Status": {
        "Health": "OK",
        "State": "Enabled"
    }
}

# Função para carregar o estado do SessionService
def load_session_service():
    """
    Carrega o estado do SessionService do arquivo JSON.

    Returns:
        dict: Dicionário com o estado do SessionService carregado do arquivo ou o estado padrão se o arquivo não existir ou estiver inválido.
    """
    if os.path.exists(SESSION_SERVICE_FILE):
        try:
            with open(SESSION_SERVICE_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Erro ao carregar JSON: {e}")
    return default_service_state.copy()


# Função para salvar o estado do SessionService
def save_session_service(state):
    """
    Salva o estado do SessionService no arquivo JSON.

    Args:
        state (dict): Dicionário com o estado do SessionService a ser salvo.
    """
    with open(SESSION_SERVICE_FILE, "w") as file:
        json.dump(state, file, indent=4)

# Carregar estado inicial do SessionService
session_service_state = load_session_service()

def get_session_service():
    """
    Retorna os dados do SessionService no formato Redfish.

    Returns:
        flask.Response: Resposta JSON com os dados do SessionService.
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
    Atualiza propriedades do SessionService, como ServiceEnabled e SessionTimeout.

    Args:
        data (dict): Dicionário com as propriedades a serem atualizadas.

    Returns:
        flask.Response: Mensagem de sucesso se atualizado ou erro 400 se propriedades inválidas.
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
