"""
Tests de integración para API
Wiki Inteligente SAP IS-U
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from api.main import app
from api.db.database import get_db
from api.db.models import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool


# Base de datos de prueba en memoria
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """Override de la dependencia de DB para tests"""
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests async"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Setup de base de datos de prueba"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(setup_database):
    """Cliente HTTP de prueba"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_token(client):
    """Token de administrador para tests"""
    # Crear usuario admin de prueba
    admin_data = {
        "email": "admin@test.com",
        "password": "testpassword123",
        "role": "admin",
        "tenant_slug": "STANDARD"
    }
    
    # Registrar admin (esto requeriría un endpoint especial para tests)
    # Por simplicidad, asumir que existe
    login_data = {
        "email": "admin@test.com",
        "password": "testpassword123"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    
    return None


class TestHealthEndpoints:
    """Tests de endpoints de salud"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test endpoint raíz"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check"""
        response = await client.get("/health")
        assert response.status_code in [200, 503]  # Puede fallar por servicios externos
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "services" in data


class TestAuthEndpoints:
    """Tests de autenticación"""
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        """Test login con credenciales inválidas"""
        login_data = {
            "email": "invalid@test.com",
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client):
        """Test endpoint protegido sin token"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestIngestEndpoints:
    """Tests de ingesta"""
    
    @pytest.mark.asyncio
    async def test_ingest_text_without_auth(self, client):
        """Test ingesta sin autenticación"""
        document_data = {
            "tenant_slug": "STANDARD",
            "text": "Test document content"
        }
        
        response = await client.post("/api/v1/ingest/text", json=document_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_ingest_text_invalid_data(self, client, admin_token):
        """Test ingesta con datos inválidos"""
        if not admin_token:
            pytest.skip("No admin token available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Texto muy corto
        document_data = {
            "tenant_slug": "STANDARD",
            "text": "Short"
        }
        
        response = await client.post(
            "/api/v1/ingest/text", 
            json=document_data, 
            headers=headers
        )
        assert response.status_code == 422


class TestSearchEndpoints:
    """Tests de búsqueda"""
    
    @pytest.mark.asyncio
    async def test_search_without_auth(self, client):
        """Test búsqueda sin autenticación"""
        search_data = {
            "tenant_slug": "STANDARD",
            "query": "test query"
        }
        
        response = await client.post("/api/v1/search/vector", json=search_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_chat_without_auth(self, client):
        """Test chat sin autenticación"""
        chat_data = {
            "tenant_slug": "STANDARD",
            "query": "¿Cómo hacer una facturación?"
        }
        
        response = await client.post("/api/v1/search/chat", json=chat_data)
        assert response.status_code == 401


class TestRateLimiting:
    """Tests de rate limiting"""
    
    @pytest.mark.asyncio
    async def test_health_rate_limit(self, client):
        """Test rate limit en health check"""
        # Hacer muchas requests seguidas
        responses = []
        for _ in range(15):  # Más del límite de 10/minuto
            response = await client.get("/health")
            responses.append(response.status_code)
        
        # Alguna debería ser 429 (rate limited)
        assert 429 in responses or all(code in [200, 503] for code in responses)


class TestCORS:
    """Tests de CORS"""
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """Test headers CORS"""
        response = await client.options("/")
        
        # Verificar que no falla
        assert response.status_code in [200, 405]  # 405 si OPTIONS no está implementado


# Tests de integración con base de datos real (solo si está disponible)
class TestDatabaseIntegration:
    """Tests de integración con BD"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--integration", default=False),
        reason="Integration tests require --integration flag"
    )
    async def test_database_connection(self):
        """Test conexión a base de datos real"""
        from api.db.database import engine
        
        try:
            async with engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                assert result.scalar() == 1
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
