import readings
from flask import jsonify, request
from ssdp_control import start_ssdp, stop_ssdp


def get_managers():
    """
    Returns the collection of managers available in the system.

    Returns:
        flask.Response: JSON with managers collection in Redfish format.
    """
    managers = {
        "@odata.context": "/redfish/v1/$metadata#ManagerCollection.ManagerCollection",
        "@odata.id": "/redfish/v1/Managers",
        "@odata.type": "#ManagerCollection.ManagerCollection",
        "Name": "Managers Collection",
        "Members": [
            {
                "@odata.id": "/redfish/v1/Managers/" + readings.machine_id()
            }
        ],
        "Members@odata.count": 1
    }
    return jsonify(managers)

def get_manager_details(manager_id):
    """
    Returns details for a specific manager.

    Args:
        manager_id (str): Manager ID.

    Returns:
        flask.Response: JSON with manager details or 404 error if not found.
    """
    if manager_id != readings.machine_id():
        return jsonify({"error": "Manager not found"}), 404

    manager = {
        "@odata.id": f"/redfish/v1/Managers/{manager_id}",
        "@odata.type": "#Manager.v1_20_0.Manager",
        "Id": manager_id,
        "Name": "Raspberry Pi Manager",
        "Description": "Raspberry Pi Manager",
        "ManagerType": "ManagementController",        # ManagementController: A generic manager used for devices without specific BMC or chassis functions.
        "Model": readings.model(),                                                       
        "UUID": readings.system_uuid(),
        "CommandShell": {
            "ServiceEnabled": readings.get_command_shell_service_enabled(),
            "MaxConcurrentSessions": readings.get_command_shell_max_sessions(),
            "ConnectTypesSupported": readings.get_command_shell_connect_types()
        },
        "Status": {
            "Health": "OK",
            "State": "Enabled"
        },
        "DateTime": readings.get_datetime(),
        "DateTimeLocalOffset": readings.get_datetime_offset(),
        "EthernetInterfaces": {
                "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/EthernetInterfaces"
        },
        "NetworkProtocol": {
            "@odata.id": f"/redfish/v1/Managers/{manager_id}/NetworkProtocol"                   # TODO: Verify endpoint
        },
        "Links": {
            "ManagerForChassis": [
                {
                    "@odata.id": "/redfish/v1/Chassis/" + readings.machine_id()
                }
            ],
            "ManagerForServers": [
                {
                    "@odata.id": "/redfish/v1/Systems/" + readings.machine_id()
                }
            ]
        }
    }
    return jsonify(manager)

def update_manager(manager_id):
    """
    Updates manager properties, such as DateTime, DateTimeLocalOffset and ServiceEnabled.

    Args:
        manager_id (str): Manager ID.

    Returns:
        flask.Response: Success message and updated fields, or error.
    """
    data = request.get_json()
    response = {}

    # Updates DateTime
    if "DateTime" in data:
        readings.set_datetime(data["DateTime"])
        response["DateTime"] = data["DateTime"]

    # Updates DateTimeLocalOffset
    if "DateTimeLocalOffset" in data:
        readings.set_datetime_offset(data["DateTimeLocalOffset"])
        response["DateTimeLocalOffset"] = data["DateTimeLocalOffset"]

    # Updates ServiceEnabled
    if "ServiceEnabled" in data:
        readings.set_service_enabled(data["ServiceEnabled"])
        response["ServiceEnabled"] = data["ServiceEnabled"]

    return jsonify({"Message": "Manager updated successfully", **response}), 200



def get_manager_network_protocol():
    """
    Returns manager network protocol configurations.

    Returns:
        flask.Response: JSON with network protocol configurations (FQDN, HTTPS, HostName).
    """
    network_protocol = {
        "@odata.type": "#ManagerNetworkProtocol.v1_10_1.ManagerNetworkProtocol",
        "Id": "NetworkProtocol",
        "Name": "Manager Network Protocol",
        "Description": "Manager Network Service",
        "FQDN": readings.get_fqdn(),  # Get fully qualified domain name
        "HTTPS": {
            "Port": readings.get_https_port(),
            "ProtocolEnabled": readings.get_https_protocol_enabled()
        },
        "SSDP": {
            "ProtocolEnabled": readings.get_ssdp_enabled(),  # bool
            "Port": 1900,  # SSDP standard port
            "NotifyTTL": 2,
            "NotifyMulticastIntervalSeconds": 30,
            "NotifyIPv6Scope": "Link"  # Or "Site", as appropriate
        },
        "HostName": readings.get_hostname(),  # Get hostname
        "@odata.id": "/redfish/v1/Managers/" + readings.machine_id() + "/NetworkProtocol"
    }
    return jsonify(network_protocol)

def update_network_protocol():
    """
    Updates manager network protocol configurations (FQDN, HTTPS.Port, HTTPS.ProtocolEnabled, SSDP).

    Returns:
        flask.Response: Success message and updated fields, or error.
    """
    data = request.get_json()
    response = {}

    # Updates FQDN
    if "FQDN" in data:
        readings.set_fqdn(data["FQDN"])
        response["FQDN"] = data["FQDN"]

    # Updates HTTPS.Port
    if "HTTPS" in data and isinstance(data["HTTPS"], dict):
        if "Port" in data["HTTPS"]:
            readings.set_https_port(data["HTTPS"]["Port"])
            response["HTTPS.Port"] = data["HTTPS"]["Port"]
        if "ProtocolEnabled" in data["HTTPS"]:
            readings.set_https_protocol_enabled(data["HTTPS"]["ProtocolEnabled"])
            response["HTTPS.ProtocolEnabled"] = data["HTTPS"]["ProtocolEnabled"]

    # Updates SSDP.ProtocolEnabled
    if isinstance(data.get("SSDP"), dict) and "ProtocolEnabled" in data["SSDP"]:
        enabled = data["SSDP"]["ProtocolEnabled"]
        readings.set_ssdp_enabled(enabled)
        response["SSDP.ProtocolEnabled"] = enabled
        if enabled:
            start_ssdp()
        else:
            stop_ssdp()

    if response:
        return jsonify({"Message": "NetworkProtocol updated successfully", **response}), 200
    else:
        return jsonify({"Message": "No valid fields provided"}), 400

