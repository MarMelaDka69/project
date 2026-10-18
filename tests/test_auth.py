from app import auth


def test_register(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Password123!"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "password_hash" not in data


def test_duplicate_registration(client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Password123!"
    }

    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_login_and_profile(client):
    client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "Password123!"
        }
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "Password123!"
        }
    )

    assert login.status_code == 200
    assert "session" in client.cookies

    profile = client.get("/auth/me")

    assert profile.status_code == 200
    assert profile.json()["username"] == "loginuser"


def test_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "username": "wrongpass",
            "email": "wrong@example.com",
            "password": "Password123!"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "IncorrectPassword!"
        }
    )

    assert response.status_code == 401


def test_logout(client):
    client.post(
        "/auth/register",
        json={
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "Password123!"
        }
    )

    client.post(
        "/auth/login",
        json={
            "email": "logout@example.com",
            "password": "Password123!"
        }
    )

    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert client.get("/auth/me").status_code == 401