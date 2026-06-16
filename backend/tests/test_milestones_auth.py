"""Protected-route auth gating: milestone endpoints must require a token and
scope data to the owner."""


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_list_milestones_requires_auth(client):
    assert client.get("/api/milestones").status_code == 401


def test_create_milestone_requires_auth(client):
    res = client.post("/api/milestones", json={"name": "Foundation"})
    assert res.status_code == 401


def test_create_and_list_milestone_with_token(client, auth_token):
    create = client.post(
        "/api/milestones", json={"name": "Foundation"}, headers=_auth(auth_token)
    )
    assert create.status_code in (200, 201), create.text

    listed = client.get("/api/milestones", headers=_auth(auth_token))
    assert listed.status_code == 200
    names = [m["name"] for m in listed.json()]
    assert "Foundation" in names


def test_milestones_scoped_to_owner(client):
    # User A creates a milestone.
    a = client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "password": "secret123", "full_name": "A"},
    ).json()["access_token"]
    client.post("/api/milestones", json={"name": "A's build"}, headers=_auth(a))

    # User B must not see it.
    b = client.post(
        "/api/auth/register",
        json={"email": "b@example.com", "password": "secret123", "full_name": "B"},
    ).json()["access_token"]
    listed = client.get("/api/milestones", headers=_auth(b))
    assert listed.status_code == 200
    assert listed.json() == []
