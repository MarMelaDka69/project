
from app.models import Model


def test_upload_model(test_env):
    client = test_env["client"]

    response = client.post(
        "/models/upload",
        data={
            "title": "BMW",
            "description": "Test car",
        },
        files={
            "file": (
                "bmw.blend",
                b"fake blend content",
                "application/octet-stream",
            ),
            "image": (
                "bmw.png",
                b"fake image content",
                "image/png",
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "BMW"
    assert data["format"] == "BLEND"
    assert data["file_path"] == "uploads/bmw.blend"
    assert data["image_path"] == "uploads/images/bmw.png"

    model_file = test_env["upload_dir"] / "bmw.blend"
    image_file = test_env["image_dir"] / "bmw.png"

    assert model_file.exists()
    assert image_file.exists()

    assert model_file.read_bytes() == b"fake blend content"
    assert image_file.read_bytes() == b"fake image content"

    with test_env["session_factory"]() as db:
        model = db.get(Model, data["id"])

        assert model is not None
        assert model.file_path == "uploads/bmw.blend"
        assert model.image_path == "uploads/images/bmw.png"


def test_reject_wrong_model_extension(client):
    response = client.post(
        "/models/upload",
        data={
            "title": "Invalid",
            "description": "Wrong extension",
        },
        files={
            "file": (
                "model.exe",
                b"test",
                "application/octet-stream",
            ),
            "image": (
                "preview.png",
                b"test",
                "image/png",
            ),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Разрешены только файлы .blend"
    )


def test_reject_wrong_image_extension(client):
    response = client.post(
        "/models/upload",
        data={
            "title": "Invalid image",
            "description": "Test",
        },
        files={
            "file": (
                "model.blend",
                b"test",
                "application/octet-stream",
            ),
            "image": (
                "preview.exe",
                b"test",
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Разрешены изображения JPG, JPEG, PNG и WEBP"
    )


def test_upload_missing_image(client):
    response = client.post(
        "/models/upload",
        data={
            "title": "No image",
            "description": "Test",
        },
        files={
            "file": (
                "model.blend",
                b"test",
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 422
