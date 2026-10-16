from flask import Blueprint, Response, current_app, jsonify, send_from_directory
from werkzeug.exceptions import NotFound
import json
import os

from config import RATE_LIMIT
from extensions import conditional_limit
import redfish_root

basic_bp = Blueprint("basic", __name__)

# Returns a welcome message
@basic_bp.route('/')
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
@basic_bp.route('/redfish', methods=['GET'], strict_slashes=False)
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
@basic_bp.route('/redfish/v1', methods=['GET'], strict_slashes=False)
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
@basic_bp.route('/redfish/v1', methods=['POST', 'PATCH', 'DELETE', 'FAKEMETHODFORTEST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)  
def redfish_root_unsupported_methods():
    """
    Handle unsupported HTTP methods on /redfish/v1/ endpoint.

    Returns:
        flask.Response: Error message with HTTP 405 status code.
    """
    return jsonify({"error": "Method not allowed"}), 405

# Route to serve the application favicon
@basic_bp.route('/favicon.ico', strict_slashes=False)
@conditional_limit(RATE_LIMIT) 
def favicon():
    """
    Route to serve the application favicon.

    Returns:
        flask.Response: favicon.ico file.
    """
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# Route for /redfish/v1/$metadata, returns metadata file
@basic_bp.route('/redfish/v1/$metadata', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT) 
def metadata():
    """Route for /redfish/v1/$metadata, returns metadata file.
    
    Returns:
        tuple: XML file content and header or error message and 404 code.
    """
    try:
        metadata_path = os.path.join(
            current_app.root_path, 'schemas', 'v1', 'metadata.xml'
        )
        with open(metadata_path, 'r') as file:
            return file.read(), 200, {'Content-Type': 'application/xml'}
    except FileNotFoundError:
        return jsonify({"error": "$metadata file not found"}), 404


# Route to serve schema files from schemas/v1 directory
@basic_bp.route('/schemas/v1/<path:filename>', methods=['GET'], strict_slashes=False)
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
        return send_from_directory(
            os.path.join(current_app.root_path, 'schemas', 'v1'),
            filename
        )
    except NotFound:
        return jsonify({"error": f"Schema file '{filename}' not found"}), 404

# Route for /redfish/v1/odata endpoint, returns basic OData information
@basic_bp.route('/redfish/v1/odata', methods=['GET'], strict_slashes=False)
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