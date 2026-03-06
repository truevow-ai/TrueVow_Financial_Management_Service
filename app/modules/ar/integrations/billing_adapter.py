"""Billing Service Adapter Interface"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID
import logging
import time
from app.core.retry import retry_async, RetryConfig
from app.core.monitoring import get_logger, log_api_call, log_retry_event, log_performance_metric

logger = logging.getLogger(__name__)
monitoring_logger = get_logger('billing_integration')

# Retry configuration for billing service calls
BILLING_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    retryable_exceptions=(Exception,)
)


class BillingAdapter(ABC):
    """Abstract adapter for Billing service integration"""
    
    @abstractmethod
    async def get_customers(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get customers from Billing service
        
        Returns: (customers, next_cursor)
        """
        pass
    
    @abstractmethod
    async def get_invoices(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get invoices from Billing service
        
        Returns: (invoices, next_cursor)
        """
        pass
    
    @abstractmethod
    async def get_payments(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get payments from Billing service
        
        Returns: (payments, next_cursor)
        """
        pass
    
    @abstractmethod
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict]:
        """Get single invoice by ID"""
        pass
    
    @abstractmethod
    async def get_payment_by_id(self, payment_id: str) -> Optional[Dict]:
        """Get single payment by ID"""
        pass
    
    @abstractmethod
    async def get_tenant_pricing(self, tenant_id: UUID) -> Optional[Dict]:
        """Get pricing information for a tenant"""
        pass
    
    @abstractmethod
    async def get_tenant_addons(self, tenant_id: UUID) -> List[Dict]:
        """Get add-on purchases for a tenant"""
        pass


class HTTPBillingAdapter(BillingAdapter):
    """HTTP client adapter for Billing service (uses billing_service_url)."""
    def __init__(self):
        from app.core.config import settings
        self._base_url = (settings.billing_service_url or "").rstrip("/")
        self._token = settings.billing_service_token or settings.billing_api_key

    async def get_customers(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get customers from Billing service with retry logic and monitoring"""
        if not self._base_url:
            return [], None
        
        import httpx
        
        async def _fetch():
            start_time = time.time()
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get(
                        f"{self._base_url}/customers",
                        params={"entity_id": str(entity_id), "limit": limit, "cursor": since_cursor},
                        headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
                    )
                    r.raise_for_status()
                    data = r.json()
                    
                    # Log successful API call
                    duration_ms = (time.time() - start_time) * 1000
                    log_api_call(
                        logger=monitoring_logger,
                        service='billing',
                        endpoint='/customers',
                        status_code=r.status_code,
                        duration_ms=duration_ms,
                        success=True,
                        metadata={'entity_id': str(entity_id)}
                    )
                    
                    # Check performance
                    log_performance_metric(
                        logger=monitoring_logger,
                        metric_name='billing_api_response_time',
                        value=duration_ms,
                        threshold_warning=500,
                        threshold_critical=2000
                    )
                    
                    return data.get("items", []), data.get("next_cursor")
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_api_call(
                    logger=monitoring_logger,
                    service='billing',
                    endpoint='/customers',
                    status_code=None,
                    duration_ms=duration_ms,
                    success=False,
                    error_message=str(e),
                    metadata={'entity_id': str(entity_id)}
                )
                raise
        
        return await execute_with_retry(_fetch, config=BILLING_RETRY_CONFIG)

    async def get_invoices(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get invoices from Billing service with retry logic"""
        if not self._base_url:
            return [], None
        
        import httpx
        
        async def _fetch():
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self._base_url}/invoices",
                    params={"entity_id": str(entity_id), "limit": limit, "cursor": since_cursor},
                    headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
                )
                r.raise_for_status()
                data = r.json()
                return data.get("items", []), data.get("next_cursor")
        
        return await execute_with_retry(_fetch, config=BILLING_RETRY_CONFIG)

    async def get_payments(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get payments from Billing service with retry logic"""
        if not self._base_url:
            return [], None
        
        import httpx
        
        async def _fetch():
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self._base_url}/payments",
                    params={"entity_id": str(entity_id), "limit": limit, "cursor": since_cursor},
                    headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
                )
                r.raise_for_status()
                data = r.json()
                return data.get("items", []), data.get("next_cursor")
        
        return await execute_with_retry(_fetch, config=BILLING_RETRY_CONFIG)

    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict]:
        """Get single invoice by ID with retry logic"""
        if not self._base_url:
            return None
        
        import httpx
        
        async def _fetch():
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self._base_url}/invoices/{invoice_id}",
                    headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
                )
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                return r.json()
        
        try:
            return await execute_with_retry(_fetch, config=BILLING_RETRY_CONFIG)
        except Exception:
            return None

    async def get_payment_by_id(self, payment_id: str) -> Optional[Dict]:
        """Get single payment by ID with retry logic"""
        if not self._base_url:
            return None
        
        import httpx
        
        async def _fetch():
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self._base_url}/payments/{payment_id}",
                    headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
                )
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                return r.json()
        
        try:
            return await execute_with_retry(_fetch, config=BILLING_RETRY_CONFIG)
        except Exception:
            return None
    
    async def get_tenant_pricing(self, tenant_id: UUID) -> Optional[Dict]:
        """Get pricing information for a tenant from Billing service with retry logic"""
        if not self._base_url:
            return None
        
        import httpx
        
        async def _fetch():
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self._base_url}/tenants/{tenant_id}/feature-access",
                    headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
                )
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                return r.json()
        
        try:
            return await execute_with_retry(_fetch, config=BILLING_RETRY_CONFIG)
        except Exception:
            return None
    
    async def get_tenant_addons(self, tenant_id: UUID) -> List[Dict]:
        """Get add-on purchases for a tenant from Billing service with retry logic"""
        if not self._base_url:
            return []
        
        import httpx
        
        async def _fetch():
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self._base_url}/tenants/{tenant_id}/addons",
                    headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
                )
                if r.status_code == 404:
                    return []
                r.raise_for_status()
                return r.json().get("addons", [])
        
        try:
            return await execute_with_retry(_fetch, config=BILLING_RETRY_CONFIG)
        except Exception:
            return []

