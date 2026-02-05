"""GL Account Repository"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.gl_account_model import GLAccount, GLAccountMapping


class GLAccountRepository(BaseRepository[GLAccount]):
    """Repository for GLAccount"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, GLAccount)
    
    async def get_by_code_and_book(
        self, 
        account_code: str, 
        book_id: UUID
    ) -> Optional[GLAccount]:
        """Get account by code and book"""
        result = await self.session.execute(
            select(GLAccount).where(
                GLAccount.account_code == account_code,
                GLAccount.book_id == book_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_book(self, book_id: UUID) -> List[GLAccount]:
        """List all accounts for a book"""
        result = await self.session.execute(
            select(GLAccount)
            .where(GLAccount.book_id == book_id)
            .order_by(GLAccount.account_code)
        )
        return list(result.scalars().all())
    
    async def list_active_by_book(self, book_id: UUID) -> List[GLAccount]:
        """List active accounts for a book"""
        result = await self.session.execute(
            select(GLAccount)
            .where(
                GLAccount.book_id == book_id,
                GLAccount.is_active == True
            )
            .order_by(GLAccount.account_code)
        )
        return list(result.scalars().all())


class GLAccountMappingRepository(BaseRepository[GLAccountMapping]):
    """Repository for GLAccountMapping"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, GLAccountMapping)
    
    async def get_mapping(
        self,
        legal_entity_id: UUID,
        book_id: UUID,
        map_key: str
    ) -> Optional[GLAccountMapping]:
        """Get mapping by entity, book, and key"""
        result = await self.session.execute(
            select(GLAccountMapping).where(
                GLAccountMapping.legal_entity_id == legal_entity_id,
                GLAccountMapping.book_id == book_id,
                GLAccountMapping.map_key == map_key
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_book(self, book_id: UUID) -> List[GLAccountMapping]:
        """List all mappings for a book"""
        result = await self.session.execute(
            select(GLAccountMapping).where(
                GLAccountMapping.book_id == book_id
            )
        )
        return list(result.scalars().all())
