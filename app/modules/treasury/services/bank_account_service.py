"""Bank Account Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
from app.modules.general_ledger.repositories.legal_entity_repository import LegalEntityRepository
from app.modules.treasury.models.bank_account_model import BankAccount
from app.core.exceptions import NotFoundError, ValidationError


class BankAccountService:
    """Service for bank account management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_repo = BankAccountRepository(session)
        self.entity_repo = LegalEntityRepository(session)
    
    async def create_account(
        self,
        legal_entity_id: UUID,
        account_name: str,
        bank_name: str,
        currency: str,
        account_number: Optional[str] = None,
        bank_code: Optional[str] = None,
        account_type: Optional[str] = None,
        wps_enabled: bool = False,
        wps_agent_id: Optional[str] = None
    ) -> BankAccount:
        """Create a new bank account"""
        # Verify entity exists
        entity = await self.entity_repo.get_by_id(legal_entity_id)
        if not entity:
            raise NotFoundError(f"Legal entity {legal_entity_id} not found")
        
        # Validate currency matches entity functional currency (optional check)
        # In practice, entities can have accounts in multiple currencies
        
        account = await self.account_repo.create(
            legal_entity_id=legal_entity_id,
            account_name=account_name,
            account_number=account_number,
            bank_name=bank_name,
            bank_code=bank_code,
            currency=currency,
            account_type=account_type,
            is_active=True,
            wps_enabled=wps_enabled,
            wps_agent_id=wps_agent_id
        )
        
        await self.session.commit()
        return account
    
    async def get_account(self, account_id: UUID) -> Optional[BankAccount]:
        """Get account by ID"""
        return await self.account_repo.get_by_id(account_id)
    
    async def list_accounts(
        self,
        entity_id: UUID,
        active_only: bool = True
    ) -> List[BankAccount]:
        """List accounts for an entity"""
        return await self.account_repo.list_by_entity(entity_id, active_only=active_only)
    
    async def update_account(
        self,
        account_id: UUID,
        account_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        wps_enabled: Optional[bool] = None,
        wps_agent_id: Optional[str] = None
    ) -> BankAccount:
        """Update bank account"""
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundError(f"Bank account {account_id} not found")
        
        updates = {}
        if account_name is not None:
            updates["account_name"] = account_name
        if is_active is not None:
            updates["is_active"] = is_active
        if wps_enabled is not None:
            updates["wps_enabled"] = wps_enabled
        if wps_agent_id is not None:
            updates["wps_agent_id"] = wps_agent_id
        
        if updates:
            await self.account_repo.update(account_id, **updates)
            await self.session.commit()
            return await self.account_repo.get_by_id(account_id)
        
        return account
