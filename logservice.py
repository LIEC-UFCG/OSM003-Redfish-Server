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


# Carregar logs do arquivo JSON
def load_logs():
    """
    Carrega os logs do arquivo JSON.

    Returns:
        list: Lista de dicionários representando os logs. Retorna lista vazia se o arquivo não existir ou estiver corrompido.
    """
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            pass  # Se houver erro, retorna uma lista vazia
    return []

# Salvar logs no arquivo JSON
def save_logs(logs):
    """
    Salva a lista de logs no arquivo JSON.

    Args:
        logs (list): Lista de dicionários de logs a serem salvos.
    """
    try:
        with open(LOG_FILE, "w") as file:
            json.dump(logs, file, indent=4)
        LOG_SERVICE_STATUS["Health"] = "OK"
    except Exception as e:
        LOG_SERVICE_STATUS["Health"] = "Critical"
        # Aqui você pode logar no syslog, enviar alerta, etc.
        print(f"Erro ao salvar logs: {e}")

def ensure_dict(value):
    """
    Garante que o valor seja um dicionário.

    Args:
        value: Valor a ser verificado.

    Returns:
        dict: O valor original se for um dicionário, ou um dicionário vazio caso contrário.
    """
    return value if isinstance(value, dict) else {}

# Função para retornar a coleção de LogServices disponíveis para um System
def get_log_services_collection(system_id):
    """
    Retorna a coleção de serviços de log disponíveis para um sistema específico.

    Args:
        system_id (str): ID do sistema.

    Returns:
        flask.Response: Resposta JSON com a coleção de serviços de log.
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
    Retorna um serviço de log específico.

    Args:
        system_id (str): ID do sistema.
        log_id (str): ID do serviço de log.

    Returns:
        flask.Response: Resposta JSON com os detalhes do serviço de log.
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
    Retorna um LogService específico.

    Args:
        system_id (str): ID do sistema.
        logservice_id (str): ID do serviço de log.

    Returns:
        flask.Response: Resposta JSON com os detalhes do LogService.
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

# Retorna a coleção de LogEntry de um System específico
def get_log_entries(system_id, log_id):
    """
    Retorna a coleção de Log Entries para um Log específico.

    Args:
        system_id (str): ID do sistema.
        log_id (str): ID do serviço de log.

    Returns:
        flask.Response: Resposta JSON com a coleção de Log Entries.
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

# Retorna um LogEntry específico
def get_log_entry_by_id(system_id, logservice_id, event_id):
    """
    Retorna um LogEntry específico.

    Args:
        system_id (str): ID do sistema.
        logservice_id (str): ID do serviço de log.
        event_id (str): ID do evento de log.

    Returns:
        flask.Response: Resposta JSON com os detalhes do LogEntry ou erro 404 se não encontrado.
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
    Adiciona um novo LogEntry ao serviço de log.

    Args:
        system_id (str): ID do sistema.
        logservice_id (str): ID do serviço de log.
        entry_type (str): Tipo da entrada de log (ex: 'Event').
        severity (str): Severidade do evento (ex: 'Warning').
        message (str): Mensagem do evento.
        message_id (str): Identificador da mensagem.

    Returns:
        flask.Response: Resposta JSON com o novo LogEntry criado e status 201.
    """
    logs = load_logs()
    new_event_id = str(int(datetime.utcnow().timestamp() * 1000))  # Gera um ID baseado no timestamp

    # Garantimos que os campos obrigatórios existam antes de salvar
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
        print(f"Erro ao salvar audit log: {e}")

# Repita o mesmo padrão para add_auth_log_entry, add_event_log_entry, add_error_log_entry,
# mudando apenas EntryType, arquivo de destino e valores padrão de MessageId/Severity.

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
        print(f"Erro ao salvar auth log: {e}")

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
        print(f"Erro ao salvar event log: {e}")

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
        print(f"Erro ao salvar error log: {e}")

