from flask import Blueprint, Response, jsonify, request
import json

from auth import requires_authentication, requires_privilege
from config import RATE_LIMIT
from extensions import conditional_limit
import eventdestination
import eventservice
import readings

eventservice_bp = Blueprint(
    "eventservice", __name__, url_prefix="/redfish/v1/EventService"
)

# Allows retrieving and updating event service information
@eventservice_bp.route('', methods=['GET', 'PATCH'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EventService")
def event_service():
    """Allows retrieving and updating event service information.
    
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

# Allows retrieving and creating event subscriptions
@eventservice_bp.route('/Subscriptions', methods=['GET', 'POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EventDestinationCollection")
def event_subscriptions_collection():
    """Allows retrieving and creating event subscriptions.
    
    Returns:
        GET: All event subscriptions.
        POST: Creates a new event subscription.
    """
    if request.method == 'GET':
        return eventdestination.get_event_subscriptions()
    elif request.method == 'POST':
        return eventdestination.create_event_subscription()

# Allows retrieving and deleting event subscriptions
@eventservice_bp.route('/Subscriptions/<subscription_id>', methods=['GET', 'DELETE'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EventDestination")
def event_subscription_detail(subscription_id):
    """Allows retrieving and deleting a specific event subscription.
    
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

# Allows submitting a test event
@eventservice_bp.route('/Actions/EventService.SubmitTestEvent', methods=['POST'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("EventService")
def submit_test_event():
    """Allows submitting a test event to the event service.
    
    Returns:
        Result of test event submission.
    """
    return eventservice.submit_test_event()
