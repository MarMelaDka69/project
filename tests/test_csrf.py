def test_csrf_token(client):
    response = client.get("/auth/csrf")

    assert response.status_code == 200
    assert "csrf_token" in response.json()


def test_register_without_csrf(client):
    response = client.post(
        "/auth/register",
        headers={"X-CSRF-Token": ""},
        json={
            "username": "csrfuser",
            "email": "csrf@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 403


def test_register_with_invalid_csrf(client):
    response = client.post(
        "/auth/register",
        headers={"X-CSRF-Token": "invalid-token"},
        json={
            "username": "csrfuser",
            "email": "csrf@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 403


def test_register_with_valid_csrf(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "csrfuser",
            "email": "csrf@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 201