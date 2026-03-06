"""
Inter-Service Communication Helper

Provides utilities for calling other services via the Service Registry.
Ensures all inter-service calls go through registry discovery.
"""
import httpx
from typing import Optional, Dict, Any, Union
from app.core.service_registry import get_registry_client, ServiceRegistryError, ServiceUnreachableError
from app.core.logging import logger
from app.core.config import settings


class InterServiceClient:
    """
    HTTP client for making calls to other services discovered via registry.
    
    Usage:
        async with InterServiceClient() as client:
            # Discover and call billing service
            response = await client.get("billing-service", "/api/v1/invoices/123")
            
            # POST with body
            response = await client.post(
                "billing-service", 
                "/api/v1/invoices",
                json={"amount": 100.00, "currency": "USD"}
            )
    
    Or using the convenience functions:
        response = await service_get("billing-service", "/api/v1/health")
        response = await service_post("billing-service", "/api/v1/invoices", json={...})
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
    ):
        """
        Initialize the inter-service client.
        
        Args:
            timeout: HTTP timeout in seconds
            headers: Additional headers to include in all requests
            auth_token: Optional Bearer token for authentication
        """
        self._timeout = timeout
        self._headers = headers or {}
        self._auth_token = auth_token
        self._client: Optional[httpx.AsyncClient] = None
        self._discovered_urls: Dict[str, str] = {}
    
    async def __aenter__(self) -> "InterServiceClient":
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            headers=self._get_default_headers(),
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for all requests"""
        headers = {
            "Content-Type": "application/json",
            "X-Source-Service": settings.service_name,
            **self._headers,
        }
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers
    
    async def _get_base_url(self, service_name: str) -> str:
        """
        Discover the base URL for a service via registry.
        
        Caches the result for the lifetime of this client instance.
        """
        if service_name not in self._discovered_urls:
            registry = get_registry_client()
            self._discovered_urls[service_name] = await registry.discover(service_name)
        return self._discovered_urls[service_name]
    
    async def _build_url(self, service_name: str, path: str) -> str:
        """Build the full URL for a service endpoint"""
        base_url = await self._get_base_url(service_name)
        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base_url}{path}"
    
    async def _log_and_check(
        self,
        method: str,
        service_name: str,
        url: str,
        response: httpx.Response,
    ) -> None:
        """Log the request and check for errors"""
        logger.debug(
            f"Inter-service call: {method} {service_name}{url} -> {response.status_code}"
        )
        
        if response.status_code >= 500:
            logger.error(
                f"Service {service_name} returned error {response.status_code}: "
                f"{response.text[:200]}"
            )
    
    async def get(
        self,
        service_name: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Make a GET request to another service.
        
        Args:
            service_name: Name of the target service (e.g., "billing-service")
            path: API path (e.g., "/api/v1/invoices/123")
            params: Query parameters
            headers: Additional headers for this request
            
        Returns:
            The HTTP response
            
        Raises:
            ServiceRegistryError: If service cannot be discovered
            httpx.HTTPError: If the request fails
        """
        url = await self._build_url(service_name, path)
        response = await self._client.get(url, params=params, headers=headers)
        await self._log_and_check("GET", service_name, url, response)
        return response
    
    async def post(
        self,
        service_name: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Make a POST request to another service.
        
        Args:
            service_name: Name of the target service
            path: API path
            json: JSON body
            data: Form data body
            headers: Additional headers
            
        Returns:
            The HTTP response
        """
        url = await self._build_url(service_name, path)
        response = await self._client.post(url, json=json, data=data, headers=headers)
        await self._log_and_check("POST", service_name, url, response)
        return response
    
    async def put(
        self,
        service_name: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make a PUT request to another service"""
        url = await self._build_url(service_name, path)
        response = await self._client.put(url, json=json, headers=headers)
        await self._log_and_check("PUT", service_name, url, response)
        return response
    
    async def patch(
        self,
        service_name: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make a PATCH request to another service"""
        url = await self._build_url(service_name, path)
        response = await self._client.patch(url, json=json, headers=headers)
        await self._log_and_check("PATCH", service_name, url, response)
        return response
    
    async def delete(
        self,
        service_name: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make a DELETE request to another service"""
        url = await self._build_url(service_name, path)
        response = await self._client.delete(url, headers=headers)
        await self._log_and_check("DELETE", service_name, url, response)
        return response


# Convenience functions for quick one-off calls
# Note: These create a new client for each call, which is less efficient
# than using InterServiceClient as a context manager for multiple calls.

async def service_get(
    service_name: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    auth_token: Optional[str] = None,
) -> httpx.Response:
    """
    Convenience function for a single GET request to another service.
    
    For multiple calls to the same service, use InterServiceClient instead.
    """
    async with InterServiceClient(auth_token=auth_token) as client:
        return await client.get(service_name, path, params=params)


async def service_post(
    service_name: str,
    path: str,
    json: Optional[Dict[str, Any]] = None,
    auth_token: Optional[str] = None,
) -> httpx.Response:
    """
    Convenience function for a single POST request to another service.
    
    For multiple calls to the same service, use InterServiceClient instead.
    """
    async with InterServiceClient(auth_token=auth_token) as client:
        return await client.post(service_name, path, json=json)


async def service_put(
    service_name: str,
    path: str,
    json: Optional[Dict[str, Any]] = None,
    auth_token: Optional[str] = None,
) -> httpx.Response:
    """Convenience function for a single PUT request"""
    async with InterServiceClient(auth_token=auth_token) as client:
        return await client.put(service_name, path, json=json)


async def service_delete(
    service_name: str,
    path: str,
    auth_token: Optional[str] = None,
) -> httpx.Response:
    """Convenience function for a single DELETE request"""
    async with InterServiceClient(auth_token=auth_token) as client:
        return await client.delete(service_name, path)


async def discover_service_url(service_name: str) -> str:
    """
    Discover a service's URL from the registry.
    
    Use this when you need the URL but will make the HTTP call yourself
    (e.g., with a different HTTP client or for websockets).
    """
    registry = get_registry_client()
    return await registry.discover(service_name)
