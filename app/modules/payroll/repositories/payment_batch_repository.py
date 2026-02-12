"""Payment Batch Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.payroll.models.payment_batch_model import PayrollPaymentBatch, BatchStatus


class PayrollPaymentBatchRepository(BaseRepository[PayrollPaymentBatch]):
    """Repository for PayrollPaymentBatch"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PayrollPaymentBatch)
    
    async def get_by_batch_number(self, batch_number: str) -> Optional[PayrollPaymentBatch]:
        """Get batch by batch number"""
        result = await self.session.execute(
            select(PayrollPaymentBatch).where(PayrollPaymentBatch.batch_number == batch_number)
        )
        return result.scalar_one_or_none()
    
    async def list_by_run(
        self,
        payroll_run_id: UUID,
        status: Optional[BatchStatus] = None
    ) -> List[PayrollPaymentBatch]:
        """List batches for a payroll run"""
        query = select(PayrollPaymentBatch).where(
            PayrollPaymentBatch.payroll_run_id == payroll_run_id
        )
        if status:
            query = query.where(PayrollPaymentBatch.status == status)
        query = query.order_by(PayrollPaymentBatch.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
