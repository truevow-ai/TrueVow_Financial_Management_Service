"""Intercompany Transfer Repository"""
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.intercompany.models.intercompany_transfer_model import IntercompanyTransfer


class IntercompanyTransferRepository(BaseRepository[IntercompanyTransfer]):
    """Repository for IntercompanyTransfer"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, IntercompanyTransfer)
    
    async def list_by_entity_pair(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_reconciled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[IntercompanyTransfer]:
        """List transfers between two entities"""
        query = select(IntercompanyTransfer).where(
            (IntercompanyTransfer.from_entity_id == from_entity_id) &
            (IntercompanyTransfer.to_entity_id == to_entity_id)
        )
        
        if start_date:
            query = query.where(IntercompanyTransfer.transfer_date >= start_date)
        if end_date:
            query = query.where(IntercompanyTransfer.transfer_date <= end_date)
        if is_reconciled is not None:
            query = query.where(IntercompanyTransfer.is_reconciled == is_reconciled)
        
        query = query.order_by(IntercompanyTransfer.transfer_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        direction: Optional[str] = None,  # "from" or "to"
        limit: int = 100,
        offset: int = 0
    ) -> List[IntercompanyTransfer]:
        """List transfers for an entity"""
        if direction == "from":
            query = select(IntercompanyTransfer).where(
                IntercompanyTransfer.from_entity_id == entity_id
            )
        elif direction == "to":
            query = select(IntercompanyTransfer).where(
                IntercompanyTransfer.to_entity_id == entity_id
            )
        else:
            query = select(IntercompanyTransfer).where(
                or_(
                    IntercompanyTransfer.from_entity_id == entity_id,
                    IntercompanyTransfer.to_entity_id == entity_id
                )
            )
        
        query = query.order_by(IntercompanyTransfer.transfer_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def calculate_balance(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """Calculate net balance between entities"""
        query = select(IntercompanyTransfer).where(
            (IntercompanyTransfer.from_entity_id == from_entity_id) &
            (IntercompanyTransfer.to_entity_id == to_entity_id)
        )
        
        if as_of_date:
            query = query.where(IntercompanyTransfer.transfer_date <= as_of_date)
        
        result = await self.session.execute(query)
        transfers = list(result.scalars().all())
        
        # Net balance = sum of transfers (positive = receivable, negative = payable)
        balance = Decimal("0.00")
        for transfer in transfers:
            balance += transfer.amount  # From entity's perspective
        
        return balance
