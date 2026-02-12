"""Royalty Calculation Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.intercompany.repositories.royalty_repository import (
    RoyaltyAgreementRepository,
    RoyaltyCalculationRepository
)
from app.modules.ar.repositories.ar_invoice_repository import ARInvoiceRepository
from app.modules.ar.repositories.deferred_revenue_repository import RevenueSchedulePeriodRepository
from app.modules.intercompany.models.royalty_model import (
    RoyaltyAgreement,
    RoyaltyCalculation,
    RoyaltyBasis
)
from app.core.exceptions import NotFoundError, ValidationError


class RoyaltyCalculationService:
    """Service for royalty calculations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.agreement_repo = RoyaltyAgreementRepository(session)
        self.calc_repo = RoyaltyCalculationRepository(session)
        self.invoice_repo = ARInvoiceRepository(session)
        self.revrec_repo = RevenueSchedulePeriodRepository(session)
    
    async def calculate_royalty(
        self,
        agreement_id: UUID,
        period_start: date,
        period_end: date
    ) -> RoyaltyCalculation:
        """Calculate royalty for a period"""
        agreement = await self.agreement_repo.get_by_id(agreement_id)
        if not agreement:
            raise NotFoundError(f"Royalty agreement {agreement_id} not found")
        
        if not agreement.is_active:
            raise ValidationError("Royalty agreement is not active")
        
        # Check if calculation already exists
        existing = await self.calc_repo.get_by_agreement_and_period(agreement_id, period_start)
        if existing:
            return existing
        
        # Get revenue base based on agreement basis
        revenue_base = Decimal("0.00")
        recognized_revenue_base = Decimal("0.00")
        collected_revenue_base = Decimal("0.00")
        
        if agreement.basis in [RoyaltyBasis.REVENUE, RoyaltyBasis.RECOGNIZED_REVENUE]:
            # Get recognized revenue from revenue recognition
            recognized = await self._get_recognized_revenue(
                agreement.from_entity_id,
                period_start,
                period_end
            )
            recognized_revenue_base = recognized
            if agreement.basis == RoyaltyBasis.REVENUE:
                revenue_base = recognized
        
        if agreement.basis in [RoyaltyBasis.REVENUE, RoyaltyBasis.COLLECTED_REVENUE]:
            # Get collected revenue from AR payments
            collected = await self._get_collected_revenue(
                agreement.from_entity_id,
                period_start,
                period_end
            )
            collected_revenue_base = collected
            if agreement.basis == RoyaltyBasis.REVENUE:
                revenue_base += collected
        
        if agreement.basis == RoyaltyBasis.FIXED:
            calculated_amount = agreement.fixed_amount or Decimal("0.00")
        else:
            # Calculate based on rate
            if agreement.basis == RoyaltyBasis.RECOGNIZED_REVENUE:
                base = recognized_revenue_base
            elif agreement.basis == RoyaltyBasis.COLLECTED_REVENUE:
                base = collected_revenue_base
            else:
                base = revenue_base
            
            calculated_amount = base * (agreement.rate / Decimal("100"))
        
        # Create calculation
        calculation = await self.calc_repo.create(
            royalty_agreement_id=agreement_id,
            period_start=period_start,
            period_end=period_end,
            revenue_base=revenue_base,
            recognized_revenue_base=recognized_revenue_base,
            collected_revenue_base=collected_revenue_base,
            calculated_amount=calculated_amount,
            currency=agreement.currency,
            is_posted=False
        )
        
        await self.session.commit()
        return calculation
    
    async def _get_recognized_revenue(
        self,
        entity_id: UUID,
        period_start: date,
        period_end: date
    ) -> Decimal:
        """Get recognized revenue for period"""
        # Get revenue recognition periods - need to join with schedule to filter by entity
        from sqlalchemy import select
        from app.modules.ar.models.deferred_revenue_model import RevenueSchedulePeriod, RevenueSchedule
        
        query = select(RevenueSchedulePeriod).join(RevenueSchedule).where(
            RevenueSchedule.legal_entity_id == entity_id,
            RevenueSchedulePeriod.period_start >= period_start,
            RevenueSchedulePeriod.period_end <= period_end,
            RevenueSchedulePeriod.is_recognized == True
        )
        
        result = await self.session.execute(query)
        periods = list(result.scalars().all())
        
        total = Decimal("0.00")
        for period in periods:
            total += period.recognition_amount
        
        return total
    
    async def _get_collected_revenue(
        self,
        entity_id: UUID,
        period_start: date,
        period_end: date
    ) -> Decimal:
        """Get collected revenue for period"""
        # Get AR payments in period for entity
        from sqlalchemy import select
        from app.modules.ar.models.ar_payment_model import ARPayment
        from app.modules.ar.models.ar_invoice_model import ARInvoice
        
        query = select(ARPayment).join(ARInvoice).where(
            ARInvoice.legal_entity_id == entity_id,
            ARPayment.payment_date >= period_start,
            ARPayment.payment_date <= period_end
        )
        
        result = await self.session.execute(query)
        payments = list(result.scalars().all())
        
        total = Decimal("0.00")
        for payment in payments:
            total += payment.payment_amount
        
        return total
    
    async def post_royalty(
        self,
        calculation_id: UUID,
        posted_by: UUID
    ) -> UUID:
        """Post royalty calculation as intercompany transfer"""
        calculation = await self.calc_repo.get_by_id(calculation_id)
        if not calculation:
            raise NotFoundError(f"Royalty calculation {calculation_id} not found")
        
        if calculation.is_posted:
            raise ValidationError("Royalty calculation already posted")
        
        # Create intercompany transfer
        from app.modules.intercompany.services.intercompany_transfer_service import IntercompanyTransferService
        transfer_service = IntercompanyTransferService(self.session)
        
        transfer = await transfer_service.create_transfer(
            from_entity_id=calculation.agreement.from_entity_id,
            to_entity_id=calculation.agreement.to_entity_id,
            transfer_date=calculation.period_end,
            amount=calculation.calculated_amount,
            currency=calculation.currency,
            transfer_type="ROYALTY",
            description=f"Royalty payment: {calculation.agreement.agreement_name} - {calculation.period_start}",
            reference_number=f"ROY-{calculation.agreement.agreement_code}-{calculation.period_start}"
        )
        
        # Post transfer to both entities
        from_je_id, to_je_id = await transfer_service.post_transfer(transfer.id, posted_by)
        
        # Update calculation
        await self.calc_repo.update(
            calculation_id,
            is_posted=True,
            posted_at=date.today(),
            journal_entry_id=from_je_id,  # From entity's journal entry
            intercompany_transfer_id=transfer.id
        )
        
        await self.session.commit()
        return from_je_id
