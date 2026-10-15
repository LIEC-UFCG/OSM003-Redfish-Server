from flask import Blueprint, make_response, request

from auth import requires_authentication, requires_privilege
from config import RATE_LIMIT
from extensions import conditional_limit
import session
import sessionservice

sessionservice_bp = Blueprint(
    "sessionservice", __name__, url_prefix="/redfish/v1/SessionService"
)


@sessionservice_bp.route('', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)
@requires_authentication
@requires_privilege("SessionService")
def session_service():
    """Allow retrieving and updating session service information."""
    if request.method == 'GET':
        return sessionservice.get_session_service()
    elif request.method == 'PATCH':
        return sessionservice.update_session_service(request.json)


@sessionservice_bp.route('/Sessions', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)
def session_collection():
    """Allow retrieving and creating sessions."""
    session_service_state = sessionservice.load_session_service()

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


@sessionservice_bp.route('/Sessions/<session_id>', methods=['GET', 'DELETE'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)
@requires_authentication
@requires_privilege("Session")
def session_detail(session_id):
    """Allow retrieving and deleting a specific session."""
    session_service_state = sessionservice.load_session_service()

    if not session_service_state["ServiceEnabled"]:
        return make_response({"error": "SessionService is disabled."}, 403)

    if request.method == 'GET':
        return session.get_session(session_id)
    elif request.method == 'DELETE':
        return session.delete_session(session_id)
