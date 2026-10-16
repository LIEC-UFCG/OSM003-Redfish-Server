from flask import Blueprint, request, jsonify

from extensions import conditional_limit
from auth import requires_authentication, requires_privilege
from config import RATE_LIMIT
import chassis
import readings

chassis_bp = Blueprint(
    "chassis", __name__, url_prefix="/redfish/v1/Chassis"
)

# Load AssetTag when starting the server
readings.load_asset_tag()

# Route for /redfish/v1/Chassis/, returns information about chassis
@chassis_bp.route('', methods=['GET'], strict_slashes=False)
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

# Route for /redfish/v1/Chassis/<machine_id> endpoint, allows GET and PATCH methods
@chassis_bp.route('/<system_id>', methods=['GET', 'PATCH'], strict_slashes=False)
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
@chassis_bp.route('/<system_id>/ThermalSubsystem', methods=['GET'], strict_slashes=False)
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
@chassis_bp.route('/<system_id>/ThermalSubsystem/ThermalMetrics', methods=['GET'], strict_slashes=False)
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
@chassis_bp.route('/<system_id>/PowerSubsystem', methods=['GET'], strict_slashes=False)
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


# Route for /redfish/v1/Chassis/<system_id>/PowerSubsystem/PowerSupplies endpoint
@chassis_bp.route('/<system_id>/PowerSubsystem/PowerSupplies', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("PowerSubsystem")
def get_chassis_id_powerSupplies(system_id):
    """Route for endpoint /redfish/v1/Chassis/<system_id>/PowerSubsystem/PowerSupplies.

    Returns power supply collection information for the chassis.

    Returns:
        flask.Response: JSON with power supply collection information.
    """
    return chassis.get_power_supplies(system_id)


# Route for /redfish/v1/Chassis/<system_id>/PowerSubsystem/PowerSupplies/<psu_id> endpoint
@chassis_bp.route('/<system_id>/PowerSubsystem/PowerSupplies/<psu_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("PowerSubsystem")
def get_chassis_id_powerSupply(system_id, psu_id):
    """Route for endpoint /redfish/v1/Chassis/<system_id>/PowerSubsystem/PowerSupplies/<psu_id>.

    Returns one power supply resource for the chassis.

    Returns:
        flask.Response: JSON with power supply data.
    """
    return chassis.get_power_supply(system_id, psu_id)

# Route for /redfish/v1/Chassis/<machine_id>/Sensors endpoint, returns sensor information
@chassis_bp.route('/<system_id>/Sensors', methods=['GET'], strict_slashes=False)
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
@chassis_bp.route('/<system_id>/Sensors/<sensor_id>', methods=['GET'], strict_slashes=False)
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