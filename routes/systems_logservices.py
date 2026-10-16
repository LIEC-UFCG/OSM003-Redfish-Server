import json
import os
from flask import Blueprint, request, jsonify

from extensions import conditional_limit
from auth import requires_authentication, requires_privilege, get_authenticated_username
from config import RATE_LIMIT
from logservice import add_audit_log_entry
from logservice import AUDIT_LOG_FILE, AUTH_LOG_FILE, EVENT_LOG_FILE, ERROR_LOG_FILE
import logservice

systems_logservices_bp = Blueprint(
    "systems_logservices", __name__, url_prefix="/redfish/v1/Systems"
)

def load_log_file(log_file):
    import json
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
                if isinstance(logs, list):
                    return logs
        except Exception:
            pass
    return []

def normalize_log_entry_type(entry_type):
    """Maps custom/internal entry types to Redfish-allowed LogEntry values."""
    allowed_types = {"Event", "SEL", "Oem", "CXL"}
    normalized = str(entry_type) if entry_type is not None else "Event"
    if normalized in allowed_types:
        return normalized
    return "Event"

def format_log_entry_object(log, system_id, log_type):
    """
    Converts a log dictionary to a complete LogEntry object.
    
    Args:
        log (dict): Log dictionary from JSON file
        system_id (str): System ID
        log_type (str): Type of log service (AuditLog, AuthLog, EventLog, ErrorLog)
    
    Returns:
        dict: Complete LogEntry object with all required properties
    """
    event_id = log.get("EventId", "")
    username = log.get("Username", log.get("UserName"))
    response = {
        "@odata.type": "#LogEntry.v1_17_0.LogEntry",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_type}/Entries/{event_id}",
        "Id": event_id,
        "Name": log.get("Name", f"Log Entry {event_id}"),
        "EntryType": normalize_log_entry_type(log.get("EntryType", "Event")),
        "Severity": log.get("Severity", "Warning"),
        "Created": log.get("Created", ""),
        "Resolved": log.get("Resolved", False),
        "Message": log.get("Message", ""),
        "MessageId": log.get("MessageId", ""),
        "MessageArgs": log.get("MessageArgs", [])
    }
    if username not in (None, ""):
        response["Username"] = username
    return response

def get_log_entry_by_eventid(log_file, system_id, log_type, event_id):
    logs = load_log_file(log_file)
    for log in logs:
        if str(log["EventId"]) == str(event_id):
            username = log.get("Username", log.get("UserName"))
            response = {
                "@odata.type": "#LogEntry.v1_17_0.LogEntry",
                "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_type}/Entries/{event_id}",
                "Id": log["EventId"],
                "Name": log["Name"],
                "EntryType": normalize_log_entry_type(log.get("EntryType", "Event")),
                "Severity": log["Severity"],
                "Created": log["Created"],
                "Resolved": log["Resolved"],
                "Message": log["Message"],
                "MessageId": log["MessageId"],
                "MessageArgs": log["MessageArgs"]
            }
            if username not in (None, ""):
                response["Username"] = username
            return jsonify(response), 200
    return jsonify({"error": "Log entry not found"}), 404

