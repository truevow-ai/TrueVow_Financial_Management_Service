"""Billing Sync Batch Repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime
from app.shared.repositories.base_repository import BaseRepository
from app.modules.ar.models.billing_sync_batch_model import BillingSyncBatch
from app.modules.general_ledger.models.treasury_sync_batch_model import SyncBatchStatus


class BillingSyncBatchRepository(BaseRepository[BillingSyncBatch]):
    """Repository for BillingSyncBatch"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, BillingSyncBatch)
    
    async def generate_batch_number(self, entity_id: UUID) -> str:
        """Generate unique batch number"""
        # Format: BS-YYYYMMDD-HHMMSS-XXXX
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")
        
        # Get count for today
        result = await self.session.execute(
            select(func.count(BillingSyncBatch.id)).where(
                BillingSyncBatch.legal_entity_id == entity_id,
                func.date(BillingSyncBatch.created_at) == now.date()
            )
        )
        count = result.scalar() or 0
        
        return f"BS-{date_str}-{time_str}-{count+1:04d}"
    
    async def get_by_batch_number(self, batch_number: str) -> Optional[BillingSyncBatch]:
        """Get batch by batch number"""
        result = await self.session.execute(
            select(BillingSyncBatch).where(BillingSyncBatch.batch_number == batch_number)
        )
        return result.scalar_one_or_none()
