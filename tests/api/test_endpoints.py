import pytest

@pytest.mark.anyio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

@pytest.mark.anyio
async def test_login(client):
    resp = await client.post("/api/v1/auth/token", data={"username": "admin", "password": "admin_api_secret"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.anyio
async def test_ports_unauthorized(client):
    resp = await client.get("/api/v1/ports/")
    assert resp.status_code == 401

@pytest.mark.anyio
async def test_ports_authorized(client, auth_headers):
    resp = await client.get("/api/v1/ports/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
