# Required imports for Flask server and additional functionality
from flask import Flask, abort, jsonify, request, Response, make_response, send_from_directory, redirect
from multiprocessing import Process
import json
import readings
import redfish_root
import sessionservice
import chassis
import computersystem
import ethernetinterfaces
import accountservice
import distributedcontrolnode
import eventservice
import logservice
import manager
import operatingsystem
import session
import updateservice
import manageraccount
import roles
import eventdestination
import jsonschemas
import os
import container
from auth import requires_authentication, requires_privilege
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time
from session import load_sessions, save_sessions
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import FLASK_PORT, FLASK_IP, CERT_FILE, KEY_FILE, ENABLE_RATE_LIMIT, RATE_LIMIT
import subprocess
from gerar_certificado_dinamico import obter_ip_local, gerar_certificados, certificados_estao_atualizados, registrar_certificado_no_sistema
from flask_talisman import Talisman
from logservice import add_audit_log_entry, add_event_log_entry
from logservice import AUDIT_LOG_FILE, AUTH_LOG_FILE, EVENT_LOG_FILE, ERROR_LOG_FILE
import ssdp_control

from flask import current_app
from flask_limiter.errors import RateLimitExceeded
from flask import jsonify
import logging

RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI")

HOME = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME, "redfishpi_logs")
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR, mode=0o700, exist_ok=True)
    except Exception as e:
        print(f"Error creating logs directory: {e}")

# Initialize Flask application
app = Flask(__name__) 
Talisman(app)



# Function to get the authentication token from the request header
# If the token is not present, uses the remote address of the client
def get_token():
    """
    Retrieve authentication token from request header.

    If token is not present, use the remote client address instead.

    Returns:
        str: Authentication token or client IP address.
    """
    return request.headers.get("X-Auth-Token") or get_remote_address()




# Configure rate limiter
limiter = Limiter(
    key_func=get_token,
    app=app,
    default_limits=[],
    storage_uri=RATE_LIMIT_STORAGE_URI if RATE_LIMIT_STORAGE_URI else "memory://"
)

def conditional_limit(limit):
    def decorator(func):
        if ENABLE_RATE_LIMIT:
            return limiter.limit(limit)(func)
        return func
    return decorator

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    current_app.logger.warning("Rate limit exceeded: %s", e)
    return jsonify(error="Too many requests"), 429

# Middleware to format JSON responses with indentation

@app.after_request
def pretty_json(response):
    """Middleware to format JSON responses with indentation.
    
    This decorator formats all JSON responses with proper indentation for readability.
    Content-Type is explicitly set as application/json.
    
    Args:
        response: Flask response object for the HTTP request.
    Returns:
        response: Formatted response with indented JSON.
    """
    if (
        response.content_type == "application/json" # Check if response is JSON
        and response.get_data(as_text=True)         # Ignore empty responses
    ):
        try:
            # Format JSON with indentation
            data = json.loads(response.get_data(as_text=True))
            pretty = json.dumps(data, indent=4)
            response.set_data(pretty)
            response.headers["Content-Length"] = len(pretty)    # Update content length header
        except Exception:
            pass  # Ignore errors and keep original response
    return response

# Configure to prevent ASCII character escaping in JSON output
app.config['JSON_AS_ASCII'] = False 

# Return a welcome message
@app.route('/')
@conditional_limit(RATE_LIMIT)
def index():
    """
    Home route for Flask application.

    Display a welcome message indicating that the Redfish service is active.

    Returns:
        str: Welcome message.
    """
    return 'Bem Vindo a RedfishPi'

# Route for /redfish endpoint, returns the root path
@app.route('/redfish', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)
def redfish():
    """
    Route for /redfish endpoint.

    Returns:
        tuple: Dictionary with path to API v1 and HTTP 200 status code.
    """
    return {
        "v1": "/redfish/v1/"
    }, 200

# Route for /redfish/v1/ endpoint, returns Redfish root data
@app.route('/redfish/v1', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)
def get_redfish_root():
    """
    Root API route.

    Returns:
        flask.Response: Formatted JSON response with Redfish root data.
    """
    redfish_data = redfish_root.get_redfish_v1()
    return Response(
        json.dumps(redfish_data, indent=2, ensure_ascii=False), # Format JSON
        mimetype='application/json'                             # Define content type as JSON
    )

