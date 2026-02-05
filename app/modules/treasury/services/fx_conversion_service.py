"""FX Conversion Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.treasury.repositories.fx_conversion_repository import FXConversionRepository
from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
from app.modules.general_ledger.repositories.legal_entity_repository import LegalEntityRepository
from app.modules.treasury.models.fx_conversion_model import FXConversion
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError


class FXConversionService:
    """Service for FX conversion management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversion_repo = FXConversionRepository(session)
        self.account_repo = BankAccountRepository(session)
        self.entity_repo = LegalEntityRepository(session)
    
    async def create_conversion(
        self,
        legal_entity_id: UUID,
        conversion_date: date,
        from_currency: str,
        to_currency: str,
        from_amount: Decimal,
        to_amount: Decimal,
        exchange_rate: Decimal,
        rate_source: str,
        from_bank_account_id: Optional[UUID] = None,
        to_bank_account_id: Optional[UUID] = None,
        description: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> FXConversion:
        """Create an FX conversion"""
        # Verify entity exists
        entity = await self.entity_repo.get_by_id(legal_entity_id)
        if not entity:
            raise NotFoundError(f"Legal entity {legal_entity_id} not found")
        
        # Validate currencies are different
        if from_currency == to_currency:
            raise ValidationError("From and to currencies must be different")
        
        # Verify accounts if provided
        if from_bank_account_id:
            from_account = await self.account_repo.get_by_id(from_bank_account_id)
            if not from_account:
                raise NotFoundError(f"From bank account {from_bank_account_id} not found")
            if from_account.currency != from_currency:
                raise ValidationError(f"From account currency {from_account.currency} does not match conversion from_currency {from_currency}")
        
        if to_bank_account_id:
            to_account = await self.account_repo.get_by_id(to_bank_account_id)
            if not to_account:
                raise NotFoundError(f"To bank account {to_bank_account_id} not found")
            if to_account.currency != to_currency:
                raise ValidationError(f"To account currency {to_account.currency} does not match conversion to_currency {to_currency}")
        
        # Validate exchange rate calculation
        calculated_rate = to_amount / from_amount
        if abs(calculated_rate - exchange_rate) > Decimal("0.0001"):
            raise ValidationError(f"Exchange rate {exchange_rate} does not match calculated rate {calculated_rate}")
        
        # Check for duplicate by external_id
        if external_id:
            existing = await self.conversion_repo.get_by_external_id(external_id)
            if existing:
                raise DuplicateEntryError(f"FX conversion with external_id {external_id} already exists")
        
        conversion = await self.conversion_repo.create(
            legal_entity_id=legal_entity_id,
            conversion_date=conversion_date,
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=from_amount,
            to_amount=to_amount,
            exchange_rate=exchange_rate,
            rate_source=rate_source,
            from_bank_account_id=from_bank_account_id,
            to_bank_account_id=to_bank_account_id,
            description=description,
            external_id=external_id
        )
        
        await self.session.commit()
        return conversion
    
    async def get_conversion(self, conversion_id: UUID) -> Optional[FXConversion]:
        """Get conversion by ID"""
        return await self.conversion_repo.get_by_id(conversion_id)
    
    async def list_conversions(
        self,
        entity_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FXConversion]:
        """List conversions for an entity"""
        return await self.conversion_repo.list_by_entity(
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
