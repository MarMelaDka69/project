
def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_add_message(client):
    response = client.post(
        "/messages",
        json={"text": "Hello pytest"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Hello pytest",
    }


def test_get_messages(client):
    client.post(
        "/messages",
        json={"text": "First message"},
    )

    response = client.get("/messages")

    assert response.status_code == 200
    assert response.json() == {
        "text": "First message\n"
    }


def test_message_validation(client):
    response = client.post(
        "/messages",
        json={},
    )

    assert response.status_code == 422
    assert "detail" in response.json()
