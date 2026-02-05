"""Book Repository"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.book_model import Book, BookType


class BookRepository(BaseRepository[Book]):
    """Repository for Book"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)
    
    async def get_by_entity_and_type(
        self, 
        entity_id: UUID, 
        book_type: BookType
    ) -> Optional[Book]:
        """Get book by entity and type"""
        result = await self.session.execute(
            select(Book).where(
                Book.legal_entity_id == entity_id,
                Book.book_type == book_type
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(self, entity_id: UUID) -> List[Book]:
        """List all books for an entity"""
        result = await self.session.execute(
            select(Book).where(Book.legal_entity_id == entity_id)
        )
        return list(result.scalars().all())