# Route for unsupported HTTP methods on /redfish/v1/ endpoint
@app.route('/redfish/v1', methods=['POST', 'PATCH', 'DELETE', 'FAKEMETHODFORTEST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)  
def redfish_root_unsupported_methods():
    """
    Handle unsupported HTTP methods on /redfish/v1/ endpoint.

    Returns:
        flask.Response: Error message with HTTP 405 status code.
    """
    return jsonify({"error": "Method not allowed"}), 405

# Route for /redfish/v1/$metadata, returns metadata file
@app.route('/redfish/v1/$metadata', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT) 
def metadata():
    """Route for /redfish/v1/$metadata, returns metadata file.
    
    Returns:
        tuple: XML file content and header or error message and 404 code.
    """
    try:
        with open('schemas/v1/metadata.xml', 'r') as file:
            return file.read(), 200, {'Content-Type': 'application/xml'}
    except FileNotFoundError:
        return jsonify({"error": "$metadata file not found"}), 404

# Route to serve schema files from schemas/v1 directory
@app.route('/schemas/v1/<path:filename>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)  
def serve_schemas_v1(filename):
    """
    Serve schema files from schemas/v1 directory.

    Args:
        filename (str): Name of the file to retrieve from the directory.

    Returns:
        flask.Response: Schema file or 404 error message.
    """
    try:
        return send_from_directory('schemas/v1', filename)
    except FileNotFoundError:
        return jsonify({"error": f"Schema file '{filename}' not found"}), 404

# Route to serve the application favicon
@app.route('/favicon.ico', strict_slashes=False)
@conditional_limit(RATE_LIMIT) 
def favicon():
    """
    Route to serve the application favicon.

    Returns:
        flask.Response: favicon.ico file.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

# Route for /redfish/v1/odata endpoint, returns basic OData information
@app.route('/redfish/v1/odata', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)  
def odata():
    """
    Route for /redfish/v1/odata endpoint, returns basic OData information.

    Returns:
        flask.Response: JSON with OData context and default value.
    """
    response = {
        "@odata.context": "/redfish/v1/$metadata",
        "value": []  # Minimum value, can be expanded as needed
    }
    return jsonify(response), 200

# Fetch system ID from readings module
system_id = readings.machine_id()

# Route for /redfish/v1/AccountService/ endpoint, allows GET and PATCH methods
@app.route('/redfish/v1/AccountService', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limit to 1 request per second
@requires_authentication
@requires_privilege("AccountService")
def account_service():
    """
    Route for /redfish/v1/AccountService/ endpoint.

    Allow GET to retrieve or PATCH to update AccountService information.

    Returns:
        flask.Response: 
            - GET: Returns AccountService data.
            - PATCH: Updates AccountService state and returns success or error message.
    """
    if request.method == 'GET':
        return accountservice.get_account_service()
    elif request.method == 'PATCH':
        return accountservice.update_account_service(request.json)


# Route for /redfish/v1/AccountService/Accounts endpoint, allows GET and POST methods
@app.route('/redfish/v1/AccountService/Accounts', methods=['GET', 'POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("ManagerAccountCollection")
def accounts_collection():
    """
    Route for /redfish/v1/AccountService/Accounts endpoint.

    Allow GET to retrieve account list or POST to create a new account.

    Returns:
        flask.Response:
            - GET: Returns list of accounts.
            - POST: Returns newly created account.
    """
    if request.method == 'GET':
        accounts = manageraccount.get_accounts()
        return accounts, 200
    elif request.method == 'POST':
        new_account, status_code = manageraccount.create_account()

        if status_code == 201 and "UserName" in new_account:
            add_audit_log_entry(
                system_id=system_id,
                logservice_id="Log1",
                message=f"User {new_account['UserName']} created",
                user_name=request.headers.get("X-Auth-Token", "admin"),
                severity="OK",
                message_id="Audit.User.Create"
            )
        else:
            logging.warning(f"Failed to create user: {new_account}")

        return new_account, status_code

# Route for /redfish/v1/AccountService/Accounts/<account_id> endpoint, allows GET, PATCH and DELETE methods
@app.route('/redfish/v1/AccountService/Accounts/<account_id>', methods=['GET', 'PATCH', 'DELETE'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("ManagerAccount")
def account_detail(account_id):
    """
    Route for /redfish/v1/AccountService/Accounts/<account_id> endpoint.

    Allow GET to retrieve, PATCH to update, or DELETE to remove a specific account.

    Args:
        account_id (str): Account ID.

    Returns:
        flask.Response:
            - GET: Returns account data.
            - PATCH: Updates account.
            - DELETE: Removes account.
    """
    if request.method == 'GET':
        return manageraccount.get_account(account_id)
    elif request.method == 'PATCH':
        add_audit_log_entry(
            system_id=system_id,
            logservice_id="Log1",
            message=f"User {account_id} updated",
            user_name=request.headers.get("X-Auth-Token", "admin"),
            severity="OK",
            message_id="Audit.User.Update"
        )
        return manageraccount.update_account(account_id)
    elif request.method == 'DELETE':
        add_audit_log_entry(
            system_id=system_id,
            logservice_id="Log1",
            message=f"User {account_id} deleted",
            user_name=request.headers.get("X-Auth-Token", "admin"),
            severity="OK",
            message_id="Audit.User.Delete"
        )
        return manageraccount.delete_account(account_id)

# Route for /redfish/v1/AccountService/Roles endpoint, returns available roles
@app.route('/redfish/v1/AccountService/Roles', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("RoleCollection")
def roles_collection():
    """
    Route for /redfish/v1/AccountService/Roles endpoint.

    Returns list of available roles (roles).

    Returns:
        flask.Response: List of available roles.
    """
    return roles.get_roles()

# Route for /redfish/v1/AccountService/Roles/<role_id> endpoint, returns details of specific role
@app.route('/redfish/v1/AccountService/Roles/<role_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("Role")
def role_detail(role_id):
    """
    Route for /redfish/v1/AccountService/Roles/<role_id> endpoint.

    Returns details of a specific role (role).

    Args:
        role_id (str): Role ID.

    Returns:
        flask.Response: Details of requested role.
    """
    return roles.get_role(role_id)

# Route for /redfish/v1/Chassis/, returns information about chassis
@app.route('/redfish/v1/Chassis', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limit to 1 request per second
@requires_authentication
@requires_privilege("ChassisCollection")
def get_chassis():
    """
    Route for /redfish/v1/Chassis/ endpoint.

    Returns information about all available chassis in the system.

    Returns:
        flask.Response: JSON with chassis collection in Redfish format.
    """
    return chassis.get_chassis()

# Load AssetTag when starting the server
readings.load_asset_tag()

# Route for /redfish/v1/Chassis/<machine_id> endpoint, allows GET and PATCH methods
@app.route('/redfish/v1/Chassis/<system_id>', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("Chassis")
def get_chassis_id(system_id):
    """Route for endpoint /redfish/v1/Chassis/<machine_id>.
    
    Allow GET to retrieve or PATCH to update detailed chassis information identified by machine_id.
    
    Returns:
        flask.Response:
            - GET: Returns detailed chassis information.
            - PATCH: Updates chassis AssetTag and returns success or error message.
    """
    if request.method == 'GET':
        return chassis.get_chassis_id(system_id)
    elif request.method == 'PATCH':
        data = request.get_json()
        if "AssetTag" in data:
            readings.set_asset_tag(data["AssetTag"]) # Update AssetTag
            return jsonify({
                "Message": "AssetTag updated successfully!",
                "AssetTag": data["AssetTag"]
            }), 200
        else:
            return jsonify({"Message": "AssetTag field not provided"}), 400

# Route for /redfish/v1/Chassis/<machine_id>/ThermalSubsystem endpoint, returns thermal information
@app.route('/redfish/v1/Chassis/<system_id>/ThermalSubsystem', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ThermalSubsystem")
def get_chassis_id_thermalSubsystem(system_id):
    """Route for endpoint /redfish/v1/Chassis/<machine_id>/ThermalSubsystem.
    
    Returns thermal subsystem information for the chassis.
    
    Returns:
        flask.Response: JSON with thermal subsystem information.
    """
    return chassis.get_thermalSubsystem(system_id)

# Route for /redfish/v1/Chassis/<machine_id>/ThermalSubsystem/ThermalMetrics endpoint, allows GET and PATCH methods
@app.route('/redfish/v1/Chassis/<system_id>/ThermalSubsystem/ThermalMetrics', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ThermalMetrics")
def get_chassis_id_thermalMetrics(system_id):
    """Route for endpoint /redfish/v1/Chassis/<machine_id>/ThermalSubsystem/ThermalMetrics.
    
    Returns thermal metrics for the chassis.
    
    Returns:
        flask.Response: JSON with chassis thermal metrics.
    """
    return chassis.get_thermalMetrics(system_id)

# Route for /redfish/v1/Chassis/<machine_id>/PowerSubsystem endpoint, returns power information
@app.route('/redfish/v1/Chassis/<system_id>/PowerSubsystem', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("PowerSubsystem")
def get_chassis_id_powerSubsystem(system_id):
    """Route for endpoint /redfish/v1/Chassis/<machine_id>/PowerSubsystem.
    
    Returns power subsystem information for the chassis.
    
    Returns:
        flask.Response: JSON with power subsystem information.
    """
    return chassis.get_powerSubsystem(system_id)

# Route for /redfish/v1/Chassis/<machine_id>/Sensors endpoint, returns sensor information
@app.route('/redfish/v1/Chassis/<system_id>/Sensors', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("Sensor")
def get_chassis_id_sensors(system_id):
    """Route for endpoint /redfish/v1/Chassis/<machine_id>/Sensors.
    
    Returns sensor information for the chassis.
    
    Returns:
        flask.Response: JSON with readings from chassis sensors.
    """
    return chassis.get_sensors(system_id)

# Route for /redfish/v1/Chassis/<machine_id>/Sensors/<sensor_id> endpoint, returns one sensor
@app.route('/redfish/v1/Chassis/<system_id>/Sensors/<sensor_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("Sensor")
def get_chassis_id_sensor(system_id, sensor_id):
    """Route for endpoint /redfish/v1/Chassis/<machine_id>/Sensors/<sensor_id>.

    Returns details for a single chassis sensor resource.

    Returns:
        flask.Response: JSON with sensor data.
    """
    return chassis.get_sensor(sensor_id, system_id)
#-----------------------------------------------------------------------------------------------------------------------

# Route for /redfish/v1/JsonSchemas/ endpoint
# Returns a list of JSON schemas available for the API
@app.route('/redfish/v1/JsonSchemas', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("JsonSchemaFileCollection")
def get_json_schema_file():
    """Route for /redfish/v1/JsonSchemas/ endpoint.
    
    Returns:
        return: Returns a list of JSON schemas available for the API.
    """
    return jsonschemas.get_json_schemas()

# Route for /redfish/v1/JsonSchemas/Chassis.v1_26_0 endpoint
# Returns the specific JSON schema for chassis version 1.26.0
@app.route('/redfish/v1/JsonSchemas/Chassis.v1_26_0', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("JsonSchemaFile")
def get_json_schema_chassis():
    """Route for /redfish/v1/JsonSchemas/Chassis.v1_26_0 endpoint.

    Returns:
        return: Returns the specific JSON schema for chassis version 1.26.0.
    """
    return jsonschemas.get_chassis_schemas()

# Route for /redfish/v1/Systems/ endpoint
# Returns information about available computer systems
@app.route('/redfish/v1/Systems', methods=['GET'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/Actions/ComputerSystem.Reset', methods=['POST'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>', methods=['GET'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/Processors', methods=['GET'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/Processors/CPU1', methods=['GET'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/SimpleStorage', methods=['GET'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/Storage', methods=['GET'], strict_slashes=False)
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

    for func in storage_functions: # Iterate over storage functions
        # Register each function as a Flask route
        # The function name is used to create the route, removing the 'storage_' prefix
        # The HTTP method is set to GET
        route = f"/redfish/v1/Systems/<system_id>/SimpleStorage/{func.__name__.replace('storage_', '')}"
        # Manually chain decorators
        protected_func = requires_privilege("SimpleStorage")(
                            requires_authentication(func)
                        )
        decorated_func = conditional_limit(RATE_LIMIT)(protected_func)
        app.route(route, methods=['GET'], endpoint=f"simple_storage_{func.__name__}")(decorated_func)

    for func in storage_functions:
        route = f"/redfish/v1/Systems/<system_id>/Storage/{func.__name__.replace('storage_', '')}"
        protected_func = requires_privilege("SimpleStorage")(
                            requires_authentication(func)
                        )
        decorated_func = conditional_limit(RATE_LIMIT)(protected_func)
        app.route(route, methods=['GET'], endpoint=f"storage_{func.__name__}")(decorated_func)

# Route to retrieve operating system information
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem', methods=['GET'], strict_slashes=False) 
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
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/OperatingSystemMetrics', methods=['GET', 'PATCH'], strict_slashes=False) 
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
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers', methods=['GET'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers/<container_id>', methods=['GET'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Reset', methods=['POST'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Start', methods=['POST'], strict_slashes=False)
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
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Stop', methods=['POST'], strict_slashes=False)
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

# Allow retrieving system log information
@app.route('/redfish/v1/Systems/<system_id>/LogServices', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogServiceCollection")
def log_services_collection(system_id):
    """Allow retrieving system log information.
    
    Args:
        system_id: System UUID.
    Returns:
        Collection of log services available for a specific system.
    """
    return logservice.get_log_services_collection(system_id)

# Allow retrieving detailed information about a specific log
@app.route('/redfish/v1/Systems/<system_id>/LogServices/<log_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogService")
def log_service_detail(system_id, log_id):
    """Allow retrieving detailed information about a specific log.
    
    Args:
        system_id: System UUID.
        log_id: Unique log ID to be detailed.
    Returns:
        A specific log service.
    """
    return logservice.get_log_service_detail(system_id, log_id)

# Allow retrieving log entry information for a specific log
@app.route('/redfish/v1/Systems/<system_id>/LogServices/Log1/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def log_entries(system_id):
    """Allow retrieving log entry information for a specific log.
    
    Args:
        system_id: System UUID.
    Returns:
        Collection of Log Entries for a specific Log.
    """
    return logservice.get_log_entries(system_id, "Log1")

# Allow retrieving detailed information about a specific log entry
@app.route('/redfish/v1/Systems/<system_id>/LogServices/Log1/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def log_entry_detail(system_id, event_id):
    """Allow retrieving detailed information about a specific log entry.
    
    Args:
        system_id: System UUID.
        event_id: Unique event ID.
    Returns:
        A specific LogEntry.
    """
    return logservice.get_log_entry_by_id(system_id, "Log1", event_id)

# Allow creating a new log entry in a specific log
@app.route('/redfish/v1/Systems/<system_id>/LogServices/<logservice_id>/Entries', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def create_log_entry(system_id, logservice_id):
    """Allow creating a new log entry in a specific log. Allows POST method.
    
    Creates a new LogEntry in the LogService.
    
    Args:
        system_id: System UUID.
        logservice_id: Unique ID for logservice.
    Returns:
        Adds a new LogEntry.
    """
    try:
        data = request.get_json()
        username = data.get("UserName")

        required_fields = ["EntryType", "Severity", "Message", "MessageId"] # Required fields
        # Verify if required fields are present
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Create new log entry
        new_entry = logservice.add_log_entry( 
            system_id=system_id,
            logservice_id=logservice_id,
            entry_type=data["EntryType"],
            severity=data["Severity"],
            message=data["Message"],
            message_id=data["MessageId"],
            user_name=username
        )

        return jsonify(new_entry), 201

    except Exception as e:
        return jsonify({"error": f"Failed to create log entry: {str(e)}"}), 500


def load_log_file(log_file):
    import json
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
                if isinstance(logs, list):
                    return logs
        except Exception:
            pass
    return []

def normalize_log_entry_type(entry_type):
    """Maps custom/internal entry types to Redfish-allowed LogEntry values."""
    allowed_types = {"Event", "SEL", "Oem", "CXL"}
    normalized = str(entry_type) if entry_type is not None else "Event"
    if normalized in allowed_types:
        return normalized
    return "Event"

def format_log_entry_object(log, system_id, log_type):
    """
    Converts a log dictionary to a complete LogEntry object.
    
    Args:
        log (dict): Log dictionary from JSON file
        system_id (str): System ID
        log_type (str): Type of log service (AuditLog, AuthLog, EventLog, ErrorLog)
    
    Returns:
        dict: Complete LogEntry object with all required properties
    """
    event_id = log.get("EventId", "")
    username = log.get("Username", log.get("UserName"))
    response = {
        "@odata.type": "#LogEntry.v1_17_0.LogEntry",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_type}/Entries/{event_id}",
        "Id": event_id,
        "Name": log.get("Name", f"Log Entry {event_id}"),
        "EntryType": normalize_log_entry_type(log.get("EntryType", "Event")),
        "Severity": log.get("Severity", "Warning"),
        "Created": log.get("Created", ""),
        "Resolved": log.get("Resolved", False),
        "Message": log.get("Message", ""),
        "MessageId": log.get("MessageId", ""),
        "MessageArgs": log.get("MessageArgs", [])
    }
    if username not in (None, ""):
        response["Username"] = username
    return response

def get_log_entry_by_eventid(log_file, system_id, log_type, event_id):
    logs = load_log_file(log_file)
    for log in logs:
        if str(log["EventId"]) == str(event_id):
            username = log.get("Username", log.get("UserName"))
            response = {
                "@odata.type": "#LogEntry.v1_17_0.LogEntry",
                "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_type}/Entries/{event_id}",
                "Id": log["EventId"],
                "Name": log["Name"],
                "EntryType": normalize_log_entry_type(log.get("EntryType", "Event")),
                "Severity": log["Severity"],
                "Created": log["Created"],
                "Resolved": log["Resolved"],
                "Message": log["Message"],
                "MessageId": log["MessageId"],
                "MessageArgs": log["MessageArgs"]
            }
            if username not in (None, ""):
                response["Username"] = username
            return jsonify(response), 200
    return jsonify({"error": "Log entry not found"}), 404

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuditLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def audit_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "AuditLog")

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuthLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def auth_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "AuthLog")

@app.route('/redfish/v1/Systems/<system_id>/LogServices/EventLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def event_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "EventLog")

@app.route('/redfish/v1/Systems/<system_id>/LogServices/ErrorLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def error_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "ErrorLog")


@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuditLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def audit_log_entries(system_id):
    logs = load_log_file(AUDIT_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuditLog/Entries",
        "Name": "Audit Log Entries Collection",
        "Members": [format_log_entry_object(log, system_id, "AuditLog") for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuthLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def auth_log_entries(system_id):
    logs = load_log_file(AUTH_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuthLog/Entries",
        "Name": "Auth Log Entries Collection",
        "Members": [format_log_entry_object(log, system_id, "AuthLog") for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/EventLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def event_log_entries(system_id):
    logs = load_log_file(EVENT_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/EventLog/Entries",
        "Name": "Event Log Entries Collection",
        "Members": [format_log_entry_object(log, system_id, "EventLog") for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/ErrorLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def error_log_entries(system_id):
    logs = load_log_file(ERROR_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/ErrorLog/Entries",
        "Name": "Error Log Entries Collection",
        "Members": [format_log_entry_object(log, system_id, "ErrorLog") for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuditLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def audit_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(AUDIT_LOG_FILE, system_id, "AuditLog", event_id)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuthLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def auth_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(AUTH_LOG_FILE, system_id, "AuthLog", event_id)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/EventLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def event_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(EVENT_LOG_FILE, system_id, "EventLog", event_id)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/ErrorLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def error_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(ERROR_LOG_FILE, system_id, "ErrorLog", event_id)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/<log_id>/Actions/LogService.ClearLog', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def clear_log_action(system_id, log_id):
    log_files = {
        "AuditLog": AUDIT_LOG_FILE,
        "AuthLog": AUTH_LOG_FILE,
        "EventLog": EVENT_LOG_FILE,
        "ErrorLog": ERROR_LOG_FILE
    }
    log_file = log_files.get(log_id)
    if not log_file:
        return jsonify({"error": "Invalid log id"}), 404

    try:
        with open(log_file, "w") as f:
            f.write("[]")
        add_audit_log_entry(
            system_id=system_id,
            logservice_id=log_id,
            message=f"Log {log_id} cleared by user",
            user_name=get_authenticated_username(),
            severity="OK",
            message_id="Audit.Log.Cleared"
        )
        return '', 204
    except Exception as e:
        return jsonify({"error": f"Failed to clear log: {str(e)}"}), 500


# Route to retrieve DCN information
@app.route('/redfish/v1/DistributedControlNode', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def distributed_control_node_endpoint():
    """Route to retrieve DCN information using GET method. As an O-PAS node type, can be "DCN" or other.
    
    Returns:
        JSON with information about the DCN.
    """
    return distributedcontrolnode.get_dcn()

# Route to retrieve Ethernet interfaces
@app.route('/redfish/v1/Systems/<system_id>/EthernetInterfaces', methods=['GET'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EthernetInterfaceCollection")
def get_computersystem_id_ethernetInterfaces(system_id):
    """Route to retrieve Ethernet interfaces.
    
    Returns:
        All interfaces in the EthernetInterfaces JSON.
    """
    return ethernetinterfaces.get_computersystem_id_ethernetInterfaces(system_id)

# Route to retrieve detailed information of a specific Ethernet interface
@app.route('/redfish/v1/Systems/<system_id>/EthernetInterfaces/<iface>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EthernetInterface")
def get_computersystem_id_ethernetInterfaces_iface(system_id, iface):
    """Allow retrieving detailed information of a specific Ethernet interface.
    
    Args:
        iface (str): Ethernet interface name.
    
    Returns:
        Detailed JSON of the requested Ethernet interface.
        Returns 404 if interface is not found.
    """
    funcs = ethernetinterfaces.dynamic_eth_funcs() # Get dynamic Ethernet interface functions
    # Iterate over dynamic Ethernet interface functions
    # If function name matches iface parameter, call the function
    for func in funcs:
        if func.__name__ == iface:
            return func(system_id)
    abort(404)

# Allow retrieving and updating event service information
@app.route('/redfish/v1/EventService', methods=['GET', 'PATCH'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EventService")
def event_service():
    """Allow retrieving and updating event service information.
    
    Returns:
        GET: Event service JSON.
        PATCH: Updates event service settings and returns success or error message.
    """
    if request.method == 'GET':
        return Response( # Get event service
            json.dumps(eventservice.get_event_service(), indent=2), # Format JSON
            mimetype='application/json'
        )
    elif request.method == 'PATCH': # Update event service
        # Verify if event service is enabled
        data = request.get_json()
        response = {}
        # Update event service fields according to received data
        if "DeliveryRetryAttempts" in data:
            readings.set_delivery_retry_attempts(data["DeliveryRetryAttempts"])
            response["DeliveryRetryAttempts"] = data["DeliveryRetryAttempts"]

        if "DeliveryRetryIntervalSeconds" in data:
            readings.set_delivery_retry_interval_seconds(data["DeliveryRetryIntervalSeconds"])
            response["DeliveryRetryIntervalSeconds"] = data["DeliveryRetryIntervalSeconds"]

        if "ServiceEnabled" in data:
            readings.set_service_enabled(data["ServiceEnabled"])
            response["ServiceEnabled"] = data["ServiceEnabled"]

        if response:
            return jsonify({
                "Message": "Settings updated successfully!",
                **response
            }), 200
        else:
            return jsonify({"Message": "No valid fields were provided"}), 400

# Allow retrieving and creating event subscriptions
@app.route('/redfish/v1/EventService/Subscriptions', methods=['GET', 'POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EventDestinationCollection")
def event_subscriptions_collection():
    """Allow retrieving and creating event subscriptions.
    
    Returns:
        GET: All event subscriptions.
        POST: Creates a new event subscription.
    """
    if request.method == 'GET':
        return eventdestination.get_event_subscriptions()
    elif request.method == 'POST':
        return eventdestination.create_event_subscription()

# Allow retrieving and deleting event subscriptions
@app.route('/redfish/v1/EventService/Subscriptions/<subscription_id>', methods=['GET', 'DELETE'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EventDestination")
def event_subscription_detail(subscription_id):
    """Allow retrieving and deleting a specific event subscription.
    
    Args:
        subscription_id (str): Event subscription ID.
    
    Returns:
        GET: Subscription details.
        DELETE: Deletes the subscription.
    """
    if request.method == 'GET':
        return eventdestination.get_event_subscription(subscription_id)
    elif request.method == 'DELETE':
        return eventdestination.delete_event_subscription(subscription_id)

# Allow submitting a test event
@app.route('/redfish/v1/EventService/Actions/EventService.SubmitTestEvent', methods=['POST'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EventService")
def submit_test_event():
    """Allow submitting a test event to the event service.
    
    Returns:
        Result of test event submission.
    """
    return eventservice.submit_test_event()

# Return information about available managers
@app.route('/redfish/v1/Managers', methods=['GET'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ManagerCollection")
def managers():
    """Return information about available managers.
    
    Returns:
        JSON with list of available managers.
    """
    return manager.get_managers()

# Allow retrieving and updating information of a specific manager
@app.route('/redfish/v1/Managers/<manager_id>', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("Manager")
def manager_details(manager_id):
    """Allow retrieving and updating information of a specific manager.
    
    Args:
        manager_id (str): Manager ID.
    
    Returns:
        GET: Manager details.
        PATCH: Updates manager information.
    """
    if request.method == 'GET':
        return manager.get_manager_details(manager_id)
    elif request.method == 'PATCH':
        return manager.update_manager(manager_id)

# Allow retrieving and updating network protocol information of a specific manager
@app.route('/redfish/v1/Managers/<manager_id>/NetworkProtocol', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ManagerNetworkProtocol")
def network_protocol(manager_id):
    """Allow retrieving and updating network protocol information of a specific manager.
    
    Args:
        manager_id (str): Manager ID.
    
    Returns:
        GET: Network protocol information.
        PATCH: Updates network protocol information.
    """
    if request.method == 'GET':
        return manager.get_manager_network_protocol()
    elif request.method == 'PATCH':
        return manager.update_network_protocol()

# Allow retrieving and updating session service information
@app.route('/redfish/v1/SessionService', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("SessionService")
def session_service():
    """Allow retrieving and updating session service information.
    
    Returns:
        GET: Session service information.
        PATCH: Updates session service information.
    """
    if request.method == 'GET':
        return sessionservice.get_session_service()
    elif request.method == 'PATCH':
        return sessionservice.update_session_service(request.json)

# Allow retrieving and creating sessions
@app.route('/redfish/v1/SessionService/Sessions', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
def session_collection():
    """Allow retrieving and creating sessions.
    
    Returns:
        GET: All sessions.
        POST: Creates a new session.
        OPTIONS: Responds to CORS preflight requests.
    """
    session_service_state = sessionservice.load_session_service() # Load session service state
    # Verify if session service is enabled

    # Handle CORS preflight request (OPTIONS)
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5000'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 200

    if not session_service_state["ServiceEnabled"]:
        return make_response({"error": "SessionService is disabled."}, 403)

    if request.method == 'GET':
        return session.get_sessions()
    elif request.method == 'POST':
        return session.create_session()

# Allow retrieving and deleting a specific session
@app.route('/redfish/v1/SessionService/Sessions/<session_id>', methods=['GET', 'DELETE'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("Session")
def session_detail(session_id):
    """Allow retrieving and deleting a specific session.
    
    Args:
        session_id (str): Session ID.
    
    Returns:
        GET: Session details.
        DELETE: Deletes the session.
    """
    session_service_state = sessionservice.load_session_service()

    if not session_service_state["ServiceEnabled"]:
        return make_response({"error": "SessionService is disabled."}, 403)

    if request.method == 'GET':
        return session.get_session(session_id)
    elif request.method == 'DELETE':
        return session.delete_session(session_id)

# Allow retrieving and updating update service information
@app.route('/redfish/v1/UpdateService', methods=['GET', 'PATCH'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("UpdateService")
def update_service():
    """Allow retrieving and updating update service information.
    
    Returns:
        GET: Update service information.
        PATCH: Updates update service information.
    """
    if request.method == 'GET':
        return updateservice.get_update_service()
    elif request.method == 'PATCH':
        return updateservice.update_update_service(request.json)

# Allow performing a simple firmware update
@app.route('/redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate', methods=['POST'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("UpdateService")
def update_firmware():
    """Allow performing a simple firmware update.
    
    Returns:
        Update result.
    """
    return updateservice.simple_update()

# Function to clear expired sessions
# Removes sessions whose expiration time has passed
def limpar_sessoes_expiradas():
    """Remove expired sessions from session storage.
    
    This function iterates through all saved sessions, checks if the expiration time has passed,
    and removes expired sessions. Updated sessions are saved again.
    
    Side Effects:
        Removes expired sessions from sessions file and prints removed sessions to console.
    """
    sessions = load_sessions() # Load sessions
    current_time = time.time() # Get current time
    expired = [sid for sid, sess in sessions.items() if sess["ExpirationTime"] < current_time] # Filter expired sessions
    # If there are expired sessions, remove them and save updated sessions
    if expired:
        print(f"Clearing expired sessions: {expired}")
        for sid in expired:
            del sessions[sid]
        save_sessions(sessions)

# Function to initialize Flask server
# Configures SSL certificates, starts Flask server and SSDP discovery process
def iniciar_servidor_flask():
    """Initialize Flask server with HTTPS and schedule periodic expired session cleanup.
    
    - Clears expired sessions before starting the server.
    - Schedules session cleanup every 2 minutes using APScheduler.
    - Ensures scheduler will stop when program terminates.
    - Starts Flask server with configured SSL context.
    
    Side Effects:
        Starts Flask server and background task scheduler.
    """
    # Clear expired sessions before starting the server
    limpar_sessoes_expiradas()

    # Start scheduler to continue cleaning every 2 minutes
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=limpar_sessoes_expiradas, trigger="interval", seconds=120)
    scheduler.start()

    # Ensure scheduler will stop when program terminates
    atexit.register(lambda: scheduler.shutdown())

    # Start Flask server with HTTPS
    app.run(host=FLASK_IP, port=FLASK_PORT, ssl_context=(CERT_FILE, KEY_FILE))
    

# CORS configuration to allow requests from a specific domain
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to HTTP response.
    
    Args:
        response: Flask response object.
    
    Returns:
        Response object with CORS headers added.
    """
    response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5000'  # or '*' if testing
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

def get_authenticated_username():
    """Retrieve the authenticated username from session token or Basic auth header.
    
    Attempts to get username from session token first, then falls back to Basic Authorization.
    
    Returns:
        str: Username if authenticated, 'anonymous' otherwise.
    """
    # Try to get from session token
    token = request.headers.get("X-Auth-Token")
    sessions = load_sessions()
    for sess in sessions.values():
        if sess.get("Token") == token:
            return sess.get("UserName")
    # Try to get from Basic Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        import base64
        try:
            decoded = base64.b64decode(auth_header.split()[1]).decode()
            username, _ = decoded.split(":", 1)
            return username
        except Exception:
            pass
    return "anonymous"

@app.after_request
def log_all_requests(response):
    """Log all HTTP requests to audit log.
    
    Records successful and error requests with user information to audit log.
    
    Args:
        response: Flask response object.
    
    Returns:
        Flask response object (unchanged).
    """
    try:
        username = get_authenticated_username()
        endpoint = request.path
        method = request.method
        status = response.status_code
        if status != 404:
            add_audit_log_entry(
                system_id=readings.machine_id(),
                logservice_id="Log1",
                message=f"{method} {endpoint} - Status {status}",
                user_name=username,
                severity="OK" if status < 400 else "Warning",
                message_id=f"HTTP.{method}.{status}"
            )
    except Exception:
        pass
    return response 

# Function to generate interactive SSL certificates
# Requests the user for Common Name (CN) and generates necessary certificates
def gerar_certificados_interativo():
    """Generate SSL certificates interactively by requesting Common Name (CN) from user.
    
    - Generates private key, CSR, extension file and certificate with SAN.
    - Saves generated files in current directory.
    
    Side Effects:
        Creates certificate, private key, CSR and extension files on disk.
        Prints status messages to console.
    """
    cn = input("Enter the Common Name (CN) for the certificate: ").strip()

    if not cn:
        print(" CN cannot be empty.")
        return

    # File creation
    key_file = "domain.key"
    csr_file = "domain.csr"
    ext_file = "domain.ext"
    cert_file = "domainSAN.crt"

    print(" Generating private key...")
    subprocess.run(["openssl", "genrsa", "-out", key_file, "2048"], check=True)

    print(" Generating CSR...")
    subprocess.run([
        "openssl", "req", "-new", "-key", key_file,
        "-out", csr_file,
        "-subj", f"/CN={cn}"
    ], check=True)

    print(" Creating domain.ext file with SAN...")
    with open(ext_file, "w") as f:
        f.write(f"subjectAltName=DNS:{cn}\n")

    print(" Generating certificate with SAN...")
    subprocess.run([
        "openssl", "x509", "-req", "-days", "365",
        "-in", csr_file,
        "-signkey", key_file,
        "-out", cert_file,
        "-extfile", ext_file
    ], check=True)

    print(" Certificate generated successfully:", cert_file)


#USE ssl_context = "adhoc" to test HTTPS locally without worrying about generating and configuring certificates

# Main function
# Configures SSL certificates, starts Flask server and SSDP discovery process
if __name__ == '__main__': 
    """Main initialization block for RedfishPi server.
    
    - Gets machine's local IP address.
    - Verifies if SSL certificates are up-to-date for the current IP.
      - If not, generates new certificates and registers in system.
    - Starts Flask server in a separate process using HTTPS.
    - Starts SSDP discovery process in parallel to announce service on the network.
    - Waits for Flask and SSDP processes to terminate.
    
    Side Effects:
        - Generates and registers SSL certificates if necessary.
        - Starts parallel processes for Flask server and SSDP discovery.
        - Flask server will be available on configured IP and port via HTTPS.
    """
    # Start Flask server in a separate process

    ip = obter_ip_local() # Get local IP
    if not certificados_estao_atualizados(ip):
        gerar_certificados(ip)
        if os.getenv("REGISTER_CERT_IN_SYSTEM", "false").lower() == "true":
         registrar_certificado_no_sistema()

    if readings.get_ssdp_enabled():
        ssdp_control.start_ssdp()
    else:
        print("SSDP disabled at startup by ManagerNetworkProtocol setting.")

    # Start Flask server in a separate process
    # Flask process is started with configured IP and port
    processo_flask = Process(target=iniciar_servidor_flask) 
    processo_flask.start() 

    # Wait for processes to terminate
    processo_flask.join() 