# Allow retrieving system log information
@systems_logservices_bp.route('/<system_id>/LogServices', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogServiceCollection")
def log_services_collection(system_id):
    """Allow retrieving system log information.
    
    Args:
        system_id: System UUID.
    Returns:
        Collection of log services available for a specific system.
    """
    return logservice.get_log_services_collection(system_id)


# Allow retrieving detailed information about a specific log
@systems_logservices_bp.route('/<system_id>/LogServices/<log_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogService")
def log_service_detail(system_id, log_id):
    """Allow retrieving detailed information about a specific log.
    
    Args:
        system_id: System UUID.
        log_id: Unique log ID to be detailed.
    Returns:
        A specific log service.
    """
    return logservice.get_log_service_detail(system_id, log_id)

# Allow retrieving log entry information for a specific log
@systems_logservices_bp.route('/<system_id>/LogServices/Log1/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def log_entries(system_id):
    """Allow retrieving log entry information for a specific log.
    
    Args:
        system_id: System UUID.
    Returns:
        Collection of Log Entries for a specific Log.
    """
    return logservice.get_log_entries(system_id, "Log1")


# Allow retrieving detailed information about a specific log entry
@systems_logservices_bp.route('/<system_id>/LogServices/Log1/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def log_entry_detail(system_id, event_id):
    """Allow retrieving detailed information about a specific log entry.
    
    Args:
        system_id: System UUID.
        event_id: Unique event ID.
    Returns:
        A specific LogEntry.
    """
    return logservice.get_log_entry_by_id(system_id, "Log1", event_id)


# Allow creating a new log entry in a specific log
@systems_logservices_bp.route('/<system_id>/LogServices/<logservice_id>/Entries', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Rate limit: 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def create_log_entry(system_id, logservice_id):
    """Allow creating a new log entry in a specific log. Allows POST method.
    
    Creates a new LogEntry in the LogService.
    
    Args:
        system_id: System UUID.
        logservice_id: Unique ID for logservice.
    Returns:
        Adds a new LogEntry.
    """
    try:
        data = request.get_json()
        username = data.get("UserName")

        required_fields = ["EntryType", "Severity", "Message", "MessageId"] # Required fields
        # Verify if required fields are present
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Create new log entry
        new_entry = logservice.add_log_entry( 
            system_id=system_id,
            logservice_id=logservice_id,
            entry_type=data["EntryType"],
            severity=data["Severity"],
            message=data["Message"],
            message_id=data["MessageId"],
            user_name=username
        )

        return jsonify(new_entry), 201

    except Exception as e:
        return jsonify({"error": f"Failed to create log entry: {str(e)}"}), 500

@systems_logservices_bp.route('/<system_id>/LogServices/AuditLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def audit_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "AuditLog")

#---


@systems_logservices_bp.route('/<system_id>/LogServices/AuthLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def auth_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "AuthLog")

@systems_logservices_bp.route('/<system_id>/LogServices/EventLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def event_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "EventLog")

@systems_logservices_bp.route('/<system_id>/LogServices/ErrorLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def error_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "ErrorLog")


@systems_logservices_bp.route('/<system_id>/LogServices/AuditLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def audit_log_entries(system_id):
    logs = load_log_file(AUDIT_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuditLog/Entries",
        "Name": "Audit Log Entries Collection",
        "Members": [format_log_entry_object(log, system_id, "AuditLog") for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@systems_logservices_bp.route('/<system_id>/LogServices/AuthLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def auth_log_entries(system_id):
    logs = load_log_file(AUTH_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuthLog/Entries",
        "Name": "Auth Log Entries Collection",
        "Members": [format_log_entry_object(log, system_id, "AuthLog") for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@systems_logservices_bp.route('/<system_id>/LogServices/EventLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def event_log_entries(system_id):
    logs = load_log_file(EVENT_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/EventLog/Entries",
        "Name": "Event Log Entries Collection",
        "Members": [format_log_entry_object(log, system_id, "EventLog") for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@systems_logservices_bp.route('/<system_id>/LogServices/ErrorLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntryCollection")
def error_log_entries(system_id):
    logs = load_log_file(ERROR_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/ErrorLog/Entries",
        "Name": "Error Log Entries Collection",
        "Members": [format_log_entry_object(log, system_id, "ErrorLog") for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)


@systems_logservices_bp.route('/<system_id>/LogServices/AuditLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def audit_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(AUDIT_LOG_FILE, system_id, "AuditLog", event_id)

@systems_logservices_bp.route('/<system_id>/LogServices/AuthLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def auth_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(AUTH_LOG_FILE, system_id, "AuthLog", event_id)

@systems_logservices_bp.route('/<system_id>/LogServices/EventLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def event_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(EVENT_LOG_FILE, system_id, "EventLog", event_id)

@systems_logservices_bp.route('/<system_id>/LogServices/ErrorLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogEntry")
def error_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(ERROR_LOG_FILE, system_id, "ErrorLog", event_id)

@systems_logservices_bp.route('/<system_id>/LogServices/<log_id>/Actions/LogService.ClearLog', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limits to 1 request per second
@requires_authentication
@requires_privilege("LogService")
def clear_log_action(system_id, log_id):
    log_files = {
        "AuditLog": AUDIT_LOG_FILE,
        "AuthLog": AUTH_LOG_FILE,
        "EventLog": EVENT_LOG_FILE,
        "ErrorLog": ERROR_LOG_FILE
    }
    log_file = log_files.get(log_id)
    if not log_file:
        return jsonify({"error": "Invalid log id"}), 404

    try:
        with open(log_file, "w") as f:
            f.write("[]")
        add_audit_log_entry(
            system_id=system_id,
            logservice_id=log_id,
            message=f"Log {log_id} cleared by user",
            user_name=get_authenticated_username(),
            severity="OK",
            message_id="Audit.Log.Cleared"
        )
        return '', 204
    except Exception as e:
        return jsonify({"error": f"Failed to clear log: {str(e)}"}), 500
