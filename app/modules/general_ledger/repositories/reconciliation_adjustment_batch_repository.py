"""Reconciliation Adjustment Batch Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.reconciliation_adjustment_batch_model import ReconciliationAdjustmentBatch


class ReconciliationAdjustmentBatchRepository(BaseRepository[ReconciliationAdjustmentBatch]):
    """Repository for ReconciliationAdjustmentBatch"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ReconciliationAdjustmentBatch)
