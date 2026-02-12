"""AP Vendor Repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.ap.models.ap_vendor_model import APVendor


class APVendorRepository:
    """Repository for AP Vendor data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, vendor: APVendor) -> APVendor:
        """Create a new vendor"""
        self.session.add(vendor)
        await self.session.flush()
        return vendor
    
    async def get_by_id(self, vendor_id: UUID) -> Optional[APVendor]:
        """Get vendor by ID"""
        stmt = select(APVendor).where(APVendor.id == vendor_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_code(self, vendor_code: str) -> Optional[APVendor]:
        """Get vendor by code"""
        stmt = select(APVendor).where(APVendor.vendor_code == vendor_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_by_entity(self, entity_id: UUID, is_active: Optional[bool] = None) -> List[APVendor]:
        """List vendors for an entity"""
        stmt = select(APVendor).where(APVendor.legal_entity_id == entity_id)
        if is_active is not None:
            stmt = stmt.where(APVendor.is_active == is_active)
        stmt = stmt.order_by(APVendor.vendor_name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, vendor: APVendor) -> APVendor:
        """Update a vendor"""
        await self.session.flush()
        return vendor
