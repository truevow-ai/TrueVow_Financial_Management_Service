"""Deferred Revenue Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.ar.models.deferred_revenue_model import (
    RevenueSchedule,
    RevenueSchedulePeriod,
    ScheduleStatus
)


class RevenueScheduleRepository(BaseRepository[RevenueSchedule]):
    """Repository for RevenueSchedule"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, RevenueSchedule)
    
    async def get_by_invoice_line(self, invoice_line_id: UUID) -> Optional[RevenueSchedule]:
        """Get schedule by invoice line"""
        result = await self.session.execute(
            select(RevenueSchedule).where(RevenueSchedule.ar_invoice_line_id == invoice_line_id)
        )
        return result.scalar_one_or_none()
    
    async def list_active_by_book(
        self,
        book_id: UUID,
        limit: int = 1000
    ) -> List[RevenueSchedule]:
        """List active schedules for a book"""
        result = await self.session.execute(
            select(RevenueSchedule)
            .where(
                RevenueSchedule.book_id == book_id,
                RevenueSchedule.status == ScheduleStatus.ACTIVE
            )
        )
        return list(result.scalars().all())


class RevenueSchedulePeriodRepository(BaseRepository[RevenueSchedulePeriod]):
    """Repository for RevenueSchedulePeriod"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, RevenueSchedulePeriod)
    
    async def list_unrecognized_by_period(
        self,
        period_start: date,
        period_end: date,
        limit: int = 1000
    ) -> List[RevenueSchedulePeriod]:
        """List unrecognized periods within date range"""
        result = await self.session.execute(
            select(RevenueSchedulePeriod)
            .where(
                RevenueSchedulePeriod.period_start >= period_start,
                RevenueSchedulePeriod.period_end <= period_end,
                RevenueSchedulePeriod.is_recognized == False
            )
        )
        return list(result.scalars().all())
    
    async def get_by_schedule_and_period(
        self,
        schedule_id: UUID,
        period_start: date
    ) -> Optional[RevenueSchedulePeriod]:
        """Get period by schedule and start date"""
        result = await self.session.execute(
            select(RevenueSchedulePeriod).where(
                RevenueSchedulePeriod.revenue_schedule_id == schedule_id,
                RevenueSchedulePeriod.period_start == period_start
            )
        )
        return result.scalar_one_or_none()
