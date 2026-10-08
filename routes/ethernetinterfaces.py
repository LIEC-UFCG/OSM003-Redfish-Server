from flask import Blueprint, abort

from extensions import conditional_limit
from auth import requires_authentication, requires_privilege
from config import RATE_LIMIT
import ethernetinterfaces

ethernetinterfaces_bp = Blueprint(
    "ethernetinterfaces", __name__, url_prefix="/redfish/v1/Systems"
)


# Route to retrieve Ethernet interfaces
@ethernetinterfaces_bp.route('/<system_id>/EthernetInterfaces', methods=['GET'], strict_slashes=False) 
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
@ethernetinterfaces_bp.route('/<system_id>/EthernetInterfaces/<iface>', methods=['GET'], strict_slashes=False)
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
