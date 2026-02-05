"""Settlement Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.treasury.repositories.settlement_repository import SettlementRepository
from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
from app.modules.general_ledger.repositories.legal_entity_repository import LegalEntityRepository
from app.modules.treasury.models.settlement_model import Settlement, SettlementSource
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError


class SettlementService:
    """Service for settlement management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settlement_repo = SettlementRepository(session)
        self.account_repo = BankAccountRepository(session)
        self.entity_repo = LegalEntityRepository(session)
    
    async def create_settlement(
        self,
        legal_entity_id: UUID,
        bank_account_id: UUID,
        settlement_date: date,
        source: SettlementSource,
        gross_amount: Decimal,
        fees: Decimal,
        net_amount: Decimal,
        currency: str,
        external_settlement_id: Optional[str] = None,
        external_payout_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Settlement:
        """Create a settlement"""
        # Verify entity exists
        entity = await self.entity_repo.get_by_id(legal_entity_id)
        if not entity:
            raise NotFoundError(f"Legal entity {legal_entity_id} not found")
        
        # Verify bank account exists and belongs to entity
        account = await self.account_repo.get_by_id(bank_account_id)
        if not account:
            raise NotFoundError(f"Bank account {bank_account_id} not found")
        if account.legal_entity_id != legal_entity_id:
            raise ValidationError("Bank account must belong to the specified entity")
        if account.currency != currency:
            raise ValidationError(f"Bank account currency {account.currency} does not match settlement currency {currency}")
        
        # Validate amounts
        if gross_amount < 0:
            raise ValidationError("Gross amount must be positive")
        if fees < 0:
            raise ValidationError("Fees must be positive")
        if net_amount != (gross_amount - fees):
            raise ValidationError(f"Net amount {net_amount} must equal gross_amount {gross_amount} - fees {fees}")
        
        # Check for duplicate by external_settlement_id
        if external_settlement_id:
            existing = await self.settlement_repo.get_by_external_id(external_settlement_id)
            if existing:
                raise DuplicateEntryError(f"Settlement with external_settlement_id {external_settlement_id} already exists")
        
        settlement = await self.settlement_repo.create(
            legal_entity_id=legal_entity_id,
            bank_account_id=bank_account_id,
            settlement_date=settlement_date,
            source=source,
            gross_amount=gross_amount,
            fees=fees,
            net_amount=net_amount,
            currency=currency,
            external_settlement_id=external_settlement_id,
            external_payout_id=external_payout_id,
            description=description
        )
        
        await self.session.commit()
        return settlement
    
    async def import_settlement(
        self,
        settlement_data: dict
    ) -> Settlement:
        """Import settlement from external system (manual JSON/CSV)"""
        return await self.create_settlement(
            legal_entity_id=settlement_data["legal_entity_id"],
            bank_account_id=settlement_data["bank_account_id"],
            settlement_date=settlement_data["settlement_date"],
            source=SettlementSource(settlement_data.get("source", "MANUAL")),
            gross_amount=Decimal(str(settlement_data["gross_amount"])),
            fees=Decimal(str(settlement_data.get("fees", 0))),
            net_amount=Decimal(str(settlement_data["net_amount"])),
            currency=settlement_data["currency"],
            external_settlement_id=settlement_data.get("external_settlement_id"),
            external_payout_id=settlement_data.get("external_payout_id"),
            description=settlement_data.get("description")
        )
    
    async def get_settlement(self, settlement_id: UUID) -> Optional[Settlement]:
        """Get settlement by ID"""
        return await self.settlement_repo.get_by_id(settlement_id)
    
    async def list_settlements(
        self,
        entity_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        source: Optional[SettlementSource] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Settlement]:
        """List settlements for an entity"""
        return await self.settlement_repo.list_by_entity(
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
            source=source,
            limit=limit,
            offset=offset
        )
