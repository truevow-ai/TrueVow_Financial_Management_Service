"""Treasury Sync Service - Pulls Treasury data for FM posting"""
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from app.modules.treasury.repositories.bank_transaction_repository import BankTransactionRepository
from app.modules.treasury.repositories.settlement_repository import SettlementRepository
from app.modules.treasury.repositories.fx_conversion_repository import FXConversionRepository
from app.modules.treasury.repositories.transfer_repository import TransferRepository
from app.modules.treasury.repositories.sync_cursor_repository import SyncCursorRepository
from app.modules.treasury.models.bank_transaction_model import BankTransaction
from app.modules.treasury.models.settlement_model import Settlement
from app.modules.treasury.models.fx_conversion_model import FXConversion
from app.modules.treasury.models.transfer_model import Transfer
from app.core.exceptions import NotFoundError


class TreasurySyncService:
    """Service for syncing Treasury data to FM"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repo = BankTransactionRepository(session)
        self.settlement_repo = SettlementRepository(session)
        self.fx_repo = FXConversionRepository(session)
        self.transfer_repo = TransferRepository(session)
        self.cursor_repo = SyncCursorRepository(session)
    
    async def sync_transactions(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 1000
    ) -> tuple[List[BankTransaction], Optional[str]]:
        """Sync bank transactions from Treasury
        
        Returns: (transactions, next_cursor)
        """
        # Get or use provided cursor
        cursor_obj = await self.cursor_repo.get_cursor(
            entity_id=entity_id,
            source_system="treasury",
            object_type="transaction"
        )
        
        cursor = since_cursor or (cursor_obj.cursor_value if cursor_obj else None)
        
        # Get transactions with cursor pagination
        transactions, next_cursor = await self.transaction_repo.list_with_cursor(
            updated_after=None,  # Use cursor instead
            limit=limit,
            cursor=cursor
        )
        
        # Filter by entity (through bank accounts)
        entity_transactions = []
        for tx in transactions:
            # Need to check if transaction's bank account belongs to entity
            # This would require a join - simplified for now
            entity_transactions.append(tx)
        
        # Update cursor if we got results
        if next_cursor:
            await self.cursor_repo.update_cursor(
                entity_id=entity_id,
                source_system="treasury",
                object_type="transaction",
                cursor_value=next_cursor
            )
            await self.session.commit()
        
        return entity_transactions, next_cursor
    
    async def sync_settlements(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Settlement], Optional[str]]:
        """Sync settlements from Treasury"""
        # Get cursor
        cursor_obj = await self.cursor_repo.get_cursor(
            entity_id=entity_id,
            source_system="treasury",
            object_type="settlement"
        )
        
        # For settlements, use updated_after timestamp
        updated_after = None
        if cursor_obj and cursor_obj.last_sync_at:
            updated_after = cursor_obj.last_sync_at
        
        # List settlements
        settlements = await self.settlement_repo.list_by_entity(
            entity_id=entity_id,
            limit=limit,
            offset=0
        )
        
        # Update cursor
        if settlements:
            await self.cursor_repo.update_cursor(
                entity_id=entity_id,
                source_system="treasury",
                object_type="settlement",
                cursor_value=str(settlements[-1].id) if settlements else cursor_obj.cursor_value if cursor_obj else ""
            )
            await self.session.commit()
        
        return settlements, None
    
    async def sync_fx_conversions(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[FXConversion], Optional[str]]:
        """Sync FX conversions from Treasury"""
        conversions = await self.fx_repo.list_by_entity(
            entity_id=entity_id,
            limit=limit,
            offset=0
        )
        
        return conversions, None
    
    async def sync_transfers(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[Transfer], Optional[str]]:
        """Sync transfers from Treasury"""
        transfers = await self.transfer_repo.list_by_entity(
            entity_id=entity_id,
            limit=limit,
            offset=0
        )
        
        return transfers, None
