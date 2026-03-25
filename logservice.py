import json
import os
from flask import jsonify, request, make_response
from datetime import datetime

#LOG_FILE = "log_entries.json"
HOME = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME, "redfishpi_logs")
LOG_FILE = os.path.join(LOG_DIR, "log_entries.json")
AUDIT_LOG_FILE = os.path.join(LOG_DIR, "audit_log.json")
AUTH_LOG_FILE = os.path.join(LOG_DIR, "auth_log.json")
EVENT_LOG_FILE = os.path.join(LOG_DIR, "event_log.json")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error_log.json")

LOG_SERVICE_STATUS = {"Health": "OK", "State": "Enabled"}


# Load logs from JSON file
def load_logs():
    """
    Loads logs from JSON file.

    Returns:
        list: List of dictionaries representing logs. Returns empty list if file does not exist or is corrupted.
    """
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            pass  # If error occurs, return empty list
    return []

# Save logs to JSON file
def save_logs(logs):
    """
    Saves the list of logs to JSON file.

    Args:
        logs (list): List of log dictionaries to be saved.
    """
    try:
        with open(LOG_FILE, "w") as file:
            json.dump(logs, file, indent=4)
        LOG_SERVICE_STATUS["Health"] = "OK"
    except Exception as e:
        LOG_SERVICE_STATUS["Health"] = "Critical"
        # Here you can log to syslog, send alert, etc.
        print(f"Error saving logs: {e}")

def ensure_dict(value):
    """
    Ensures the value is a dictionary.

    Args:
        value: Value to be checked.

    Returns:
        dict: The original value if it is a dictionary, or an empty dictionary otherwise.
    """
    return value if isinstance(value, dict) else {}

# Function to return the collection of LogServices available for a System
def get_log_services_collection(system_id):
    """
    Returns the collection of log services available for a specific system.

    Args:
        system_id (str): System ID.

    Returns:
        flask.Response: JSON response with the collection of log services.
    """
    log_services = {
        "@odata.type": "#LogServiceCollection.LogServiceCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices",
        "Name": "Log Service Collection",
        "Description": "Collection of system log services",
        "Members@odata.count": 4,
        "Members": [
            {"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuditLog"},
            {"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuthLog"},
            {"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/EventLog"},
            {"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/ErrorLog"}
        ]
    }
    
    return jsonify(log_services)

def get_log_service_detail(system_id, log_id):
    """
    Returns a specific log service.

    Args:
        system_id (str): System ID.
        log_id (str): ID of the log service.

    Returns:
        flask.Response: JSON response with log service details.
    """
    log_service = {
        "@odata.type": "#LogService.v1_7_0.LogService",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_id}",
        "Id": log_id,
        "Name": f"{log_id} Service",
        "Description": f"Log Service for {log_id}",
        "Entries": {
            "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_id}/Entries"
        },
        "Status": LOG_SERVICE_STATUS
    }

    return jsonify(log_service)


def get_log_service(system_id, logservice_id):
    """
    Returns a specific LogService.

    Args:
        system_id (str): System ID.
        logservice_id (str): ID of the log service.

    Returns:
        flask.Response: JSON response with LogService details.
    """
    log_service = {
        "@odata.type": "#LogService.v1_7_0.LogService",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{logservice_id}",
        "Id": logservice_id,
        "Name": f"{logservice_id} Service",
        "Description": f"Log Service for {logservice_id}",
        "Entries": {
            "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{logservice_id}/Entries"
        }
    }

    return jsonify(log_service)

# Returns the collection of LogEntry for a specific System
def get_log_entries(system_id, log_id):
    """
    Returns the collection of Log Entries for a specific log.

    Args:
        system_id (str): System ID.
        log_id (str): ID of the log service.

    Returns:
        flask.Response: JSON response with the collection of Log Entries.
    """
    logs = load_logs()
    
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_id}/Entries",
        "Name": "Log Entries Collection",
        "Members": [{"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_id}/Entries/{log['EventId']}"} for log in logs] if logs else [],
        "Members@odata.count": len(logs)
    }

    return jsonify(response)

# Returns a specific LogEntry
def get_log_entry_by_id(system_id, logservice_id, event_id):
    """
    Returns a specific LogEntry.

    Args:
        system_id (str): System ID.
        logservice_id (str): ID of the log service.
        event_id (str): Log event ID.

    Returns:
        flask.Response: JSON response with LogEntry details or 404 error if not found.
    """
    logs = load_logs()
    
    for log in logs:
        if str(log["EventId"]) == str(event_id):
            response = {
                "@odata.type": "#LogEntry.v1_17_0.LogEntry",
                "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{logservice_id}/Entries/{event_id}",
                "Id": log["EventId"],
                "Name": log["Name"],
                "EntryType": log["EntryType"],
                "Severity": log["Severity"],
                "Created": log["Created"],
                "Resolved": log["Resolved"],
                "Message": log["Message"],
                "MessageId": log["MessageId"],
                "MessageArgs": log["MessageArgs"]
            }
            return jsonify(response), 200, {"Content-Type": "application/json"}

    return make_response(jsonify({"error": "Log entry not found"}), 404)


