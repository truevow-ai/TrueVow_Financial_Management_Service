"""Intercompany Reconciliation Service"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.intercompany.repositories.intercompany_transfer_repository import IntercompanyTransferRepository
from app.modules.intercompany.repositories.intercompany_balance_repository import IntercompanyBalanceRepository
from app.modules.intercompany.models.intercompany_transfer_model import IntercompanyTransfer
from app.modules.intercompany.models.intercompany_balance_model import IntercompanyBalance, BalanceType
from app.core.exceptions import NotFoundError, ValidationError


class IntercompanyReconciliationService:
    """Service for intercompany reconciliation"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transfer_repo = IntercompanyTransferRepository(session)
        self.balance_repo = IntercompanyBalanceRepository(session)
    
    async def calculate_balance(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        as_of_date: date
    ) -> Decimal:
        """Calculate intercompany balance"""
        return await self.transfer_repo.calculate_balance(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            as_of_date=as_of_date
        )
    
    async def create_balance_snapshot(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        as_of_date: date
    ) -> IntercompanyBalance:
        """Create balance snapshot"""
        # Calculate balance
        balance_amount = await self.calculate_balance(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            as_of_date=as_of_date
        )
        
        # Determine balance type
        if balance_amount > 0:
            balance_type = BalanceType.RECEIVABLE  # From entity's perspective
        elif balance_amount < 0:
            balance_type = BalanceType.PAYABLE
        else:
            balance_type = BalanceType.NET
        
        # Get currency from first transfer (or entity default)
        transfers = await self.transfer_repo.list_by_entity_pair(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            limit=1
        )
        currency = transfers[0].currency if transfers else "USD"
        
        # Check if snapshot exists
        existing = await self.balance_repo.get_balance(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            as_of_date=as_of_date,
            balance_type=balance_type
        )
        
        if existing:
            # Update existing
            await self.balance_repo.update(
                existing.id,
                balance_amount=abs(balance_amount)
            )
            await self.session.commit()
            return await self.balance_repo.get_by_id(existing.id)
        else:
            # Create new
            balance = await self.balance_repo.create(
                from_entity_id=from_entity_id,
                to_entity_id=to_entity_id,
                as_of_date=as_of_date,
                balance_type=balance_type,
                balance_amount=abs(balance_amount),
                currency=currency
            )
            await self.session.commit()
            return balance
    
    async def reconcile_transfers(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        transfer_ids: List[UUID],
        reconciled_at: date
    ) -> int:
        """Reconcile transfers"""
        reconciled_count = 0
        
        for transfer_id in transfer_ids:
            transfer = await self.transfer_repo.get_by_id(transfer_id)
            if not transfer:
                continue
            
            if transfer.from_entity_id != from_entity_id or transfer.to_entity_id != to_entity_id:
                continue
            
            if not transfer.is_reconciled:
                await self.transfer_repo.update(
                    transfer_id,
                    is_reconciled=True,
                    reconciled_at=reconciled_at
                )
                reconciled_count += 1
        
        await self.session.commit()
        return reconciled_count
    
    async def get_reconciliation_report(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        as_of_date: date
    ) -> Dict:
        """Get reconciliation report"""
        # Get all transfers
        transfers = await self.transfer_repo.list_by_entity_pair(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            end_date=as_of_date
        )
        
        # Calculate totals
        total_transfers = len(transfers)
        reconciled_count = sum(1 for t in transfers if t.is_reconciled)
        unreconciled_count = total_transfers - reconciled_count
        
        # Calculate balance
        balance = await self.calculate_balance(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            as_of_date=as_of_date
        )
        
        return {
            "from_entity_id": str(from_entity_id),
            "to_entity_id": str(to_entity_id),
            "as_of_date": as_of_date.isoformat(),
            "total_transfers": total_transfers,
            "reconciled_count": reconciled_count,
            "unreconciled_count": unreconciled_count,
            "net_balance": float(balance),
            "transfers": [
                {
                    "id": str(t.id),
                    "transfer_date": t.transfer_date.isoformat(),
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "is_reconciled": t.is_reconciled
                }
                for t in transfers
            ]
        }
