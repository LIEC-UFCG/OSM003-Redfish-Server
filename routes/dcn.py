from flask import Blueprint
from extensions import conditional_limit
from auth import requires_authentication, requires_privilege
import distributedcontrolnode
from config import RATE_LIMIT

dcn_bp = Blueprint(
    "dcn", __name__, url_prefix="/redfish/v1/DistributedControlNode"
)

# Route to retrieve DCN information
@dcn_bp.route('', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("ComputerSystem")
def distributed_control_node_endpoint():
    """Route to retrieve DCN information using GET method. As an O-PAS node type, can be "DCN" or other.
    
    Returns:
        JSON with information about the DCN.
    """
    return distributedcontrolnode.get_dcn()