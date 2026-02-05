"""Transfer Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.treasury.repositories.transfer_repository import TransferRepository
from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
from app.modules.general_ledger.repositories.legal_entity_repository import LegalEntityRepository
from app.modules.treasury.models.transfer_model import Transfer, TransferType
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError


class TransferService:
    """Service for transfer management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transfer_repo = TransferRepository(session)
        self.account_repo = BankAccountRepository(session)
        self.entity_repo = LegalEntityRepository(session)
    
    async def create_transfer(
        self,
        legal_entity_id: UUID,
        transfer_date: date,
        transfer_type: TransferType,
        from_bank_account_id: UUID,
        amount: Decimal,
        currency: str,
        to_bank_account_id: Optional[UUID] = None,
        to_entity_id: Optional[UUID] = None,
        description: Optional[str] = None,
        reference_number: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> Transfer:
        """Create a transfer"""
        # Verify entity exists
        entity = await self.entity_repo.get_by_id(legal_entity_id)
        if not entity:
            raise NotFoundError(f"Legal entity {legal_entity_id} not found")
        
        # Verify from account exists and belongs to entity
        from_account = await self.account_repo.get_by_id(from_bank_account_id)
        if not from_account:
            raise NotFoundError(f"From bank account {from_bank_account_id} not found")
        if from_account.legal_entity_id != legal_entity_id:
            raise ValidationError("From account must belong to the specified entity")
        if from_account.currency != currency:
            raise ValidationError(f"From account currency {from_account.currency} does not match transfer currency {currency}")
        
        # Verify to account if provided
        if to_bank_account_id:
            to_account = await self.account_repo.get_by_id(to_bank_account_id)
            if not to_account:
                raise NotFoundError(f"To bank account {to_bank_account_id} not found")
            if to_account.currency != currency:
                raise ValidationError(f"To account currency {to_account.currency} does not match transfer currency {currency}")
        
        # Verify to entity for intercompany transfers
        if transfer_type == TransferType.INTERCOMPANY:
            if not to_entity_id:
                raise ValidationError("Intercompany transfer requires to_entity_id")
            to_entity = await self.entity_repo.get_by_id(to_entity_id)
            if not to_entity:
                raise NotFoundError(f"To entity {to_entity_id} not found")
        
        # Check for duplicate by external_id
        if external_id:
            existing = await self.transfer_repo.get_by_external_id(external_id)
            if existing:
                raise DuplicateEntryError(f"Transfer with external_id {external_id} already exists")
        
        transfer = await self.transfer_repo.create(
            legal_entity_id=legal_entity_id,
            transfer_date=transfer_date,
            transfer_type=transfer_type,
            from_bank_account_id=from_bank_account_id,
            to_bank_account_id=to_bank_account_id,
            to_entity_id=to_entity_id,
            amount=amount,
            currency=currency,
            description=description,
            reference_number=reference_number,
            external_id=external_id
        )
        
        await self.session.commit()
        return transfer
    
    async def get_transfer(self, transfer_id: UUID) -> Optional[Transfer]:
        """Get transfer by ID"""
        return await self.transfer_repo.get_by_id(transfer_id)
    
    async def list_transfers(
        self,
        entity_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transfer_type: Optional[TransferType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transfer]:
        """List transfers for an entity"""
        return await self.transfer_repo.list_by_entity(
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
            transfer_type=transfer_type,
            limit=limit,
            offset=offset
        )
