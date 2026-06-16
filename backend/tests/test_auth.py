"""End-to-end auth flow tests through the API."""


def test_register_returns_token(client, user_credentials):
    res = client.post("/api/auth/register", json=user_credentials)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_register_duplicate_email_rejected(client, user_credentials):
    assert client.post("/api/auth/register", json=user_credentials).status_code == 201
    res = client.post("/api/auth/register", json=user_credentials)
    assert res.status_code == 400
    assert res.json()["detail"] == "Email already registered"


def test_login_with_correct_credentials(client, user_credentials):
    client.post("/api/auth/register", json=user_credentials)
    res = client.post(
        "/api/auth/login",
        data={
            "username": user_credentials["email"],
            "password": user_credentials["password"],
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["access_token"]


def test_login_with_wrong_password(client, user_credentials):
    client.post("/api/auth/register", json=user_credentials)
    res = client.post(
        "/api/auth/login",
        data={"username": user_credentials["email"], "password": "nope"},
    )
    assert res.status_code == 401


def test_login_unknown_user(client):
    res = client.post(
        "/api/auth/login",
        data={"username": "ghost@example.com", "password": "whatever"},
    )
    assert res.status_code == 401


def test_me_with_valid_token(client, user_credentials, auth_token):
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert res.status_code == 200, res.text
    assert res.json()["email"] == user_credentials["email"]


def test_me_without_token_unauthorized(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_garbage_token_unauthorized(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
    assert res.status_code == 401
