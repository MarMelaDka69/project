
def test_download_model(test_env):
    client = test_env["client"]

    created = client.post(
        "/models/upload",
        data={
            "title": "Download test",
            "description": "Test model",
        },
        files={
            "file": (
                "download.blend",
                b"blend file bytes",
                "application/octet-stream",
            ),
            "image": (
                "preview.png",
                b"image bytes",
                "image/png",
            ),
        },
    )

    assert created.status_code == 200
    model_id = created.json()["id"]

    response = client.get(
        f"/models/{model_id}/download"
    )

    assert response.status_code == 200
    assert response.content == b"blend file bytes"
    assert response.headers["content-type"] == (
        "application/octet-stream"
    )
    assert "download.blend" in response.headers[
        "content-disposition"
    ]


def test_download_model_not_found(client):
    response = client.get(
        "/models/999999/download"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Model not found"
    }


def test_download_without_file_path(client):
    created = client.post(
        "/models",
        json={
            "title": "No file",
            "description": "Only metadata",
            "format": "BLEND",
        },
    )

    model_id = created.json()["id"]

    response = client.get(
        f"/models/{model_id}/download"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "File path not found"
    }


def test_download_missing_file(test_env):
    client = test_env["client"]

    created = client.post(
        "/models/upload",
        data={
            "title": "Missing file",
            "description": "Test",
        },
        files={
            "file": (
                "missing.blend",
                b"file content",
                "application/octet-stream",
            ),
            "image": (
                "missing.png",
                b"image content",
                "image/png",
            ),
        },
    )

    model_id = created.json()["id"]

    (test_env["upload_dir"] / "missing.blend").unlink()

    response = client.get(
        f"/models/{model_id}/download"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "File not found"
    }
