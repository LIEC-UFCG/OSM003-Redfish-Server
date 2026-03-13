import docker
from flask import jsonify, request, make_response
from datetime import datetime

def _get_docker_client():
    """
    Cria e valida um cliente Docker sob demanda.

    Returns:
        tuple: (client, None) em caso de sucesso, ou (None, mensagem_erro).
    """
    try:
        client = docker.from_env()
        client.ping()
        return client, None
    except Exception as e:
        return None, str(e)

def get_containers(system_id):
    """
    Retorna a coleção de containers Docker do sistema.

    Args:
        system_id (str): ID do sistema Redfish.

    Returns:
        flask.Response: Resposta JSON com a coleção de containers no formato Redfish.
    """
    client, error = _get_docker_client()
    if not client:
        return make_response({
            "error": "Docker daemon unavailable or permission denied.",
            "details": error
        }, 503)

    containers = client.containers.list(all=True)  # Obtém todos os containers, incluindo os parados

    container_list = []
    for container in containers:
        container_info = {
            "@odata.id": f"/redfish/v1/Systems/{system_id}/OperatingSystem/Containers/{container.id}",
            #"@odata.type": "#Container.v1_0_1.Container",
            #"Id": container.id,
            #"Members": [],  # Removido o link incorreto
            #"Members@odata.count": 0  # Adicionado 0, já que não há membros para este nível
        }
        container_list.append(container_info)

    response = {
        "@odata.id": f"/redfish/v1/Systems/{system_id}/OperatingSystem/Containers",
        "@odata.type": "#ContainerCollection.ContainerCollection",
        "Name": "Container Collection",
        "Members": container_list,
        "Members@odata.count": len(container_list)
    }
    return jsonify(response)

def get_container(system_id, container_id):
    """
    Retorna detalhes de um container Docker específico.

    Args:
        system_id (str): ID do sistema Redfish.
        container_id (str): ID do container Docker.

    Returns:
        flask.Response: Resposta JSON com os detalhes do container.
        tuple: (response, status_code) em caso de erro.
    """
    try:
        client, error = _get_docker_client()
        if not client:
            return make_response({
                "error": "Docker daemon unavailable or permission denied.",
                "details": error
            }, 503)

        container = client.containers.get(container_id)

        # Processa volumes do contêiner (mesmo que não existam)
        mounts = container.attrs.get('Mounts', [])
        volumes = []

        if mounts:  # Caso existam volumes montados
            for mount in mounts:
                volume_info = {
                    "VolumeName": mount.get('Name', 'Unknown'),
                    "HostPath": mount.get('Source', 'Unknown'),
                    "Path": mount.get('Destination', 'Unknown'),
                    "CapacityBytes": mount.get('SizeBytes', 'Unknown'),
                    "RelatedItem": []
                }
                volumes.append(volume_info)
        else:  # Caso não existam volumes, incluir estrutura vazia
            volumes = [
                {
                    "VolumeName": "None",
                    "HostPath": "None",
                    "Path": "None",
                    "CapacityBytes": "Unknown",
                    "RelatedItem": []
                }
            ]

        # Preenche a estrutura final do JSON
        container_info = {
            "@odata.id": f"/redfish/v1/Systems/{system_id}/OperatingSystem/Containers/{container.id}",
            "@odata.type": "#Container.v1_0_1.Container",
            "Id": container.id,
            "ContainerName": container.name,
            "ContainerState": container.status,
            "ContainerType": "OCI",
            "CpuCores": container.attrs['HostConfig'].get('CpuCount', 'Unknown'),
            "CreateTime": container.attrs['Created'],
            "MemoryBytes": container.stats(stream=False).get('memory_stats', {}).get('usage', 0),
            "Status": "OK" if container.status == "running" else "Stopped",
            "Images": [
                {
                    "ImageHash": container.attrs['Config'].get('Image', 'Unknown'),
                    "ImageName": container.attrs.get('Config', {}).get('Image', 'Unknown'),
                    "ImageSizeBytes": container.attrs.get('Size', 'Unknown'),
                    "ImageType": "OCI",
                    "ImageVersion": container.attrs['Config'].get('Image', 'Unknown').split(':')[-1]
                }
            ],
            "NetworkInterfaces": [
                {
                    "InterfaceName": interface_name,
                    "Network": interface_info.get('NetworkID', 'Unknown'),
                    "Subnet": interface_info.get('IPAddress', 'Unknown'),
                    "IPAddresses": [interface_info.get('IPAddress', 'Unknown')]
                }
                for interface_name, interface_info in container.attrs.get('NetworkSettings', {}).get('Networks', {}).items()
            ],
            "Volumes": volumes,  # Inclui sempre a seção Volumes com estrutura padrão ou preenchida
            "Actions": {
                "#Container.Reset": {
                    "target": f"/redfish/v1/Systems/{system_id}/OperatingSystem/Containers/{container_id}/Actions/Container.Reset",
                    "title": "Reset Container"
                },
                "#Container.Start": {
                    "target": f"/redfish/v1/Systems/{system_id}/OperatingSystem/Containers/{container_id}/Actions/Container.Start",
                    "title": "Start Container"
                },
                "#Container.Stop": {
                    "target": f"/redfish/v1/Systems/{system_id}/OperatingSystem/Containers/{container_id}/Actions/Container.Stop",
                    "title": "Stop Container"
                }
            }
        }

        return jsonify(container_info), 200

    except docker.errors.NotFound:
        return make_response({"error": "Container not found"}, 404)
    except Exception as e:
        return make_response({"error": f"Unexpected error: {str(e)}"}, 500)


def start_container(container_id):
    """
    Inicia um container Docker.

    Args:
        container_id (str): ID do container Docker.

    Returns:
        flask.Response: Mensagem de sucesso ou erro.
    """
    try:
        client, error = _get_docker_client()
        if not client:
            return make_response({
                "error": "Docker daemon unavailable or permission denied.",
                "details": error
            }, 503)

        container = client.containers.get(container_id)
        container.start()
        return make_response({"message": "Container started successfully"}, 200)
    except docker.errors.NotFound:
        return make_response({"error": "Container not found"}, 404)

def stop_container(container_id):
    """
    Para um container Docker.

    Args:
        container_id (str): ID do container Docker.

    Returns:
        flask.Response: Mensagem de sucesso ou erro.
    """
    try:
        client, error = _get_docker_client()
        if not client:
            return make_response({
                "error": "Docker daemon unavailable or permission denied.",
                "details": error
            }, 503)

        container = client.containers.get(container_id)
        container.stop()
        return make_response({"message": "Container stopped successfully"}, 200)
    except docker.errors.NotFound:
        return make_response({"error": "Container not found"}, 404)

def reset_container(container_id):
    """
    Reinicia um container Docker.

    Args:
        container_id (str): ID do container Docker.

    Returns:
        flask.Response: Mensagem de sucesso ou erro.
    """
    try:
        client, error = _get_docker_client()
        if not client:
            return make_response({
                "error": "Docker daemon unavailable or permission denied.",
                "details": error
            }, 503)

        container = client.containers.get(container_id)
        container.restart()
        return make_response({"message": "Container reset successfully"}, 200)
    except docker.errors.NotFound:
        return make_response({"error": "Container not found"}, 404)
