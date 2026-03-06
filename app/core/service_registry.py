"""
Service Registry Client

All microservices MUST participate in the Service Registry:
1. Internal Ops (port 3006) hosts the registry database and API
2. Every service registers on startup and sends heartbeat every 5 minutes
3. No documentation-based coordination — registry is the source of truth
4. Before calling another service, query registry to get current URL/endpoints
5. If a service is unreachable, log warning and fail fast (don't silently skip)

Supports:
- Service registration with endpoints, agents, and capabilities
- Module/feature registration for cross-service discovery
- Event-based service discovery (publishers/consumers)
- Integration contract registration
"""
import asyncio
import socket
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
from dataclasses import dataclass, field
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger


@dataclass
class ServiceConfig:
    """Service configuration for registration"""
    service_name: str
    service_type: str
    service_url: str
    port: int
    endpoints: List[Dict] = None
    agents: List[str] = None
    capabilities: List[str] = None
    
    def __post_init__(self):
        self.endpoints = self.endpoints or []
        self.agents = self.agents or []
        self.capabilities = self.capabilities or []
    
    def to_dict(self):
        return {
            "service_name": self.service_name,
            "service_type": self.service_type,
            "service_url": self.service_url,
            "port": self.port,
            "endpoints": self.endpoints,
            "agents": self.agents,
            "capabilities": self.capabilities,
        }


class ServiceInfo(BaseModel):
    """Information about a registered service"""
    name: str
    host: str
    port: int
    base_url: str
    health_endpoint: str
    last_heartbeat: Optional[datetime] = None
    status: str = "unknown"
    metadata: Dict[str, Any] = {}


class ServiceRegistryError(Exception):
    """Raised when registry operations fail"""
    pass


class ServiceUnreachableError(ServiceRegistryError):
    """Raised when a discovered service is unreachable"""
    pass


