"""Billing Service Adapter Interface"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID


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
        if not self._base_url:
            return [], None
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base_url}/customers",
                params={"entity_id": str(entity_id), "limit": limit, "cursor": since_cursor},
                headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
            )
            r.raise_for_status()
            data = r.json()
            return data.get("items", []), data.get("next_cursor")

    async def get_invoices(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        if not self._base_url:
            return [], None
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base_url}/invoices",
                params={"entity_id": str(entity_id), "limit": limit, "cursor": since_cursor},
                headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
            )
            r.raise_for_status()
            data = r.json()
            return data.get("items", []), data.get("next_cursor")

    async def get_payments(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        if not self._base_url:
            return [], None
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base_url}/payments",
                params={"entity_id": str(entity_id), "limit": limit, "cursor": since_cursor},
                headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
            )
            r.raise_for_status()
            data = r.json()
            return data.get("items", []), data.get("next_cursor")

    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict]:
        if not self._base_url:
            return None
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base_url}/invoices/{invoice_id}",
                headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()

    async def get_payment_by_id(self, payment_id: str) -> Optional[Dict]:
        if not self._base_url:
            return None
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base_url}/payments/{payment_id}",
                headers={"Authorization": f"Bearer {self._token}"} if self._token else {}
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()


class MockBillingAdapter(BillingAdapter):
    """Mock Billing adapter for testing/development"""
    
    async def get_customers(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Mock implementation - returns empty list"""
        return [], None
    
    async def get_invoices(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Mock implementation - returns empty list"""
        return [], None
    
    async def get_payments(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Mock implementation - returns empty list"""
        return [], None
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict]:
        """Mock implementation"""
        return None
    
    async def get_payment_by_id(self, payment_id: str) -> Optional[Dict]:
        """Mock implementation"""
        return None
