import pytest

# ── Helpers ──────────────────────────────────────────────────────────────────

def register_and_login(client, username="testuser", email="test@example.com", password="password123"):
    """Register a user and return their auth token + user_id."""
    client.post("/users/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    res = client.post("/users/login", json={"email": email, "password": password})
    data = res.json()
    return data["token"], data["user_id"]

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

# ── Auth tests ────────────────────────────────────────────────────────────────

def test_register(client):
    res = client.post("/users/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data

def test_login(client):
    client.post("/users/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123"
    })
    res = client.post("/users/login", json={
        "email": "alice@example.com",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert "user_id" in data
    assert "username" in data

def test_login_wrong_password(client):
    client.post("/users/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123"
    })
    res = client.post("/users/login", json={
        "email": "alice@example.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401

def test_get_me(client):
    token, _ = register_and_login(client)
    res = client.get("/users/me", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"

def test_get_me_no_token(client):
    res = client.get("/users/me")
    assert res.status_code == 401  # No token = unauthorized

# ── Circle tests ──────────────────────────────────────────────────────────────

def test_create_circle(client):
    token, _ = register_and_login(client)
    res = client.post("/circles", json={"name": "Test Bloc"}, headers=auth_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Test Bloc"
    assert "invite_code" in data
    assert len(data["invite_code"]) == 8

def test_creator_is_added_as_member(client):
    """Creating a bloc should automatically add the creator as a member."""
    token, user_id = register_and_login(client)
    res = client.post("/circles", json={"name": "Test Bloc"}, headers=auth_headers(token))
    circle_id = res.json()["id"]

    members_res = client.get(f"/circles/{circle_id}/members", headers=auth_headers(token))
    member_ids = [m["id"] for m in members_res.json()]
    assert user_id in member_ids

def test_join_circle(client):
    # User A creates a bloc
    token_a, _ = register_and_login(client, "userA", "a@example.com")
    circle_res = client.post("/circles", json={"name": "Test Bloc"}, headers=auth_headers(token_a))
    circle_id = circle_res.json()["id"]

    # User B joins it
    token_b, user_id_b = register_and_login(client, "userB", "b@example.com")
    res = client.post(f"/circles/{circle_id}/join", headers=auth_headers(token_b))
    assert res.status_code == 200

    # Confirm B is in the members list
    members_res = client.get(f"/circles/{circle_id}/members", headers=auth_headers(token_a))
    member_ids = [m["id"] for m in members_res.json()]
    assert user_id_b in member_ids

def test_join_circle_duplicate(client):
    """Joining a circle you're already in should return 400."""
    token, _ = register_and_login(client)
    circle_res = client.post("/circles", json={"name": "Test Bloc"}, headers=auth_headers(token))
    circle_id = circle_res.json()["id"]

    # Creator tries to join again
    res = client.post(f"/circles/{circle_id}/join", headers=auth_headers(token))
    assert res.status_code == 400

def test_join_by_invite_code(client):
    token_a, _ = register_and_login(client, "userA", "a@example.com")
    circle_res = client.post("/circles", json={"name": "Test Bloc"}, headers=auth_headers(token_a))
    invite_code = circle_res.json()["invite_code"]

    token_b, user_id_b = register_and_login(client, "userB", "b@example.com")
    res = client.post("/circles/join-by-code", json={"invite_code": invite_code}, headers=auth_headers(token_b))
    assert res.status_code == 200

def test_join_invalid_invite_code(client):
    token, _ = register_and_login(client)
    res = client.post("/circles/join-by-code", json={"invite_code": "BADCODE1"}, headers=auth_headers(token))
    assert res.status_code == 404

def test_leave_circle(client):
    token_a, _ = register_and_login(client, "userA", "a@example.com")
    circle_res = client.post("/circles", json={"name": "Test Bloc"}, headers=auth_headers(token_a))
    circle_id = circle_res.json()["id"]

    token_b, user_id_b = register_and_login(client, "userB", "b@example.com")
    client.post(f"/circles/{circle_id}/join", headers=auth_headers(token_b))

    # B leaves
    res = client.delete(f"/circles/{circle_id}/leave", headers=auth_headers(token_b))
    assert res.status_code == 200

    # Confirm B is no longer in members
    members_res = client.get(f"/circles/{circle_id}/members", headers=auth_headers(token_a))
    member_ids = [m["id"] for m in members_res.json()]
    assert user_id_b not in member_ids

def test_leave_circle_not_member(client):
    """Leaving a circle you're not in should return 404."""
    token_a, _ = register_and_login(client, "userA", "a@example.com")
    circle_res = client.post("/circles", json={"name": "Test Bloc"}, headers=auth_headers(token_a))
    circle_id = circle_res.json()["id"]

    token_b, _ = register_and_login(client, "userB", "b@example.com")
    res = client.delete(f"/circles/{circle_id}/leave", headers=auth_headers(token_b))
    assert res.status_code == 404