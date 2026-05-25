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
        "SubscriptionType": subscription.get("SubscriptionType", "RedfishEvent"),
        "EventTypes": subscription.get("EventTypes", ["StatusChange", "ResourceUpdated", "ResourceAdded", "ResourceRemoved", "Alert"])
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
                        or 400 error if any required field is missing or invalid.
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return make_response({"error": "Invalid JSON payload"}, 400)

    # Destination is mandatory for EventDestination creation.
    if "Destination" not in data:
        return make_response({"error": "Missing required field: Destination"}, 400)

    # Validate Protocol if provided
    valid_protocols = ["Redfish", "SNMP", "SNMPv3", "Syslog", "SMTP", "IPMI", "SSH", "WMI", "WinRM", "Kairos", "RMCP", "RMCPv2"]
    protocol = data.get("Protocol", "Redfish")
    if protocol not in valid_protocols:
        return make_response({"error": f"Invalid Protocol: {protocol}. Valid protocols are: {', '.join(valid_protocols)}"}, 400)

    new_id = str(len(event_subscriptions) + 1)
    new_subscription = {
        "@odata.context": "/redfish/v1/$metadata#EventDestination.EventDestination",
        "@odata.id": f"/redfish/v1/EventService/Subscriptions/{new_id}",
        "@odata.type": "#EventDestination.v1_15_1.EventDestination",
        "Id": new_id,
        "Name": "Event Subscription",
        "Context": data.get("Context", ""),
        "Destination": data["Destination"],
        "Protocol": protocol,
        "SubscriptionType": data.get("SubscriptionType", "RedfishEvent")
    }

    if "RegistryPrefixes" in data:
        new_subscription["RegistryPrefixes"] = data["RegistryPrefixes"]
    if "ResourceTypes" in data:
        new_subscription["ResourceTypes"] = data["ResourceTypes"]
    if "MessageIds" in data:
        new_subscription["MessageIds"] = data["MessageIds"]
    if "EventTypes" in data:
        new_subscription["EventTypes"] = data["EventTypes"]
    else:
        new_subscription["EventTypes"] = ["StatusChange", "ResourceUpdated", "ResourceAdded", "ResourceRemoved", "Alert"]

    # Adds to dictionary and saves to file
    event_subscriptions[new_id] = new_subscription
    save_event_subscriptions(event_subscriptions)

    normalized = normalize_event_subscription(new_id, new_subscription)
    response = make_response(jsonify(normalized), 201)
    response.headers["Location"] = normalized["@odata.id"]
    return response

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
