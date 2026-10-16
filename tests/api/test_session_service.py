import time
import pytest
import auth
import session
import sessionservice
from main import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(
        TESTING=True,
        RATELIMIT_ENABLED=False,
    )
    return app.test_client()


@pytest.fixture
def service_state(monkeypatch):
    state = {
        "ServiceEnabled": True,
        "SessionTimeout": 600,
        "Status": {"Health": "OK", "State": "Enabled"},
    }

    monkeypatch.setattr(sessionservice, "session_service_state", state)
    monkeypatch.setattr(sessionservice, "load_session_service", lambda: state)
    monkeypatch.setattr(sessionservice, "save_session_service", lambda _: None)

    return state


@pytest.fixture
def auth_headers(monkeypatch):
    token = "test-session-token"
    session_id = "test-session-id"
    session_data = {
        "Token": token,
        "UserName": "tester",
        "RoleId": "Administrator",
        "CreatedTime": time.time(),
        "ExpirationTime": time.time() + 3600,
    }

    def load_test_sessions():
        return {session_id: session_data.copy()}

    privilege_registry = {
        "Mappings": [
            {
                "Entity": "SessionService",
                "OperationMap": {
                    "GET": [{"Privilege": ["Login"]}],
                    "PATCH": [{"Privilege": ["Login"]}],
                },
            },
            {
                "Entity": "Session",
                "OperationMap": {
                    "GET": [{"Privilege": ["Login"]}],
                    "DELETE": [{"Privilege": ["Login"]}],
                },
            },
        ]
    }

    monkeypatch.setattr(auth, "load_sessions", load_test_sessions)
    monkeypatch.setattr(auth, "save_sessions", lambda _: None)
    monkeypatch.setattr(
        auth,
        "load_accounts",
        lambda: {
            "test-account": {
                "UserName": "tester",
                "Enabled": True,
                "PasswordChangeRequired": False,
            }
        },
    )
    monkeypatch.setattr(
        auth, "load_privilege_registry", lambda: privilege_registry
    )

    # As funções de sessão consultam o módulo session, separadamente de auth.
    monkeypatch.setattr(session, "load_sessions", load_test_sessions)
    monkeypatch.setattr(session, "save_sessions", lambda _: None)

    return {"X-Auth-Token": token}


def test_get_session_service(client, service_state, auth_headers):
    response = client.get(
        "/redfish/v1/SessionService",
        base_url="https://localhost",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["@odata.id"] == "/redfish/v1/SessionService"
    assert body["ServiceEnabled"] is True
    assert body["Sessions"]["@odata.id"] == (
        "/redfish/v1/SessionService/Sessions"
    )


def test_get_session_service_requires_authentication(
    client, service_state
):
    response = client.get(
        "/redfish/v1/SessionService",
        base_url="https://localhost",
    )

    assert response.status_code == 401


def test_patch_session_service(client, service_state, auth_headers):
    response = client.patch(
        "/redfish/v1/SessionService",
        base_url="https://localhost",
        headers=auth_headers,
        json={"ServiceEnabled": False},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "message": "SessionService updated successfully."
    }
    assert service_state["ServiceEnabled"] is False


def test_patch_session_service_rejects_invalid_properties(
    client, service_state, auth_headers
):
    response = client.patch(
        "/redfish/v1/SessionService",
        base_url="https://localhost",
        headers=auth_headers,
        json={"UnknownProperty": True},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Invalid properties in request."
    }


def test_session_collection_options(client, service_state):
    response = client.options(
        "/redfish/v1/SessionService/Sessions",
        base_url="https://localhost",
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Methods"] == (
        "GET, POST, OPTIONS"
    )


def test_get_session_collection(client, service_state, monkeypatch):
    expected = {
        "@odata.id": "/redfish/v1/SessionService/Sessions",
        "Members": [],
        "Members@odata.count": 0,
    }
    monkeypatch.setattr(session, "get_sessions", lambda: expected)

    response = client.get(
        "/redfish/v1/SessionService/Sessions",
        base_url="https://localhost",
    )

    assert response.status_code == 200
    assert response.get_json() == expected


def test_create_session(client, service_state, monkeypatch):
    expected = {"Id": "new-session", "UserName": "tester"}
    monkeypatch.setattr(
        session, "create_session", lambda: (expected, 201)
    )

    response = client.post(
        "/redfish/v1/SessionService/Sessions",
        base_url="https://localhost",
        json={"UserName": "tester", "Password": "test-password"},
    )

    assert response.status_code == 201
    assert response.get_json() == expected


def test_session_collection_returns_forbidden_when_disabled(
    client, service_state
):
    service_state["ServiceEnabled"] = False

    response = client.get(
        "/redfish/v1/SessionService/Sessions",
        base_url="https://localhost",
    )

    assert response.status_code == 403
    assert response.get_json() == {
        "error": "SessionService is disabled."
    }


@pytest.mark.parametrize(
    ("method", "service_function"),
    [
        ("GET", "get_session"),
        ("DELETE", "delete_session"),
    ],
)
def test_session_detail_routes(
    client, service_state, auth_headers, monkeypatch, method, service_function
):
    expected = {"result": method}
    monkeypatch.setattr(
        session,
        service_function,
        lambda session_id: expected,
    )

    response = client.open(
        "/redfish/v1/SessionService/Sessions/test-session-id",
        method=method,
        base_url="https://localhost",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.get_json() == expected


def test_session_detail_returns_forbidden_when_service_is_disabled(
    client, service_state, auth_headers
):
    service_state["ServiceEnabled"] = False

    response = client.get(
        "/redfish/v1/SessionService/Sessions/test-session-id",
        base_url="https://localhost",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.get_json() == {
        "error": "SessionService is disabled."
    }