"""Royalty Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.intercompany.models.royalty_model import (
    RoyaltyAgreement,
    RoyaltyCalculation,
    RoyaltyBasis
)


class RoyaltyAgreementRepository(BaseRepository[RoyaltyAgreement]):
    """Repository for RoyaltyAgreement"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, RoyaltyAgreement)
    
    async def get_by_code(self, agreement_code: str) -> Optional[RoyaltyAgreement]:
        """Get agreement by code"""
        result = await self.session.execute(
            select(RoyaltyAgreement).where(RoyaltyAgreement.agreement_code == agreement_code)
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity_pair(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        active_only: bool = True
    ) -> List[RoyaltyAgreement]:
        """List agreements between two entities"""
        query = select(RoyaltyAgreement).where(
            (RoyaltyAgreement.from_entity_id == from_entity_id) &
            (RoyaltyAgreement.to_entity_id == to_entity_id)
        )
        if active_only:
            query = query.where(RoyaltyAgreement.is_active == True)
        query = query.order_by(RoyaltyAgreement.effective_from.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_active_by_date(
        self,
        calculation_date: date
    ) -> List[RoyaltyAgreement]:
        """List active agreements for a date"""
        result = await self.session.execute(
            select(RoyaltyAgreement).where(
                RoyaltyAgreement.is_active == True,
                RoyaltyAgreement.effective_from <= calculation_date,
                or_(
                    RoyaltyAgreement.effective_to >= calculation_date,
                    RoyaltyAgreement.effective_to.is_(None)
                )
            )
        )
        return list(result.scalars().all())


class RoyaltyCalculationRepository(BaseRepository[RoyaltyCalculation]):
    """Repository for RoyaltyCalculation"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, RoyaltyCalculation)
    
    async def get_by_agreement_and_period(
        self,
        agreement_id: UUID,
        period_start: date
    ) -> Optional[RoyaltyCalculation]:
        """Get calculation by agreement and period"""
        result = await self.session.execute(
            select(RoyaltyCalculation).where(
                RoyaltyCalculation.royalty_agreement_id == agreement_id,
                RoyaltyCalculation.period_start == period_start
            )
        )
        return result.scalar_one_or_none()
    
    async def list_unposted(
        self,
        entity_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[RoyaltyCalculation]:
        """List unposted calculations"""
        query = select(RoyaltyCalculation).where(
            RoyaltyCalculation.is_posted == False
        )
        
        if entity_id:
            # Join with agreement to filter by entity
            query = query.join(RoyaltyAgreement).where(
                or_(
                    RoyaltyAgreement.from_entity_id == entity_id,
                    RoyaltyAgreement.to_entity_id == entity_id
                )
            )
        
        query = query.order_by(RoyaltyCalculation.period_start.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