def add_log_entry(system_id, logservice_id, entry_type, severity, message, message_id, user_name=None):
    """
    Adds a new LogEntry to the log service.

    Args:
        system_id (str): System ID.
        logservice_id (str): ID of the log service.
        entry_type (str): Type of log entry (ex: 'Event').
        severity (str): Severity of the event (ex: 'Warning').
        message (str): Event message.
        message_id (str): Message identifier.

    Returns:
        flask.Response: JSON response with the new LogEntry created and status 201.
    """
    logs = load_logs()
    new_event_id = str(int(datetime.utcnow().timestamp() * 1000))  # Generates an ID based on timestamp

    # Ensure that mandatory fields exist before saving
    if not entry_type:
        entry_type = "Event"
    if not severity:
        severity = "Warning"
    if not message:
        message = "No message provided"
    if not message_id:
        message_id = "Unknown"

    new_entry = {
        "EventId": new_event_id,
        "Id": new_event_id,  
        "Name": f"Log Entry {new_event_id}",
        "Created": datetime.utcnow().isoformat() + "Z",
        "EntryType": entry_type,
        "Severity": severity,
        "Message": message,
        "MessageId": message_id,
        "UserName": user_name,
        "Resolved": False,
        "MessageArgs": []
    }

    logs.append(new_entry)
    save_logs(logs)

    response = {
        "@odata.type": "#LogEntry.v1_17_0.LogEntry",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{logservice_id}/Entries/{new_event_id}",
        "Id": new_entry["Id"],
        "Name": new_entry["Name"],
        "EntryType": new_entry["EntryType"],
        "Severity": new_entry["Severity"],
        "Created": new_entry["Created"],
        "Resolved": new_entry["Resolved"],
        "Message": new_entry["Message"],
        "MessageId": new_entry["MessageId"],
        "UserName": new_entry["UserName"],
        "MessageArgs": new_entry["MessageArgs"]
    }

    return jsonify(response), 201, {"Content-Type": "application/json"}



#######################################################

MAX_LOG_ENTRIES = 1000

def add_audit_log_entry(system_id, logservice_id, message, user_name=None, severity="OK", message_id="Audit.Action.Success"):
    logs = []
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    new_event_id = str(int(datetime.utcnow().timestamp() * 1000))
    new_entry = {
        "EventId": new_event_id,
        "Id": new_event_id,
        "Name": f"Audit Log Entry {new_event_id}",
        "Created": datetime.utcnow().isoformat() + "Z",
        "EntryType": "Audit",
        "Severity": severity,
        "Message": message,
        "MessageId": message_id,
        "UserName": user_name,
        "Resolved": False,
        "MessageArgs": []
    }
    if len(logs) >= MAX_LOG_ENTRIES:
        logs.pop(0)
    logs.append(new_entry)
    try:
        with open(AUDIT_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)
    except Exception as e:
        LOG_SERVICE_STATUS["Health"] = "Critical"
        print(f"Error saving audit log: {e}")

# Repeat the same pattern for add_auth_log_entry, add_event_log_entry, add_error_log_entry,
# changing only EntryType, destination file and default values of MessageId/Severity.

def add_auth_log_entry(system_id, logservice_id, message, user_name=None, severity="OK", message_id="Auth.Action.Success"):
    logs = []
    if os.path.exists(AUTH_LOG_FILE):
        try:
            with open(AUTH_LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    new_event_id = str(int(datetime.utcnow().timestamp() * 1000))
    new_entry = {
        "EventId": new_event_id,
        "Id": new_event_id,
        "Name": f"Auth Log Entry {new_event_id}",
        "Created": datetime.utcnow().isoformat() + "Z",
        "EntryType": "Auth",
        "Severity": severity,
        "Message": message,
        "MessageId": message_id,
        "UserName": user_name,
        "Resolved": False,
        "MessageArgs": []
    }
    if len(logs) >= MAX_LOG_ENTRIES:
        logs.pop(0)
    logs.append(new_entry)
    try:
        with open(AUTH_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)
    except Exception as e:
        LOG_SERVICE_STATUS["Health"] = "Critical"
        print(f"Error saving auth log: {e}")

def add_event_log_entry(system_id, logservice_id, message, user_name=None, severity="OK", message_id="Event.Action.Success"):
    logs = []
    if os.path.exists(EVENT_LOG_FILE):
        try:
            with open(EVENT_LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    new_event_id = str(int(datetime.utcnow().timestamp() * 1000))
    new_entry = {
        "EventId": new_event_id,
        "Id": new_event_id,
        "Name": f"Event Log Entry {new_event_id}",
        "Created": datetime.utcnow().isoformat() + "Z",
        "EntryType": "Event",
        "Severity": severity,
        "Message": message,
        "MessageId": message_id,
        "UserName": user_name,
        "Resolved": False,
        "MessageArgs": []
    }
    if len(logs) >= MAX_LOG_ENTRIES:
        logs.pop(0)
    logs.append(new_entry)
    try:
        with open(EVENT_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)
    except Exception as e:
        LOG_SERVICE_STATUS["Health"] = "Critical"
        print(f"Error saving event log: {e}")

def add_error_log_entry(system_id, logservice_id, message, user_name=None, severity="Critical", message_id="Error.Action.Failed"):
    logs = []
    if os.path.exists(ERROR_LOG_FILE):
        try:
            with open(ERROR_LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    new_event_id = str(int(datetime.utcnow().timestamp() * 1000))
    new_entry = {
        "EventId": new_event_id,
        "Id": new_event_id,
        "Name": f"Error Log Entry {new_event_id}",
        "Created": datetime.utcnow().isoformat() + "Z",
        "EntryType": "Error",
        "Severity": severity,
        "Message": message,
        "MessageId": message_id,
        "UserName": user_name,
        "Resolved": False,
        "MessageArgs": []
    }
    if len(logs) >= MAX_LOG_ENTRIES:
        logs.pop(0)
    logs.append(new_entry)
    try:
        with open(ERROR_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)
    except Exception as e:
        LOG_SERVICE_STATUS["Health"] = "Critical"
        print(f"Error saving error log: {e}")

