
import json
from pathlib import Path

from app.main import app


CONTRACT_PATH = (
    Path(__file__).resolve().parent.parent
    / "contracts"
    / "openapi.json"
)


def test_openapi_contract_unchanged():
    expected = json.loads(
        CONTRACT_PATH.read_text(encoding="utf-8")
    )

    actual = app.openapi()

    assert actual == expected, (
        "API contract changed. "
        "Review the changes before updating openapi.json"
    )


def test_models_response_contract(client):
    response = client.post(
        "/models",
        json={
            "title": "Test",
            "description": "Contract",
            "format": "BLEND",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert set(data.keys()) == {
        "id",
        "title",
        "description",
        "format",
        "file_path",
        "image_path",
    }

    assert isinstance(data["id"], int)
    assert isinstance(data["title"], str)
    assert isinstance(data["description"], str)
    assert isinstance(data["format"], str)
    assert data["file_path"] is None
    assert data["image_path"] is None


def test_upload_request_contract():
    schema = app.openapi()

    upload = schema["paths"]["/models/upload"]["post"]

    assert "multipart/form-data" in (
        upload["requestBody"]["content"]
    )

    assert "200" in upload["responses"]
    assert "422" in upload["responses"]


def test_model_not_found_contract(client):
    response = client.get("/models/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Model not found"
    }
