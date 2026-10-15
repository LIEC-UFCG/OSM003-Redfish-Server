import pytest

from main import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()

def test_index_returns_welcome_message(client):
    response = client.get("/", base_url="https://localhost")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Bem Vindo a RedfishPi"

def test_redfish_returns_v1_link(client):
    response = client.get("/redfish", base_url="https://localhost")

    assert response.status_code == 200
    assert response.get_json() == {"v1": "/redfish/v1/"}

def test_redfish_service_root(client):
    response = client.get(
        "/redfish/v1",
        base_url="https://localhost",
    )

    assert response.status_code == 200
    assert response.is_json

    body = response.get_json()
    assert body["@odata.type"].startswith("#ServiceRoot.")
    assert body["AccountService"]["@odata.id"] == "/redfish/v1/AccountService"

@pytest.mark.parametrize("method", ["POST", "PATCH", "DELETE", "FAKEMETHODFORTEST"])
def test_redfish_v1_rejects_unsupported_methods(client, method):
    response = client.open(
        "/redfish/v1",
        method=method,
        base_url="https://localhost",
    )

    assert response.status_code == 405
    assert response.get_json() == {"error": "Method not allowed"}

def test_favicon_serves_icon(client, tmp_path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    favicon_content = b"test-favicon"
    (static_dir / "favicon.ico").write_bytes(favicon_content)

    client.application.root_path = str(tmp_path)

    response = client.get("/favicon.ico", base_url="https://localhost")

    assert response.status_code == 200
    assert response.mimetype == "image/vnd.microsoft.icon"
    assert response.data == favicon_content

from pathlib import Path


def test_real_metadata_returns_xml(client):
    metadata_path = (
        Path(client.application.root_path) / "schemas" / "v1" / "metadata.xml"
    )

    response = client.get(
        "/redfish/v1/$metadata",
        base_url="https://localhost",
    )

    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    assert response.get_data(as_text=True) == metadata_path.read_text(encoding="utf-8")

def test_metadata_returns_xml(client, tmp_path):
    schema_dir = tmp_path / "schemas" / "v1"
    schema_dir.mkdir(parents=True)
    xml_content = "<metadata>test</metadata>"
    (schema_dir / "metadata.xml").write_text(xml_content, encoding="utf-8")

    client.application.root_path = str(tmp_path)

    response = client.get(
        "/redfish/v1/$metadata",
        base_url="https://localhost",
    )

    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    assert response.get_data(as_text=True) == xml_content

def test_metadata_returns_404_when_file_is_missing(client, tmp_path):
    client.application.root_path = str(tmp_path)

    response = client.get(
        "/redfish/v1/$metadata",
        base_url="https://localhost",
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "$metadata file not found"}


@pytest.mark.parametrize(
    ("filename", "expected_status"),
    [
        ("Resource_v1.xml", 200),
        ("arquivo_inexistente.xml", 404),
    ],
)
def test_serve_schema_file(client, filename, expected_status):
    response = client.get(
        f"/schemas/v1/{filename}",
        base_url="https://localhost",
    )

    assert response.status_code == expected_status

    if expected_status == 200:
      schema_path = (
          Path(client.application.root_path) / "schemas" / "v1" / filename
      )
      assert response.data == schema_path.read_bytes()
    elif expected_status == 404:
      assert response.get_json() == {"error": f"Schema file '{filename}' not found"}

def test_redfish_odata(client):
    response = client.get(
        "/redfish/v1/odata",
        base_url="https://localhost",
    )

    assert response.status_code == 200
    assert response.is_json

    body = response.get_json()
    assert body["@odata.context"] == "/redfish/v1/$metadata"
    assert isinstance(body["value"], list)
