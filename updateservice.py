import json
import os
from flask import jsonify, request, make_response

UPDATE_SERVICE_FILE = "update_service.json"

# Default initial state of UpdateService
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

# Load UpdateService state
def load_update_service():
    """
    Loads the UpdateService state from a JSON file.

    Returns:
        dict: Dictionary with UpdateService state loaded from file or default state if file doesn't exist.
    """
    if os.path.exists(UPDATE_SERVICE_FILE):
        with open(UPDATE_SERVICE_FILE, "r") as file:
            return json.load(file)
    return default_update_service_state.copy()

# Save UpdateService state
def save_update_service(state):
    """
    Saves the UpdateService state to a JSON file.

    Args:
        state (dict): Dictionary with UpdateService state to be saved.
    """
    with open(UPDATE_SERVICE_FILE, "w") as file:
        json.dump(state, file, indent=4)

# Initialize state
update_service_state = load_update_service()


def get_update_service():
    """
    Returns UpdateService data in Redfish format.

    Returns:
        flask.Response: JSON response with UpdateService data.
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
    Updates UpdateService properties such as ServiceEnabled.

    Args:
        data (dict): Dictionary with properties to be updated.

    Returns:
        flask.Response: Success message if updated or 400 error if invalid properties.
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
    Performs a firmware/software update via SimpleUpdate.

    Validates if the service is enabled and if the ImageURI field is present in the request.

    Returns:
        flask.Response: Update acceptance message or 400/403 error.
    """
    if not update_service_state["ServiceEnabled"]:
        return make_response({"error": "UpdateService is disabled."}, 403)

    data = request.json
    if "ImageURI" not in data:
        return make_response({"error": "ImageURI is required."}, 400)

    # Simulates an update process
    return make_response({"message": f"Firmware update initiated from {data['ImageURI']}"}, 202)
