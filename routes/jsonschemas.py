from flask import Blueprint

from extensions import conditional_limit
from auth import requires_authentication, requires_privilege
from config import RATE_LIMIT
import jsonschemas

jsonschemas_bp = Blueprint(
    "jsonschemas", __name__, url_prefix="/redfish/v1/JsonSchemas"
)

# Route for /redfish/v1/JsonSchemas/ endpoint
# Returns a list of JSON schemas available for the API
@jsonschemas_bp.route('', methods=['GET'], strict_slashes=False)
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
@jsonschemas_bp.route('/Chassis.v1_26_0', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("JsonSchemaFile")
def get_json_schema_chassis():
    """Route for /redfish/v1/JsonSchemas/Chassis.v1_26_0 endpoint.

    Returns:
        return: Returns the specific JSON schema for chassis version 1.26.0.
    """
    return jsonschemas.get_chassis_schemas()