import docker
from flask import jsonify, request, make_response
from datetime import datetime

client = None


def _get_client():
    """Return a Docker client when the daemon is available."""
    global client

    if client is not None:
        return client

    try:
        client = docker.from_env()
    except Exception:
        client = None

    return client


def _docker_unavailable_response():
    """Return a standard response when Docker is not reachable."""
    return make_response({"error": "Docker daemon unavailable"}, 503)


def _to_bytes(size_value):
    """Convert size values like '10G' or '512M' into bytes."""
    if isinstance(size_value, (int, float)):
        return int(size_value)

    if not isinstance(size_value, str):
        return 0

    text = size_value.strip().upper()
    if text.isdigit():
        return int(text)

    units = {
        "K": 1024,
        "M": 1024 ** 2,
        "G": 1024 ** 3,
        "T": 1024 ** 4,
    }

    suffix = text[-1:]
    if suffix in units:
        try:
            return int(float(text[:-1]) * units[suffix])
        except ValueError:
            return 0

    return 0


def _storage_limit_bytes(container):
    """Return container storage limit in bytes when available."""
    host_cfg = container.attrs.get("HostConfig", {})
    storage_opt = host_cfg.get("StorageOpt", {})

    if isinstance(storage_opt, dict):
        size_opt = storage_opt.get("size")
        limit = _to_bytes(size_opt)
        if limit > 0:
            return limit

    # Fallback to Docker-reported writable layer size when no explicit limit exists.
    size_rw = container.attrs.get("SizeRw")
    if isinstance(size_rw, (int, float)) and size_rw >= 0:
        return int(size_rw)

    return 0


def _interface_type_from_driver(driver_or_mode):
    """Map Docker network driver/mode to a reasonable interface type."""
    if not driver_or_mode:
        return "virtual"

    value = str(driver_or_mode).strip().lower()
    mapping = {
        "bridge": "veth",
        "host": "host",
        "overlay": "vxlan",
        "macvlan": "macvlan",
        "ipvlan": "ipvlan",
        "none": "none",
        "default": "veth",
    }
    return mapping.get(value, value)


def _resolve_interface_type(docker_client, container, interface_info):
    """Resolve interface type from network driver, then network mode."""
    network_id = interface_info.get("NetworkID")
    if network_id:
        try:
            network = docker_client.networks.get(network_id)
            driver = network.attrs.get("Driver")
            return _interface_type_from_driver(driver)
        except Exception:
            pass

    network_mode = container.attrs.get("HostConfig", {}).get("NetworkMode")
    return _interface_type_from_driver(network_mode)

def get_containers(system_id):
    """
    Returns the collection of Docker containers from the system.

    Args:
        system_id (str): Redfish system ID.

    Returns:
        flask.Response: JSON response with the collection of containers in Redfish format.
    """
    docker_client = _get_client()
    if docker_client is None:
        return _docker_unavailable_response()

    containers = docker_client.containers.list(all=True)  # Gets all containers, including stopped ones

    container_list = []
    for container in containers:
        container_info = {
            "@odata.id": f"/redfish/v1/Systems/{system_id}/OperatingSystem/Containers/{container.id}",
            #"@odata.type": "#Container.v1_0_1.Container",
            #"Id": container.id,
            #"Members": [],  # Removido o link incorreto
            #"Members@odata.count": 0  # Added 0, since there are no members for this level
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
    Returns details of a specific Docker container.

    Args:
        system_id (str): Redfish system ID.
        container_id (str): Docker container ID.

    Returns:
        flask.Response: JSON response with container details.
        tuple: (response, status_code) in case of error.
    """
    try:
        docker_client = _get_client()
        if docker_client is None:
            return _docker_unavailable_response()

        container = docker_client.containers.get(container_id)

        # Processes container volumes (even if they don't exist)
        mounts = container.attrs.get('Mounts', [])
        volumes = []

        if mounts:  # If volumes are mounted
            for mount in mounts:
                volume_info = {
                    "VolumeName": mount.get('Name', 'Unknown'),
                    "HostPath": mount.get('Source', 'Unknown'),
                    "Path": mount.get('Destination', 'Unknown'),
                    "CapacityBytes": mount.get('SizeBytes', 'Unknown'),
                    "RelatedItem": []
                }
                volumes.append(volume_info)
        else:  # If volumes don't exist, include empty structure
            volumes = [
                {
                    "VolumeName": "None",
                    "HostPath": "None",
                    "Path": "None",
                    "CapacityBytes": "Unknown",
                    "RelatedItem": []
                }
            ]

        # Fills the final JSON structure
        dns_servers = container.attrs.get('HostConfig', {}).get('Dns', [])

        container_info = {
            "@odata.id": f"/redfish/v1/Systems/{system_id}/OperatingSystem/Containers/{container.id}",
            "@odata.type": "#Container.v1_0_1.Container",
            "Id": container.id,
            "Name": container.name,
            "Status": {
                "Health": "OK" if container.status == "running" else "Warning",
                "State": "Enabled" if container.status == "running" else "Disabled"
            },
            "ContainerName": container.name,
            "ContainerState": container.status,
            "ContainerType": "OCI",
            "CpuCores": container.attrs['HostConfig'].get('CpuCount', 'Unknown'),
            "CreateTime": container.attrs['Created'],
            "MemoryBytes": container.stats(stream=False).get('memory_stats', {}).get('usage', 0),
            "StorageLimitBytes": _storage_limit_bytes(container),
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
                    "InterfaceType": _resolve_interface_type(docker_client, container, interface_info),
                    "Network": interface_info.get('NetworkID') or interface_name,
                    "Subnet": interface_info.get('IPAddress') or None,
                    "IPAddresses": [interface_info.get('IPAddress')] if interface_info.get('IPAddress') else [],
                    "DnsServers": dns_servers if isinstance(dns_servers, list) else []
                }
                for interface_name, interface_info in container.attrs.get('NetworkSettings', {}).get('Networks', {}).items()
            ],
            "Volumes": volumes,
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
    Starts a Docker container.

    Args:
        container_id (str): Docker container ID.

    Returns:
        flask.Response: Success or error message.
    """
    try:
        docker_client = _get_client()
        if docker_client is None:
            return _docker_unavailable_response()

        container = docker_client.containers.get(container_id)
        container.start()
        return make_response({"message": "Container started successfully"}, 200)
    except docker.errors.NotFound:
        return make_response({"error": "Container not found"}, 404)

def stop_container(container_id):
    """
    Stops a Docker container.

    Args:
        container_id (str): Docker container ID.

    Returns:
        flask.Response: Success or error message.
    """
    try:
        docker_client = _get_client()
        if docker_client is None:
            return _docker_unavailable_response()

        container = docker_client.containers.get(container_id)
        container.stop()
        return make_response({"message": "Container stopped successfully"}, 200)
    except docker.errors.NotFound:
        return make_response({"error": "Container not found"}, 404)

def reset_container(container_id):
    """
    Restarts a Docker container.

    Args:
        container_id (str): Docker container ID.

    Returns:
        flask.Response: Success or error message.
    """
    try:
        docker_client = _get_client()
        if docker_client is None:
            return _docker_unavailable_response()

        container = docker_client.containers.get(container_id)
        container.restart()
        return make_response({"message": "Container reset successfully"}, 200)
    except docker.errors.NotFound:
        return make_response({"error": "Container not found"}, 404)
