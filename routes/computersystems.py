import os
from flask import Blueprint, request, jsonify

from extensions import conditional_limit
from auth import requires_authentication, requires_privilege
from config import RATE_LIMIT
from logservice import add_event_log_entry
import computersystem
import operatingsystem
import container

computersystems_bp = Blueprint(
    "computersystem", __name__, url_prefix="/redfish/v1/Systems"
)

# Route for /redfish/v1/Systems/ endpoint
# Returns information about available computer systems
@computersystems_bp.route('', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystemCollection")
def get_computer():
    """Route for endpoint /redfish/v1/Systems/, allows GET method.
    
    Returns:
        Information about available computer systems.
    """
    return computersystem.get_computer()

# Route for /redfish/v1/Systems/<machine_id>/Actions/ComputerSystem.Reset endpoint
# Allow restarting the computer system identified by machine_id
@computersystems_bp.route('/<system_id>/Actions/ComputerSystem.Reset', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def reset_system(system_id):
    """Route for endpoint /redfish/v1/Systems/<machine_id>/Actions/ComputerSystem.Reset.
    
    Returns:
        Allow restarting the computer system identified by machine_id.
    """
    add_event_log_entry(
        system_id=system_id,
        logservice_id="Log1",
        message="System reset executed",
        user_name=request.headers.get("X-Auth-Token", "admin"),
        severity="OK",
        message_id="Event.System.Reset"
    )
    return computersystem.reset_computer(system_id)

# Route for /redfish/v1/Systems/<machine_id> endpoint
# Returns detailed information about the computer system identified by machine_id
@computersystems_bp.route('/<system_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def get_computer_id(system_id):
    """Route for endpoint /redfish/v1/Systems/<machine_id>.
    
    Returns:
        Detailed information about the computer system identified by machine_id.
    """
    return computersystem.get_computer_system(system_id)

# Route for /redfish/v1/Systems/<machine_id>/Processors endpoint
# Returns information about the computer system processors
@computersystems_bp.route('/<system_id>/Processors', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ProcessorCollection")
def get_systems_id_processors(system_id):
    """Route for endpoint /redfish/v1/System/<machine_id>/Processors, allows GET method.
    
    Returns:
        Information about the computer system processors.
    """
    return computersystem.get_systems_id_processors(system_id)

# Route for /redfish/v1/Systems/<machine_id>/Processors/CPU1 endpoint
# Returns detailed information about the CPU1 processor of the computer system
@computersystems_bp.route('/<system_id>/Processors/CPU1', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("Processor")
def get_systems_id_processors_cpu1(system_id):
    """Route for endpoint /redfish/v1/Systems/<machine_id>/Processors/CPU1, allows GET method.
    
    Returns:
        Detailed information about the CPU1 processor of the computer system.
    """
    return computersystem.get_systems_id_processors_cpu1(system_id)

# Route for /redfish/v1/Systems/<machine_id>/SimpleStorage
# Returns information about simple storage devices of the system
@computersystems_bp.route('/<system_id>/SimpleStorage', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("SimpleStorageCollection")
def get_systems_id_simpleStorage(system_id):
    """Route for endpoint /redfish/v1/System/<machine_id>/SimpleStorage, allows GET method.
    
    Returns:
        Information about simple storage devices of the system.
    """
    return computersystem.get_systems_id_simpleStorage(system_id)

# Route for /redfish/v1/Systems/<system_id>/Storage
# Returns information about storage devices of the system
@computersystems_bp.route('/<system_id>/Storage', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("SimpleStorageCollection")
def get_systems_id_storage(system_id):
    """Route for endpoint /redfish/v1/Systems/<system_id>/Storage, allows GET method.

    Returns:
        Information about storage devices of the system.
    """
    return computersystem.get_systems_id_storage(system_id)

if os.environ.get("SPHINX_BUILD") != "1":
    storage_functions = computersystem.dynamic_storage_funcs() # Get dynamic storage functions
    storage_resource_functions = computersystem.dynamic_storage_resource_funcs()

    for func in storage_functions: # Iterate over storage functions
        # Register each function as a Flask route
        # The function name is used to create the route, removing the 'storage_' prefix
        # The HTTP method is set to GET
        route = f"/<system_id>/SimpleStorage/{func.__name__.replace('storage_', '')}"
        # Manually chain decorators
        protected_func = requires_privilege("SimpleStorage")(
                            requires_authentication(func)
                        )
        decorated_func = conditional_limit(RATE_LIMIT)(protected_func)
        computersystems_bp.route(
          route, methods=['GET'], endpoint=f"simple_storage_{func.__name__}")(decorated_func)

    for func in storage_resource_functions:
        route = f"/<system_id>/Storage/{func.__name__.replace('storage_resource_', '')}"
        protected_func = requires_privilege("SimpleStorage")(
                            requires_authentication(func)
                        )
        decorated_func = conditional_limit(RATE_LIMIT)(protected_func)
        computersystems_bp.route(route, methods=['GET'], endpoint=f"storage_{func.__name__}")(decorated_func)


# Route to retrieve operating system information
@computersystems_bp.route('/<system_id>/OperatingSystem', methods=['GET'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def get_operating_system(system_id):
    """Route to get operating system information, allows GET method.
    
    Returns:
        JSON response matching /redfish/v1/$metadata#OperatingSystem.OperatingSystem endpoint.
    """
    return operatingsystem.get_operating_system()

# Allow retrieving and updating operating system metrics
@computersystems_bp.route('/<system_id>/OperatingSystem/OperatingSystemMetrics', methods=['GET', 'PATCH'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                     # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def operating_system_metrics(system_id):
    """Allow retrieving and updating operating system metrics. Supports GET and PATCH methods.
    
    Returns:
        GET: JSON response matching /redfish/v1/$metadata#OperatingSystemMetrics.OperatingSystemMetrics
        PATCH: Updates ServiceEnabled value across categories.
    """
    if request.method == 'GET':
        return operatingsystem.get_operating_system_metrics()
    elif request.method == 'PATCH':
        data = request.json
        return operatingsystem.update_service_enabled(data)

# Allow retrieving information about operating system containers
@computersystems_bp.route('/<system_id>/OperatingSystem/Containers', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def containers_collection(system_id):
    """Allow retrieving operating system containers information. Allows GET method.
    
    Args: 
        system_id: System UUID parameter.
    Returns:
        Collection of running containers.
    """
    return container.get_containers(system_id)

# Allow retrieving detailed information about a specific container
@computersystems_bp.route('/<system_id>/OperatingSystem/Containers/<container_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def container_detail(system_id, container_id):
    """Allow retrieving specific container details. Allows GET method.
    
    Args:
        system_id: System UUID
        container_id: ID of the container in the device
    Returns:
        Details of a specific container.
    """
    return container.get_container(system_id, container_id)

# Allow restarting a specific container
@computersystems_bp.route('/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Reset', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def reset_container(system_id, container_id):
    """Allow restarting a specific container. Allows POST method.
    
    Args:
        container_id: ID of the container in the device.
    Returns:
        Restarts a container.
    """
    return container.reset_container(container_id)

# Allow starting a specific container
@computersystems_bp.route('/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Start', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def start_container(system_id, container_id):
    """Allow starting a specific container. Allows POST method.
    
    Args:
        container_id: ID of the container in the device.
    Returns:
        Starts a container.
    """
    return container.start_container(container_id)

# Allow stopping a specific container
@computersystems_bp.route('/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Stop', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def stop_container(system_id, container_id):
    """Allow stopping a specific container. Allows POST method.
    
    Args:
        container_id: ID of the container in the device.
    Returns:
        Stops a container.
    """
    return container.stop_container(container_id)
