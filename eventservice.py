import readings
from flask import request, jsonify
from datetime import datetime
import logservice


def submit_test_event():
    """
    Simulates sending a test event to the EventService.

    Reads request data, validates mandatory fields, generates a test event with a unique ID,
    adds event to log and returns the created event.

    Returns:
        flask.Response: JSON response with created event and status 201 on success,
                        or error message and status 400/500 on failure.
    """
    try:
        # Gets request data
        data = request.get_json()

        # Required fields
        required_fields = ["Message", "MessageId", "OriginOfCondition"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Generate unique ID based on timestamp
        event_id = str(int(datetime.utcnow().timestamp() * 1000))

        test_event = {
            "@odata.type": "#Event.v1_8_0.Event",
            "@odata.id": f"/redfish/v1/EventService/TestEvents/{event_id}",
            "EventId": event_id,
            "EventTimestamp": datetime.utcnow().isoformat() + "Z",
            "Severity": data.get("Severity", "Critical"),
            "Message": data["Message"],
            "MessageId": data["MessageId"],
            "MessageArgs": data.get("MessageArgs", []),
            "OriginOfCondition": {
                "@odata.id": data["OriginOfCondition"]
            }
        }

        # Add event to log
        logservice.add_log_entry(
            system_id="EventService",
            logservice_id="TestLog",
            entry_type="Event",
            severity=test_event["Severity"],
            message=test_event["Message"],
            message_id=test_event["MessageId"]
        )

        return jsonify(test_event), 201  # Returns created event

    except Exception as e:
        return jsonify({"error": f"Failed to submit test event: {str(e)}"}), 500


def get_event_service():
    """
    Returns EventService information in Redfish format.

    Includes configurations such as delivery retry attempts, supported event types,
    service status and links to actions and subscriptions.

    Returns:
        dict: Dictionary with EventService data in Redfish standard.
    """
    event_service = {
        "@odata.context": "/redfish/v1/$metadata#EventService.EventService",
        "@odata.type": "#EventService.v1_10_3.EventService",
        "Id": "EventService",
        "Name": "Event Service",
        "Description": "Redfish Event Service",
        "Actions": {
            "#EventService.SubmitTestEvent": {
                "target": "/redfish/v1/EventService/Actions/EventService.SubmitTestEvent",
                #"@Redfish.ActionInfo": "/redfish/v1/EventService/SubmitTestEventActionInfo"
            }
        },
        "DeliveryRetryAttempts": readings.get_delivery_retry_attempts(),             # Read and write
        "DeliveryRetryIntervalSeconds": readings.get_delivery_retry_interval_seconds(),     # Read and write
        "RegistryPrefixes": [
            "Base"
        ],
        "ResourceTypes": [
            "ComputerSystem",
            "Manager",
            "Chassis"
        ],
        "Oem": {
            "OSM003": {
                "@odata.type": "#Resource.OemObject",
                "EventTypesForSubscription": [
                    "StatusChange",
                    "ResourceUpdated",
                    "ResourceAdded",
                    "ResourceRemoved",
                    "Alert"
                ]
            }
        },
        "ServiceEnabled": readings.get_service_enabled(),                 # Read and write
        "Status": {
            "Health": "OK",
            "State": "Enabled"
        },
        "Subscriptions": {
            "@odata.id": "/redfish/v1/EventService/Subscriptions"
        },
        "@odata.id": "/redfish/v1/EventService"
    }
    return event_service


'''
# Simula um evento de teste e armazena no LogService do sistema
def submit_test_event():
    event = add_log_entry(
        entry_type="Event",
        severity="Critical",
        message="Fan 2 crossed Lower Fatal Threshold; fans are no longer redundant",
        message_id="Event.1.0.FanWayTooSlow"
    )
    return jsonify(event), 200
'''
