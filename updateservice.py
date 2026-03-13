import json
import os
from flask import jsonify, request, make_response

UPDATE_SERVICE_FILE = "update_service.json"

# Estado inicial padrão do UpdateService
default_update_service_state = {
    "ServiceEnabled": True,
    #"FirmwareInventory": "/redfish/v1/UpdateService/FirmwareInventory",
    #"SoftwareInventory": "/redfish/v1/UpdateService/SoftwareInventory",
    "HttpPushUri": "http://example.com/upload_firmware",
    "MaxImageSizeBytes": 100000000,
    "Status": {
        "Health": "OK",
        "State": "Enabled"
    }
}

# Carregar estado do UpdateService
def load_update_service():
    """
    Carrega o estado do UpdateService do arquivo JSON.

    Returns:
        dict: Dicionário com o estado do UpdateService carregado do arquivo ou o estado padrão se o arquivo não existir.
    """
    if os.path.exists(UPDATE_SERVICE_FILE):
        with open(UPDATE_SERVICE_FILE, "r") as file:
            return json.load(file)
    return default_update_service_state.copy()

# Salvar estado do UpdateService
def save_update_service(state):
    """
    Salva o estado do UpdateService no arquivo JSON.

    Args:
        state (dict): Dicionário com o estado do UpdateService a ser salvo.
    """
    with open(UPDATE_SERVICE_FILE, "w") as file:
        json.dump(state, file, indent=4)

# Inicializa o estado
update_service_state = load_update_service()


def get_update_service():
    """
    Retorna os dados do UpdateService no formato Redfish.

    Returns:
        flask.Response: Resposta JSON com os dados do UpdateService.
    """
    response = {
        "@odata.context": "/redfish/v1/$metadata#UpdateService.UpdateService",
        "@odata.id": "/redfish/v1/UpdateService",
        "@odata.type": "#UpdateService.v1_15_0.UpdateService",
        "Id": "UpdateService",
        "Name": "Update Service",
        "ServiceEnabled": update_service_state["ServiceEnabled"],
        #"FirmwareInventory": {
        #    "@odata.id": update_service_state["FirmwareInventory"]
        #},
        #"SoftwareInventory": {
        #    "@odata.id": update_service_state["SoftwareInventory"]
        #},
        "HttpPushUri": update_service_state["HttpPushUri"],
        "MaxImageSizeBytes": update_service_state["MaxImageSizeBytes"],
        "Status": update_service_state["Status"],
        "Actions": {
            "#UpdateService.SimpleUpdate": {
                "target": "/redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate",
                "title": "SimpleUpdate"
            }
        }
    }
    return jsonify(response)


def update_update_service(data):
    """
    Atualiza propriedades do UpdateService, como ServiceEnabled.

    Args:
        data (dict): Dicionário com as propriedades a serem atualizadas.

    Returns:
        flask.Response: Mensagem de sucesso se atualizado ou erro 400 se propriedades inválidas.
    """
    updated = False

    if "ServiceEnabled" in data:
        update_service_state["ServiceEnabled"] = bool(data["ServiceEnabled"])
        updated = True

    if updated:
        save_update_service(update_service_state)
        return make_response({"message": "UpdateService updated successfully."}, 200)
    
    return make_response({"error": "Invalid properties in request."}, 400)


def simple_update():
    """
    Realiza a atualização de firmware/software via SimpleUpdate.

    Valida se o serviço está habilitado e se o campo ImageURI está presente na requisição.

    Returns:
        flask.Response: Mensagem de aceite da atualização ou erro 400/403.
    """
    if not update_service_state["ServiceEnabled"]:
        return make_response({"error": "UpdateService is disabled."}, 403)

    data = request.json
    if "ImageURI" not in data:
        return make_response({"error": "ImageURI is required."}, 400)

    # Simula um processo de atualização
    return make_response({"message": f"Firmware update initiated from {data['ImageURI']}"}, 202)
