"""Tests for Service Registry Client"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC

from app.core.service_registry import (
    ServiceRegistryClient,
    ServiceRegistryError,
    ServiceInfo,
    get_registry_client,
    init_service_registry,
    shutdown_service_registry,
)


class TestServiceInfo:
    """Tests for ServiceInfo model"""
    
    def test_service_info_creation(self):
        """Test creating a ServiceInfo instance"""
        info = ServiceInfo(
            name="test-service",
            host="localhost",
            port=8000,
            base_url="http://localhost:8000",
            health_endpoint="/health",
            status="healthy",
        )
        assert info.name == "test-service"
        assert info.base_url == "http://localhost:8000"
        assert info.status == "healthy"


class TestServiceRegistryClient:
    """Tests for ServiceRegistryClient"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = MagicMock()
        settings.service_registry_url = "http://localhost:3006"
        settings.service_registry_enabled = True
        settings.service_registry_timeout = 10
        settings.service_registry_heartbeat_interval = 300
        settings.service_name = "fm-service"
        settings.service_port = 8000
        settings.service_host = None
        settings.app_version = "1.0.0"
        settings.environment = "development"
        settings.billing_service_url = "http://billing:8001"
        settings.treasury_api_url = "http://treasury:8002"
        settings.auth_service_url = "http://auth:8003"
        return settings
    
    @pytest.fixture
    def client(self, mock_settings):
        """Create a client instance"""
        with patch("app.core.service_registry.settings", mock_settings):
            yield ServiceRegistryClient()
    
    @pytest.mark.asyncio
    async def test_get_service_host_auto_detect(self, client):
        """Test auto-detecting service host"""
        host = client._get_service_host()
        assert host is not None  # Should return something
    
    @pytest.mark.asyncio
    async def test_get_service_base_url(self, client):
        """Test getting service base URL"""
        url = client._get_service_base_url()
        assert url.startswith("http://")
        assert ":8000" in url
    
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Test successful registration"""
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.text = ""
        
        # Create a mock client that will be returned by the property
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False  # Needed for property check
        client._client = mock_http_client
        
        result = await client.register()
        assert result is True
        assert client._is_registered is True
    
    @pytest.mark.asyncio
    async def test_register_failure(self, client):
        """Test registration failure"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False
        client._client = mock_http_client
        
        with pytest.raises(ServiceRegistryError) as exc_info:
            await client.register()
        assert "Registration failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_register_connection_error(self, client):
        """Test registration connection error"""
        import httpx
        
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_http_client.is_closed = False
        client._client = mock_http_client
        
        with pytest.raises(ServiceRegistryError) as exc_info:
            await client.register()
        assert "Cannot connect to registry" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_deregister_success(self, client):
        """Test successful deregistration"""
        client._is_registered = True
        mock_response = AsyncMock()
        mock_response.status_code = 204
        
        mock_http_client = AsyncMock()
        mock_http_client.delete = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False
        client._client = mock_http_client
        
        result = await client.deregister()
        assert result is True
        assert client._is_registered is False
    
    @pytest.mark.asyncio
    async def test_heartbeat_success(self, client):
        """Test successful heartbeat"""
        client._is_registered = True
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False
        client._client = mock_http_client
        
        result = await client.send_heartbeat()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_heartbeat_not_registered(self, client):
        """Test heartbeat when not registered"""
        client._is_registered = False
        result = await client.send_heartbeat()
        assert result is True  # Returns True gracefully
    
    @pytest.mark.asyncio
    async def test_discover_success(self, client):
        """Test successful service discovery"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        # json() is an async method that returns the dict
        mock_response.json = AsyncMock(return_value={
            "name": "billing-service",
            "host": "billing",
            "port": 8001,
            "base_url": "http://billing:8001",
            "health_endpoint": "/health",
            "status": "healthy",
            "metadata": {},
        })
        
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False
        client._client = mock_http_client
        
        url = await client.discover("billing-service")
        assert url == "http://billing:8001"
    
    @pytest.mark.asyncio
    async def test_discover_not_found(self, client):
        """Test discovery when service not found"""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False
        client._client = mock_http_client
        
        with pytest.raises(ServiceRegistryError) as exc_info:
            await client.discover("unknown-service")
        assert "not found in registry" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_discover_caching(self, client):
        """Test that discovery caches results"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            "name": "billing-service",
            "host": "billing",
            "port": 8001,
            "base_url": "http://billing:8001",
            "health_endpoint": "/health",
            "status": "healthy",
            "metadata": {},
        })
        
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_http_client.is_closed = False
        client._client = mock_http_client
        
        # First call
        url1 = await client.discover("billing-service")
        # Second call should use cache
        url2 = await client.discover("billing-service")
        
        assert url1 == url2
        # Should only have called the registry once
        assert mock_http_client.get.call_count == 1
    
    @pytest.mark.asyncio
    async def test_discover_disabled_registry(self, client, mock_settings):
        """Test discovery when registry is disabled falls back to settings"""
        mock_settings.service_registry_enabled = False
        
        with patch("app.core.service_registry.settings", mock_settings):
            client = ServiceRegistryClient()
            url = await client.discover("billing-service")
            assert url == "http://billing:8001"
    
    @pytest.mark.asyncio
    async def test_heartbeat_task_start_stop(self, client):
        """Test starting and stopping heartbeat task"""
        client.start_heartbeat_task()
        assert client._heartbeat_task is not None
        assert not client._heartbeat_task.done()
        
        await client.stop_heartbeat_task()
        assert client._heartbeat_task is None


class TestServiceRegistryIntegration:
    """Tests for registry integration functions"""
    
    @pytest.mark.asyncio
    async def test_get_registry_client_singleton(self):
        """Test that get_registry_client returns a singleton"""
        # Clear any existing client
        import app.core.service_registry as sr_module
        sr_module._registry_client = None
        
        client1 = get_registry_client()
        client2 = get_registry_client()
        assert client1 is client2
    
    @pytest.mark.asyncio
    async def test_init_and_shutdown(self):
        """Test init and shutdown sequence"""
        import app.core.service_registry as sr_module
        sr_module._registry_client = None
        
        mock_settings = MagicMock()
        mock_settings.service_registry_url = "http://localhost:3006"
        mock_settings.service_registry_enabled = True
        mock_settings.service_registry_timeout = 10
        mock_settings.service_registry_heartbeat_interval = 300
        mock_settings.service_name = "fm-service"
        mock_settings.service_port = 8000
        mock_settings.service_host = None
        mock_settings.app_version = "1.0.0"
        mock_settings.environment = "test"
        
        with patch("app.core.service_registry.settings", mock_settings):
            # Mock the registration
            with patch.object(
                ServiceRegistryClient, "register", AsyncMock(return_value=True)
            ):
                client = await init_service_registry()
                assert client._heartbeat_task is not None
                
                await shutdown_service_registry()
                assert sr_module._registry_client is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
