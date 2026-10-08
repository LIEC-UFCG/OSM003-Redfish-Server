# Required imports for Flask server and additional functionality
from flask import Flask, abort, jsonify, request, Response, make_response, send_from_directory, redirect
from multiprocessing import Process
import json
import readings
import redfish_root
import sessionservice
import distributedcontrolnode
import eventservice
import logservice
import manager
import session
import updateservice
import eventdestination
import os
from auth import requires_authentication, requires_privilege, get_authenticated_username
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time
from session import load_sessions, save_sessions
from flask_limiter import Limiter
from extensions import limiter, conditional_limit
from config import FLASK_PORT, FLASK_IP, CERT_FILE, KEY_FILE, ENABLE_RATE_LIMIT, RATE_LIMIT
import subprocess
from gerar_certificado_dinamico import obter_ip_local, gerar_certificados, certificados_estao_atualizados, registrar_certificado_no_sistema
from flask_talisman import Talisman
from logservice import add_audit_log_entry
import ssdp_control

# Routes
from routes.accountservice import account_service_bp
from routes.chassis import chassis_bp
from routes.jsonschemas import jsonschemas_bp
from routes.computersystems import computersystems_bp
from routes.systems_logservices import systems_logservices_bp
from routes.ethernetinterfaces import ethernetinterfaces_bp

from flask import current_app
# TODO: onde isso é usado?
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

# Middleware to format JSON responses with indentation
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

# CORS configuration to allow requests from a specific domain
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

def create_app():
    # Initialize Flask application
    app = Flask(__name__) 

    # Configure to prevent ASCII character escaping in JSON output
    app.config['JSON_AS_ASCII'] = False 

    Talisman(app)
    limiter.init_app(app)

    app.after_request(pretty_json)
    app.after_request(add_cors_headers)
    app.after_request(log_all_requests)

    app.register_blueprint(account_service_bp)
    app.register_blueprint(chassis_bp)
    app.register_blueprint(jsonschemas_bp)
    app.register_blueprint(computersystems_bp)
    app.register_blueprint(systems_logservices_bp)
    app.register_blueprint(ethernetinterfaces_bp)
    
    return app

app = create_app()

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    current_app.logger.warning("Rate limit exceeded: %s", e)
    return jsonify(error="Too many requests"), 429

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