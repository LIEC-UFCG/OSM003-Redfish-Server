from flask import jsonify, make_response
import readings

def get_operating_system():
    """
    Retorna informações detalhadas do sistema operacional no formato Redfish.

    Returns:
        flask.Response: Resposta JSON com os dados do sistema operacional.
    """
    operating_system = {
        "@odata.type": "#OperatingSystem.v1_0_2.OperatingSystem",
        "Id": "OperatingSystem",
        "Name": "Operating System",
        "AccumulatedRunTime": "Unknown",
        "Hostname": readings.get_hostname(),
        "KernelName": readings.get_kernel_name(),
        "KernelRelease": readings.get_kernel_release(),
        "KernelVersion": readings.get_kernel_version(),
        "LastBootTime": readings.get_last_boot_time(),
        "Container":{
            "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/OperatingSystem/Containers"
        },
        "LogServices": {
            "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/LogServices"
        },
        "Metrics": {
            "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/OperatingSystem/OperatingSystemMetrics"
        },
        "OperatingSystemName": readings.get_operating_system_name(),
        "ProcessorArchitecture": readings.get_processor_architecture(),
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "VirtualMachines": [], 
        "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/OperatingSystem",
    }
    return jsonify(operating_system)

def get_operating_system_metrics():
    """
    Retorna as métricas do sistema operacional, incluindo métricas de rede, memória, processador e volumes.

    Se o serviço de métricas estiver desabilitado, retorna apenas o campo ServiceEnabled como False.

    Returns:
        flask.Response: Resposta JSON com as métricas do sistema operacional ou ServiceEnabled=False.
    """
    if not readings.service_enabled_state["OperatingSystemMetrics"]:
        return jsonify({
            "ServiceEnabled": False
        })

    metrics = {
        "@odata.context": "/redfish/v1/$metadata#OperatingSystemMetrics.OperatingSystemMetrics",
        "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/OperatingSystem",
        "@odata.type": "#OperatingSystemMetrics.v1_0_0.OperatingSystemMetrics",
        "EthernetInterfaceMetrics": readings.get_ethernet_metrics(
            readings.service_enabled_state["EthernetInterfaceMetrics"]
        ),
        "MemoryMetrics": readings.get_memory_metrics(
            readings.service_enabled_state["MemoryMetrics"]
        ),
        "ProcessorMetrics": readings.get_processor_metrics(
            readings.service_enabled_state["ProcessorMetrics"]
        ),
        "VolumePartitionMetrics": readings.get_volume_metrics(
            readings.service_enabled_state["VolumePartitionMetrics"]
        ),
        "MetricsTimestamp": readings.get_metrics_timestamp(),
        "ServiceEnabled": readings.service_enabled_state["OperatingSystemMetrics"]
    }
    return jsonify(metrics)

def update_service_enabled(data):
    """
    Atualiza o estado ServiceEnabled das categorias de métricas do sistema operacional.

    Args:
        data (dict): Dicionário com as categorias e seus novos estados booleanos.

    Returns:
        flask.Response: Mensagem de sucesso ou erro caso a categoria seja inválida.
    """
    updated = False
    for category, state in data.items():
        if category in readings.service_enabled_state:
            readings.service_enabled_state[category] = bool(state)
            updated = True
        else:
            return make_response({"error": f"Invalid category: {category}"}, 400)
    
    if updated:
        readings.save_service_enabled_state(readings.service_enabled_state)
        return make_response({"message": "ServiceEnabled updated successfully"}, 200)