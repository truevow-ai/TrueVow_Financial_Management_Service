"""AP Bill Line Repository"""
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.ap.models.ap_bill_model import APBillLine


class APBillLineRepository:
    """Repository for AP Bill Line data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, line: APBillLine) -> APBillLine:
        """Create a new bill line"""
        self.session.add(line)
        await self.session.flush()
        return line
    
    async def list_by_bill(self, bill_id: UUID) -> List[APBillLine]:
        """List all lines for a bill"""
        stmt = select(APBillLine).where(
            APBillLine.ap_bill_id == bill_id
        ).order_by(APBillLine.line_number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete_by_bill(self, bill_id: UUID) -> int:
        """Delete all lines for a bill"""
        lines = await self.list_by_bill(bill_id)
        count = len(lines)
        for line in lines:
            await self.session.delete(line)
        await self.session.flush()
        return count