class ServiceRegistryClient:
    """
    Client for interacting with the Service Registry hosted by Internal Ops.
    
    Usage:
        # In lifespan startup:
        registry = ServiceRegistryClient()
        await registry.register()
        registry.start_heartbeat_task()
        
        # When calling another service:
        billing_url = await registry.discover("billing-service")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{billing_url}/api/health")
        
        # In lifespan shutdown:
        await registry.deregister()
        await registry.stop_heartbeat_task()
    """
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._is_registered = False
        self._service_cache: Dict[str, ServiceInfo] = {}
        self._cache_ttl_seconds = 60  # Cache service info for 1 minute
        self._last_cache_refresh: Dict[str, datetime] = {}
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for registry requests, including API key if configured"""
        headers = {"Content-Type": "application/json"}
        if settings.service_registry_api_key:
            headers["X-Registry-API-Key"] = settings.service_registry_api_key
        return headers
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-init HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.service_registry_timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._client
    
    @property
    def registry_url(self) -> str:
        """Get the registry base URL"""
        if not settings.service_registry_url:
            raise ServiceRegistryError(
                "SERVICE_REGISTRY_URL not configured. "
                "Set this to Internal Ops URL (e.g., http://localhost:3006)"
            )
        return settings.service_registry_url.rstrip("/")
    
    def _get_service_host(self) -> str:
        """Get this service's host for registration"""
        if settings.service_host:
            return settings.service_host
        # Auto-detect: in containers, use service name; locally use localhost
        try:
            # Try to get the container/service hostname
            hostname = socket.gethostname()
            if hostname and hostname != "localhost":
                return hostname
        except Exception:
            pass
        return "localhost"
    
    def _get_service_base_url(self) -> str:
        """Get this service's full base URL"""
        host = self._get_service_host()
        port = settings.service_port
        return f"http://{host}:{port}"
    
    async def register(self) -> bool:
        """
        Register this service with the registry.
        
        Called on startup. Must succeed for the service to be discoverable.
        
        Returns:
            True if registration succeeded
            
        Raises:
            ServiceRegistryError: If registration fails (fail fast)
        """
        if not settings.service_registry_enabled:
            logger.info("Service registry disabled, skipping registration")
            return True
        
        service_info = {
            "service_name": settings.service_name,
            "service_type": settings.service_type,
            "host": self._get_service_host(),
            "port": settings.service_port,
            "service_url": self._get_service_base_url(),
            "base_url": self._get_service_base_url(),
            "health_endpoint": "/health",
            "endpoints": [],
            "agents": [],
            "capabilities": [],
            "metadata": {
                "version": settings.app_version,
                "environment": settings.environment,
                "registered_at": datetime.now(UTC).isoformat(),
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.registry_url}/api/v1/registry",
                json=service_info,
                headers=self._get_headers(),
            )
            
            if response.status_code == 200 or response.status_code == 201:
                self._is_registered = True
                logger.info(
                    f"Service registered with registry: {settings.service_name} "
                    f"at {service_info['base_url']}"
                )
                return True
            else:
                error_detail = response.text[:200] if response.text else "Unknown error"
                raise ServiceRegistryError(
                    f"Registration failed with status {response.status_code}: {error_detail}"
                )
                
        except httpx.ConnectError as e:
            raise ServiceRegistryError(
                f"Cannot connect to registry at {self.registry_url}: {e}"
            )
        except httpx.TimeoutException as e:
            raise ServiceRegistryError(
                f"Timeout connecting to registry at {self.registry_url}: {e}"
            )
    
    async def deregister(self) -> bool:
        """
        Deregister this service from the registry.
        
        Called on shutdown for graceful departure.
        """
        if not settings.service_registry_enabled or not self._is_registered:
            return True
        
        try:
            response = await self.client.delete(
                f"{self.registry_url}/api/v1/registry/services/{settings.service_name}",
            )
            
            if response.status_code in (200, 204, 404):
                self._is_registered = False
                logger.info(f"Service deregistered from registry: {settings.service_name}")
                return True
            else:
                logger.warning(
                    f"Deregistration returned status {response.status_code}, "
                    "continuing shutdown anyway"
                )
                return True
                
        except Exception as e:
            # Don't fail shutdown on deregistration errors
            logger.warning(f"Deregistration error (non-fatal): {e}")
            return True
    
    async def send_heartbeat(self) -> bool:
        """
        Send a heartbeat to the registry.
        
        Called periodically by the heartbeat task.
        """
        if not settings.service_registry_enabled or not self._is_registered:
            return True
        
        try:
            response = await self.client.post(
                f"{self.registry_url}/api/v1/registry/heartbeat",
                json={
                    "service_name": settings.service_name,
                    "status": "healthy",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                headers=self._get_headers(),
            )
            
            if response.status_code == 200:
                logger.debug(f"Heartbeat sent for {settings.service_name}")
                return True
            else:
                logger.warning(
                    f"Heartbeat failed with status {response.status_code}: {response.text[:100]}"
                )
                return False
                
        except Exception as e:
            logger.warning(f"Heartbeat error: {e}")
            return False
    
    def start_heartbeat_task(self) -> None:
        """Start the background heartbeat task"""
        if not settings.service_registry_enabled:
            return
        
        if self._heartbeat_task is not None and not self._heartbeat_task.done():
            logger.warning("Heartbeat task already running")
            return
        
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(
            f"Heartbeat task started (interval: {settings.service_registry_heartbeat_interval}s)"
        )
    
    async def stop_heartbeat_task(self) -> None:
        """Stop the background heartbeat task"""
        if self._heartbeat_task is not None and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("Heartbeat task stopped")
    
    async def _heartbeat_loop(self) -> None:
        """Background loop that sends heartbeats"""
        while True:
            try:
                await asyncio.sleep(settings.service_registry_heartbeat_interval)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                # Continue the loop even on errors
    
    async def discover(self, service_name: str, use_cache: bool = True) -> str:
        """
        Discover a service's base URL from the registry.
        
        Args:
            service_name: Name of the service to discover (e.g., "billing-service")
            use_cache: Whether to use cached service info (default True)
            
        Returns:
            The base URL of the discovered service
            
        Raises:
            ServiceRegistryError: If the service cannot be found in the registry
            ServiceUnreachableError: If the service is registered but unreachable
        """
        if not settings.service_registry_enabled:
            # Fallback to configured URLs when registry is disabled
            fallback = self._get_fallback_url(service_name)
            if fallback:
                return fallback
            raise ServiceRegistryError(
                f"Service registry disabled and no fallback URL for {service_name}"
            )
        
        # Check cache
        if use_cache and service_name in self._service_cache:
            cached_at = self._last_cache_refresh.get(service_name)
            if cached_at:
                age = (datetime.now(UTC) - cached_at).total_seconds()
                if age < self._cache_ttl_seconds:
                    return self._service_cache[service_name].base_url
        
        # Query registry
        try:
            response = await self.client.get(
                f"{self.registry_url}/api/v1/registry/services/{service_name}",
            )
            
            if response.status_code == 200:
                data = await response.json()
                service_info = ServiceInfo(**data)
                self._service_cache[service_name] = service_info
                self._last_cache_refresh[service_name] = datetime.now(UTC)
                
                if service_info.status != "healthy":
                    logger.warning(
                        f"Service {service_name} is registered but status is {service_info.status}"
                    )
                
                return service_info.base_url
                
            elif response.status_code == 404:
                raise ServiceRegistryError(
                    f"Service '{service_name}' not found in registry. "
                    "Ensure the service is running and registered."
                )
            else:
                raise ServiceRegistryError(
                    f"Registry lookup failed with status {response.status_code}: {response.text[:100]}"
                )
                
        except httpx.ConnectError as e:
            raise ServiceRegistryError(
                f"Cannot connect to registry at {self.registry_url}: {e}"
            )
        except httpx.TimeoutException as e:
            raise ServiceRegistryError(
                f"Timeout connecting to registry: {e}"
            )
    
    async def discover_all(self) -> List[ServiceInfo]:
        """
        Discover all registered services.
        
        Returns:
            List of all registered services
        """
        if not settings.service_registry_enabled:
            return []
        
        try:
            response = await self.client.get(
                f"{self.registry_url}/api/v1/registry/services",
            )
            
            if response.status_code == 200:
                data = await response.json()
                return [ServiceInfo(**svc) for svc in data.get("services", [])]
            else:
                logger.warning(f"Failed to list services: {response.status_code}")
                return []
                
        except Exception as e:
            logger.warning(f"Error listing services: {e}")
            return []
    
    async def check_service_health(self, service_name: str) -> bool:
        """
        Check if a service is healthy by calling its health endpoint.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            True if the service is healthy, False otherwise
        """
        try:
            base_url = await self.discover(service_name)
            response = await self.client.get(f"{base_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed for {service_name}: {e}")
            return False
    
    def _get_fallback_url(self, service_name: str) -> Optional[str]:
        """Get fallback URL from settings when registry is disabled"""
        fallbacks = {
            "billing-service": settings.billing_service_url,
            "tenant_billing": settings.billing_service_url,
            "treasury-service": settings.treasury_api_url,
            "auth-service": settings.auth_service_url,
            "internal_ops": "http://localhost:3006",
        }
        return fallbacks.get(service_name)
    
    # ========== MODULE REGISTRATION ==========
    
    async def register_module(
        self,
        module_name: str,
        module_version: str = "1.0.0",
        description: str = None,
        endpoints: List[Dict] = None,
        events_published: List[Dict] = None,
        events_consumed: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Register a module/feature for this service.
        
        Args:
            module_name: Name of the module (e.g., "ar_summary", "bank_reconciliation")
            module_version: Version string
            description: Human-readable description
            endpoints: List of API endpoints this module exposes
            events_published: List of events this module publishes
            events_consumed: List of events this module consumes
            
        Returns:
            Registration result
        """
        try:
            response = await self.client.post(
                f"{self.registry_url}/api/v1/registry/modules",
                json={
                    "service_name": settings.service_name,
                    "module_name": module_name,
                    "module_version": module_version,
                    "description": description,
                    "endpoints": endpoints or [],
                    "events_published": events_published or [],
                    "events_consumed": events_consumed or [],
                },
                headers=self._get_headers(),
            )
            response.raise_for_status()
            logger.info(f"Module registered: {module_name}")
            return response.json()
        except Exception as e:
            logger.error(f"Module registration failed for {module_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_modules(self, service_name: str = None) -> List[Dict[str, Any]]:
        """
        Get all modules for a service.
        
        Args:
            service_name: Service to query (defaults to this service)
            
        Returns:
            List of module information
        """
        target_service = service_name or settings.service_name
        try:
            response = await self.client.get(
                f"{self.registry_url}/api/v1/registry/{target_service}/modules",
                headers=self._get_headers(),
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Get modules failed: {e}")
            return []
    
    # ========== EVENT DISCOVERY ==========
    
    async def find_by_event(self, event_name: str) -> Dict[str, Any]:
        """
        Find services that publish/consume an event.
        
        Args:
            event_name: Name of the event to search for
            
        Returns:
            {"publishers": [...], "consumers": [...]}
        """
        try:
            response = await self.client.get(
                f"{self.registry_url}/api/v1/modules/by-event/{event_name}",
                headers=self._get_headers(),
            )
            if response.status_code == 200:
                return response.json()
            return {"publishers": [], "consumers": []}
        except Exception as e:
            logger.error(f"Find by event failed: {e}")
            return {"publishers": [], "consumers": []}
    
    # ========== INTEGRATION REGISTRATION ==========
    
    async def get_integrations(self, service_name: str = None) -> Dict[str, Any]:
        """
        Get integration partners for a service.
        
        Args:
            service_name: Service to query (defaults to this service)
            
        Returns:
            {"receives_from": [...], "sends_to": [...]}
        """
        target_service = service_name or settings.service_name
        try:
            response = await self.client.get(
                f"{self.registry_url}/api/v1/integrations/{target_service}",
                headers=self._get_headers(),
            )
            if response.status_code == 200:
                return response.json()
            return {"receives_from": [], "sends_to": []}
        except Exception as e:
            logger.error(f"Get integrations failed: {e}")
            return {"receives_from": [], "sends_to": []}
    
    async def register_integration(
        self,
        target_service: str,
        integration_type: str,
        purpose: str = None,
        event_triggers: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Register an integration contract.
        
        Args:
            target_service: Service being integrated with
            integration_type: Type of integration (api, event, sync, etc.)
            purpose: Description of the integration
            event_triggers: Events that trigger this integration
            
        Returns:
            Registration result
        """
        try:
            response = await self.client.post(
                f"{self.registry_url}/api/v1/integrations",
                json={
                    "source_service": settings.service_name,
                    "target_service": target_service,
                    "integration_type": integration_type,
                    "purpose": purpose,
                    "event_triggers": event_triggers or [],
                },
                headers=self._get_headers(),
            )
            response.raise_for_status()
            logger.info(f"Integration registered: {settings.service_name} -> {target_service}")
            return response.json()
        except Exception as e:
            logger.error(f"Integration registration failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def close(self) -> None:
        """Close the HTTP client"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# Singleton instance
_registry_client: Optional[ServiceRegistryClient] = None


def get_registry_client() -> ServiceRegistryClient:
    """Get the singleton registry client instance"""
    global _registry_client
    if _registry_client is None:
        _registry_client = ServiceRegistryClient()
    return _registry_client


async def init_service_registry() -> ServiceRegistryClient:
    """
    Initialize and register with the service registry.
    
    Call this during application startup.
    """
    client = get_registry_client()
    await client.register()
    client.start_heartbeat_task()
    return client


async def shutdown_service_registry() -> None:
    """
    Deregister from the service registry and cleanup.
    
    Call this during application shutdown.
    """
    global _registry_client
    if _registry_client is not None:
        await _registry_client.stop_heartbeat_task()
        await _registry_client.deregister()
        await _registry_client.close()
        _registry_client = None


# ========== CONVENIENCE FUNCTIONS ==========

async def require_service(service_name: str) -> str:
    """
    Get service URL or raise error (fail-fast).
    
    Args:
        service_name: Name of the service to discover
        
    Returns:
        Service URL
        
    Raises:
        RuntimeError: If service is unavailable
    """
    client = get_registry_client()
    service = await client.discover(service_name)
    
    if not service:
        raise RuntimeError(f"Service '{service_name}' is unavailable")
    
    return service


async def register_fm_modules() -> None:
    """
    Register FM service modules with the registry.
    
    Imports all modules built from day one:
    - General Ledger (chart of accounts, periods, journal entries)
    - Treasury (bank accounts, transactions, transfers, FX, settlements)
    - Accounts Receivable (invoices, customers, payments, billing sync)
    - Accounts Payable (vendors, bills, payments)
    - Payroll (runs, components, payment batches)
    - Intercompany (transfers, royalties, reconciliation)
    - Reporting (trial balance, P&L, balance sheet, cash flow)
    """
    from app.core.fm_registry_modules import FM_MODULES
    client = get_registry_client()
    for module in FM_MODULES:
        await client.register_module(**module)


async def register_fm_integrations() -> None:
    """
    Register FM service integrations with other services.
    
    Integration contracts published to the registry:
    - tenant_billing: Event subscription for billing sync
    - cs_core: Event subscription for employee events (payroll)
    - internal_ops: Service registry discovery
    - fm_frontend: Frontend UI integration
    """
    from app.core.fm_registry_modules import FM_INTEGRATIONS
    client = get_registry_client()
    for integration in FM_INTEGRATIONS:
        await client.register_integration(**integration)
