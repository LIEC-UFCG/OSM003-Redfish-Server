import json
import os
from flask import jsonify, request, make_response

# File path where subscriptions will be stored
EVENT_SUBSCRIPTIONS_FILE = "event_subscriptions.json"

# Initial event subscriptions structure
default_event_subscriptions = {}

# Loads stored subscriptions
def load_event_subscriptions():
    """
    Loads event subscriptions from JSON file.

    Returns:
        dict: Dictionary with event subscriptions. Returns an empty dictionary if file does not exist.
    """
    if os.path.exists(EVENT_SUBSCRIPTIONS_FILE):
        with open(EVENT_SUBSCRIPTIONS_FILE, "r") as file:
            return json.load(file)
    return default_event_subscriptions.copy()

# Saves event subscriptions
def save_event_subscriptions(subscriptions):
    """
    Saves event subscriptions to JSON file.

    Args:
        subscriptions (dict): Dictionary with event subscriptions to save.
    """
    with open(EVENT_SUBSCRIPTIONS_FILE, "w") as file:
        json.dump(subscriptions, file, indent=4)

# Initializes event subscriptions in memory
event_subscriptions = load_event_subscriptions()


def normalize_event_subscription(subscription_id, subscription):
    """Returns a schema-friendly EventDestination payload while preserving legacy fields in Oem."""
    normalized = {
        "@odata.context": "/redfish/v1/$metadata#EventDestination.EventDestination",
        "@odata.id": f"/redfish/v1/EventService/Subscriptions/{subscription_id}",
        "@odata.type": "#EventDestination.v1_15_1.EventDestination",
        "Id": str(subscription_id),
        "Name": subscription.get("Name", "Event Subscription"),
        "Context": subscription.get("Context", ""),
        "Destination": subscription.get("Destination", ""),
        "Protocol": subscription.get("Protocol", "Redfish"),
        "SubscriptionType": subscription.get("SubscriptionType", "RedfishEvent")
    }

    if "RegistryPrefixes" in subscription:
        normalized["RegistryPrefixes"] = subscription.get("RegistryPrefixes", [])
    if "ResourceTypes" in subscription:
        normalized["ResourceTypes"] = subscription.get("ResourceTypes", [])
    if "MessageIds" in subscription:
        normalized["MessageIds"] = subscription.get("MessageIds", [])

    legacy_event_types = subscription.get("EventTypes")
    if legacy_event_types is not None:
        normalized["Oem"] = {
            "OSM003": {
                "EventTypes": legacy_event_types
            }
        }

    return normalized

# Returns all event subscriptions
def get_event_subscriptions():
    """
    Returns all event subscriptions in Redfish format.

    Returns:
        flask.Response: JSON response with event subscriptions collection.
    """
    response = {
        "@odata.context": "/redfish/v1/$metadata#EventDestinationCollection.EventDestinationCollection",
        "@odata.id": "/redfish/v1/EventService/Subscriptions",
        "@odata.type": "#EventDestinationCollection.EventDestinationCollection",
        "Name": "Event Subscriptions Collection",
        "Members": [{"@odata.id": f"/redfish/v1/EventService/Subscriptions/{sub_id}"} for sub_id in event_subscriptions.keys()],
        "Members@odata.count": len(event_subscriptions)
    }
    return jsonify(response)

# Returns details for a specific subscription
def get_event_subscription(subscription_id):
    """
    Returns details for a specific event subscription.

    Args:
        subscription_id (str): Event subscription ID.

    Returns:
        flask.Response: JSON response with subscription details or 404 error if not found.
    """
    if subscription_id in event_subscriptions:
        return jsonify(normalize_event_subscription(subscription_id, event_subscriptions[subscription_id]))
    return make_response({"error": "Subscription not found"}, 404)

# Creates a new event subscription
def create_event_subscription():
    """
    Creates a new event subscription.

    Returns:
        flask.Response: JSON response with the new subscription and status 201,
                        or 400 error if any required field is missing.
    """
    data = request.json

    # Checks whether all required fields are present
    required_fields = ["Context", "Destination", "Protocol", "SubscriptionType"]
    for field in required_fields:
        if field not in data:
            return make_response({"error": f"Missing required field: {field}"}, 400)

    if not any(key in data for key in ["EventTypes", "RegistryPrefixes", "ResourceTypes", "MessageIds"]):
        return make_response({"error": "At least one of EventTypes, RegistryPrefixes, ResourceTypes, or MessageIds is required"}, 400)

    new_id = str(len(event_subscriptions) + 1)
    new_subscription = {
        "@odata.context": "/redfish/v1/$metadata#EventDestination.EventDestination",
        "@odata.id": f"/redfish/v1/EventService/Subscriptions/{new_id}",
        "@odata.type": "#EventDestination.v1_15_1.EventDestination",
        "Id": new_id,
        "Name": "Event Subscription",
        "Context": data["Context"],
        "Destination": data["Destination"],
        "Protocol": data["Protocol"],
        "SubscriptionType": data["SubscriptionType"]
    }

    if "RegistryPrefixes" in data:
        new_subscription["RegistryPrefixes"] = data["RegistryPrefixes"]
    if "ResourceTypes" in data:
        new_subscription["ResourceTypes"] = data["ResourceTypes"]
    if "MessageIds" in data:
        new_subscription["MessageIds"] = data["MessageIds"]
    if "EventTypes" in data:
        new_subscription["EventTypes"] = data["EventTypes"]

    # Adds to dictionary and saves to file
    event_subscriptions[new_id] = new_subscription
    save_event_subscriptions(event_subscriptions)

    return jsonify(normalize_event_subscription(new_id, new_subscription)), 201

# Deletes an event subscription
def delete_event_subscription(subscription_id):
    """
    Deletes a specific event subscription.

    Args:
        subscription_id (str): Event subscription ID to remove.

    Returns:
        flask.Response: Success message or 404 error if not found.
    """
    if subscription_id in event_subscriptions:
        del event_subscriptions[subscription_id]
        save_event_subscriptions(event_subscriptions)
        return make_response({"message": "Subscription deleted successfully"}, 200)

    return make_response({"error": "Subscription not found"}, 404)
