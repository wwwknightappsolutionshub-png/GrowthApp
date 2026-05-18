import pytest


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
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    response = await client.post("/api/v1/auth/login", json={
        "email": "noone@example.com",
        "password": "WrongPass123",
    })
    assert response.status_code == 401
