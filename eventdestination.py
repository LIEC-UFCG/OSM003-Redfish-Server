import json
import os
from flask import jsonify, request, make_response

# Caminho do arquivo onde as assinaturas serão armazenadas
EVENT_SUBSCRIPTIONS_FILE = "event_subscriptions.json"

# Estrutura inicial de assinaturas de eventos
default_event_subscriptions = {}

# Carrega as assinaturas armazenadas
def load_event_subscriptions():
    """
    Carrega as assinaturas de eventos do arquivo JSON.

    Returns:
        dict: Dicionário com as assinaturas de eventos. Retorna um dicionário vazio se o arquivo não existir.
    """
    if os.path.exists(EVENT_SUBSCRIPTIONS_FILE):
        with open(EVENT_SUBSCRIPTIONS_FILE, "r") as file:
            return json.load(file)
    return default_event_subscriptions.copy()

# Salva as assinaturas de eventos
def save_event_subscriptions(subscriptions):
    """
    Salva as assinaturas de eventos no arquivo JSON.

    Args:
        subscriptions (dict): Dicionário com as assinaturas de eventos a serem salvas.
    """
    with open(EVENT_SUBSCRIPTIONS_FILE, "w") as file:
        json.dump(subscriptions, file, indent=4)

# Inicializa as assinaturas de eventos na memória
event_subscriptions = load_event_subscriptions()

# Retorna todas as assinaturas de eventos
def get_event_subscriptions():
    """
    Retorna todas as assinaturas de eventos no formato Redfish.

    Returns:
        flask.Response: Resposta JSON com a coleção de assinaturas de eventos.
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

# Retorna detalhes de uma assinatura específica
def get_event_subscription(subscription_id):
    """
    Retorna detalhes de uma assinatura de evento específica.

    Args:
        subscription_id (str): ID da assinatura de evento.

    Returns:
        flask.Response: Resposta JSON com os detalhes da assinatura ou erro 404 se não encontrada.
    """
    if subscription_id in event_subscriptions:
        return jsonify(event_subscriptions[subscription_id])
    return make_response({"error": "Subscription not found"}, 404)

# Cria uma nova assinatura de eventos
def create_event_subscription():
    """
    Cria uma nova assinatura de eventos.

    Returns:
        flask.Response: Resposta JSON com a nova assinatura criada e status 201,
                        ou erro 400 se faltar algum campo obrigatório.
    """
    data = request.json

    # Verifica se todos os campos obrigatórios estão presentes
    required_fields = ["Context", "Destination", "EventTypes", "Protocol", "SubscriptionType"]
    for field in required_fields:
        if field not in data:
            return make_response({"error": f"Missing required field: {field}"}, 400)

    new_id = str(len(event_subscriptions) + 1)
    new_subscription = {
        "@odata.context": "/redfish/v1/$metadata#EventDestination.EventDestination",
        "@odata.id": f"/redfish/v1/EventService/Subscriptions/{new_id}",
        "@odata.type": "#EventDestination.v1_15_1.EventDestination",
        "Id": new_id,
        "Name": "Event Subscription",
        "Context": data["Context"],
        "Destination": data["Destination"],
        "EventTypes": data["EventTypes"],
        "Protocol": data["Protocol"],
        "SubscriptionType": data["SubscriptionType"]
    }

    # Adiciona ao dicionário e salva no arquivo
    event_subscriptions[new_id] = new_subscription
    save_event_subscriptions(event_subscriptions)

    return jsonify(new_subscription), 201

# Deleta uma assinatura de eventos
def delete_event_subscription(subscription_id):
    """
    Deleta uma assinatura de evento específica.

    Args:
        subscription_id (str): ID da assinatura de evento a ser removida.

    Returns:
        flask.Response: Mensagem de sucesso ou erro 404 se não encontrada.
    """
    if subscription_id in event_subscriptions:
        del event_subscriptions[subscription_id]
        save_event_subscriptions(event_subscriptions)
        return make_response({"message": "Subscription deleted successfully"}, 200)

    return make_response({"error": "Subscription not found"}, 404)
