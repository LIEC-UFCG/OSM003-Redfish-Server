import readings
from flask import request, jsonify
from datetime import datetime
import logservice


def submit_test_event():
    """
    Simula o envio de um evento de teste para o EventService.

    Lê os dados do request, valida os campos obrigatórios, gera um evento de teste com um ID único,
    adiciona o evento ao log e retorna o evento criado.

    Returns:
        flask.Response: Resposta JSON com o evento criado e status 201 em caso de sucesso,
                        ou mensagem de erro e status 400/500 em caso de falha.
    """
    try:
        # Obtém os dados do request
        data = request.get_json()

        # Campos obrigatórios
        required_fields = ["Message", "MessageId", "OriginOfCondition"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Gerar um ID único baseado no timestamp
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

        # Adicionar o evento ao log
        logservice.add_log_entry(
            system_id="EventService",
            logservice_id="TestLog",
            entry_type="Event",
            severity=test_event["Severity"],
            message=test_event["Message"],
            message_id=test_event["MessageId"]
        )

        return jsonify(test_event), 201  # Retorna o evento criado

    except Exception as e:
        return jsonify({"error": f"Failed to submit test event: {str(e)}"}), 500


def get_event_service():
    """
    Retorna as informações do EventService no formato Redfish.

    Inclui configurações como tentativas de reentrega, tipos de eventos suportados,
    status do serviço e links para ações e assinaturas.

    Returns:
        dict: Dicionário com os dados do EventService no padrão Redfish.
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
        "DeliveryRetryAttempts": readings.get_delivery_retry_attempts(),             # Escrita e leitura
        "DeliveryRetryIntervalSeconds": readings.get_delivery_retry_interval_seconds(),     # Escrita e leitura
        "EventTypesForSubscription": [
            "StatusChange",
            "ResourceUpdated",
            "ResourceAdded",
            "ResourceRemoved",
            "Alert"
        ],
        "ServiceEnabled": readings.get_service_enabled(),                 # Escrita e leitura
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
