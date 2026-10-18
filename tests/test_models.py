
from app.models import Model


def test_models_initially_empty(client):
    response = client.get("/models")

    assert response.status_code == 200
    assert response.json() == []


def test_create_model(authenticated_client):
    payload = {
        "title": "BMW M5",
        "description": "Car model",
        "format": "BLEND",
    }

    response = authenticated_client.post("/models", json=payload)
    assert response.status_code == 200

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["id"], int)
    assert data["title"] == "BMW M5"
    assert data["description"] == "Car model"
    assert data["format"] == "BLEND"


def test_model_saved_in_database(test_env, authenticated_client):
    client = authenticated_client

    response = client.post(
        "/models",
        json={
            "title": "House",
            "description": "Small house",
            "format": "BLEND",
        },
    )

    model_id = response.json()["id"]

    with test_env["session_factory"]() as db:
        model = db.get(Model, model_id)

        assert model is not None
        assert model.title == "House"
        assert model.description == "Small house"
        assert model.format == "BLEND"


def test_get_models(authenticated_client):
    client = authenticated_client
    client.post(
        "/models",
        json={
            "title": "Robot",
            "description": "3D robot",
            "format": "BLEND",
        },
    )

    response = client.get("/models")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Robot"


def test_get_model_by_id(authenticated_client):
    client = authenticated_client
    created = client.post(
        "/models",
        json={
            "title": "Cat",
            "description": "3D cat",
            "format": "BLEND",
        },
    )

    model_id = created.json()["id"]

    response = client.get(f"/models/{model_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Cat"


def test_model_not_found(client):
    response = client.get("/models/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Model not found"
    }


def test_invalid_model_data(authenticated_client):
    client = authenticated_client
    response = client.post(
        "/models",
        json={"title": "Incomplete"},
    )

    assert response.status_code == 422

def test_create_model_requires_auth(client):
    response = client.post(
        "/models",
        json={
            "title": "Unauthorized",
            "description": "Test",
            "format": "BLEND",
        },
    )

    assert response.status_code == 401