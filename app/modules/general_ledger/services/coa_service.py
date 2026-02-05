"""Chart of Accounts Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.general_ledger.repositories.gl_account_repository import (
    GLAccountRepository,
    GLAccountMappingRepository
)
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.gl_account_model import GLAccount, GLAccountMapping, AccountType
from app.core.exceptions import NotFoundError, ValidationError


class CoAService:
    """Service for Chart of Accounts management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_repo = GLAccountRepository(session)
        self.mapping_repo = GLAccountMappingRepository(session)
        self.book_repo = BookRepository(session)
    
    async def create_account(
        self,
        book_id: UUID,
        account_code: str,
        account_name: str,
        account_type: AccountType,
        parent_account_id: Optional[UUID] = None,
        description: Optional[str] = None
    ) -> GLAccount:
        """Create a new GL account"""
        # Verify book exists
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise NotFoundError(f"Book {book_id} not found")
        
        # Check if account code already exists in this book
        existing = await self.account_repo.get_by_code_and_book(account_code, book_id)
        if existing:
            raise ValidationError(f"Account code {account_code} already exists in book {book_id}")
        
        # If parent account specified, verify it exists and is in same book
        if parent_account_id:
            parent = await self.account_repo.get_by_id(parent_account_id)
            if not parent:
                raise NotFoundError(f"Parent account {parent_account_id} not found")
            if parent.book_id != book_id:
                raise ValidationError("Parent account must be in the same book")
        
        account = await self.account_repo.create(
            book_id=book_id,
            account_code=account_code,
            account_name=account_name,
            account_type=account_type,
            parent_account_id=parent_account_id,
            description=description,
            is_active=True
        )
        
        await self.session.commit()
        return account
    
    async def get_account(self, account_id: UUID) -> Optional[GLAccount]:
        """Get account by ID"""
        return await self.account_repo.get_by_id(account_id)
    
    async def list_accounts(self, book_id: UUID, active_only: bool = True) -> List[GLAccount]:
        """List accounts for a book"""
        if active_only:
            return await self.account_repo.list_active_by_book(book_id)
        return await self.account_repo.list_by_book(book_id)
    
    async def update_account(
        self,
        account_id: UUID,
        account_name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> GLAccount:
        """Update account (limited fields - code and type cannot be changed)"""
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundError(f"Account {account_id} not found")
        
        updates = {}
        if account_name is not None:
            updates["account_name"] = account_name
        if description is not None:
            updates["description"] = description
        if is_active is not None:
            updates["is_active"] = is_active
        
        if updates:
            await self.account_repo.update(account_id, **updates)
            await self.session.commit()
            return await self.account_repo.get_by_id(account_id)
        
        return account
    
    async def create_mapping(
        self,
        legal_entity_id: UUID,
        book_id: UUID,
        map_key: str,
        gl_account_id: UUID
    ) -> GLAccountMapping:
        """Create or update account mapping"""
        # Verify account exists and is in the book
        account = await self.account_repo.get_by_id(gl_account_id)
        if not account:
            raise NotFoundError(f"Account {gl_account_id} not found")
        if account.book_id != book_id:
            raise ValidationError("Account must be in the specified book")
        
        # Check if mapping exists
        existing = await self.mapping_repo.get_mapping(legal_entity_id, book_id, map_key)
        
        if existing:
            # Update existing mapping
            await self.mapping_repo.update(existing.id, gl_account_id=gl_account_id)
            await self.session.commit()
            return await self.mapping_repo.get_by_id(existing.id)
        else:
            # Create new mapping
            mapping = await self.mapping_repo.create(
                legal_entity_id=legal_entity_id,
                book_id=book_id,
                map_key=map_key,
                gl_account_id=gl_account_id
            )
            await self.session.commit()
            return mapping
    
    async def get_mapping(
        self,
        legal_entity_id: UUID,
        book_id: UUID,
        map_key: str
    ) -> Optional[GLAccountMapping]:
        """Get account mapping"""
        return await self.mapping_repo.get_mapping(legal_entity_id, book_id, map_key)
