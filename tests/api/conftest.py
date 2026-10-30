import pytest
from httpx import AsyncClient, ASGITransport
from api.app.main import app
from api.app.core.config import settings

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def auth_headers():
    # Genera un token válido para los tests
    from api.app.core.security import create_access_token
    token = create_access_token(data={"sub": settings.api_admin_user})
    return {"Authorization": f"Bearer {token}"}
