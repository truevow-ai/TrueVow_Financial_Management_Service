"""Legal Entity Repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.legal_entity_model import LegalEntity


class LegalEntityRepository(BaseRepository[LegalEntity]):
    """Repository for LegalEntity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, LegalEntity)
    
    async def get_by_code(self, code: str) -> Optional[LegalEntity]:
        """Get entity by code"""
        result = await self.session.execute(
            select(LegalEntity).where(LegalEntity.code == code)
        )
        return result.scalar_one_or_none()
    
    async def list_active(self) -> list[LegalEntity]:
        """List all active entities"""
        result = await self.session.execute(
            select(LegalEntity).where(LegalEntity.is_active == True)
        )
        return list(result.scalars().all())
