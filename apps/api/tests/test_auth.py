import pytest

from app.core.security import create_access_token, decode_access_token


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123",
        "full_name": "Test User",
        "business_name": "Test Plumbing",
        "business_type": "plumber",
        "postcode": "SW1A 1AA",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "TestPass123",
        "full_name": "Dup User",
        "business_name": "Dup Plumbing",
        "business_type": "plumber",
        "postcode": "SW1A 1AA",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "TestPass123",
        "full_name": "Login User",
        "business_name": "Login Plumbing",
        "business_type": "plumber",
        "postcode": "SW1A 1AA",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "TestPass123",
    })
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    payload = decode_access_token(body["access_token"])
    assert payload.get("tid")
    assert payload.get("sub")


@pytest.mark.asyncio
async def test_tenant_endpoints_work_without_tid_claim(client):
    """Legacy access tokens without ``tid`` should resolve membership server-side."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "legacy-tid@example.com",
            "password": "TestPass123",
            "full_name": "Legacy User",
            "business_name": "Legacy Plumbing",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    user_id = decode_access_token(reg.json()["access_token"])["sub"]
    legacy = create_access_token(subject=user_id)
    assert "tid" not in decode_access_token(legacy)

    response = await client.get(
        "/api/v1/rbac/me",
        headers={"Authorization": f"Bearer {legacy}"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "owner"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    response = await client.post("/api/v1/auth/login", json={
        "email": "noone@example.com",
        "password": "WrongPass123",
    })
    assert response.status_code == 401
