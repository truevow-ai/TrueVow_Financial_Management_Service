"""HTTP Billing Adapter - Real implementation"""
from typing import List, Optional, Dict
from uuid import UUID
import httpx
from app.modules.ar.integrations.billing_adapter import BillingAdapter
from app.core.config import settings
from app.core.logging import logger


class HTTPBillingAdapter(BillingAdapter):
    """HTTP-based Billing service adapter"""
    
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or settings.billing_service_url or settings.billing_api_url
        self.token = token or settings.billing_service_token or settings.billing_api_key
        self.timeout = 30.0
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to Billing service"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_customers(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get customers from Billing service"""
        params = {
            "entity_id": str(entity_id),
            "limit": limit
        }
        if since_cursor:
            params["cursor"] = since_cursor
        
        try:
            data = await self._make_request("GET", "/api/v1/customers", params=params)
            customers = data.get("customers", [])
            next_cursor = data.get("next_cursor")
            return customers, next_cursor
        except Exception as e:
            logger.error(f"Error fetching customers from Billing: {e}")
            return [], None
    
    async def get_invoices(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get invoices from Billing service"""
        params = {
            "entity_id": str(entity_id),
            "limit": limit
        }
        if since_cursor:
            params["cursor"] = since_cursor
        
        try:
            data = await self._make_request("GET", "/api/v1/invoices", params=params)
            invoices = data.get("invoices", [])
            next_cursor = data.get("next_cursor")
            return invoices, next_cursor
        except Exception as e:
            logger.error(f"Error fetching invoices from Billing: {e}")
            return [], None
    
    async def get_payments(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Dict], Optional[str]]:
        """Get payments from Billing service"""
        params = {
            "entity_id": str(entity_id),
            "limit": limit
        }
        if since_cursor:
            params["cursor"] = since_cursor
        
        try:
            data = await self._make_request("GET", "/api/v1/payments", params=params)
            payments = data.get("payments", [])
            next_cursor = data.get("next_cursor")
            return payments, next_cursor
        except Exception as e:
            logger.error(f"Error fetching payments from Billing: {e}")
            return [], None
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict]:
        """Get single invoice by ID"""
        try:
            data = await self._make_request("GET", f"/api/v1/invoices/{invoice_id}")
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def get_payment_by_id(self, payment_id: str) -> Optional[Dict]:
        """Get single payment by ID"""
        try:
            data = await self._make_request("GET", f"/api/v1/payments/{payment_id}")
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
