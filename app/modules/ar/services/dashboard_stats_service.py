"""Dashboard Statistics Service - Fetches real-time stats from database"""
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from app.modules.ar.schemas.dashboard_stats_schemas import DashboardStatsResponse

logger = logging.getLogger(__name__)


class DashboardStatsService:
    """Service for fetching dashboard statistics from database"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_dashboard_stats(
        self,
        legal_entity_id: UUID,
        book_id: Optional[UUID] = None
    ) -> DashboardStatsResponse:
        """Get comprehensive dashboard statistics
        
        Args:
            legal_entity_id: Legal entity identifier
            book_id: Optional book/filter identifier
            
        Returns:
            DashboardStatsResponse with all metrics
        """
        try:
            logger.info(f"Fetching dashboard stats for entity {legal_entity_id}, book {book_id}")
            
            # Fetch financial metrics from database
            financial_stats = await self._get_financial_metrics(legal_entity_id, book_id)
            
            # Fetch operational metrics
            operational_stats = await self._get_operational_metrics(legal_entity_id, book_id)
            
            logger.info(f"Successfully retrieved dashboard stats for entity {legal_entity_id}")
            
            return DashboardStatsResponse(
                **financial_stats,
                **operational_stats
            )
        except Exception as e:
            logger.error(f"Failed to fetch dashboard stats for entity {legal_entity_id}: {str(e)}")
            raise
    
    async def _get_financial_metrics(
        self,
        legal_entity_id: UUID,
        book_id: Optional[UUID]
    ) -> Dict:
        """Fetch financial metrics from general ledger"""
        
        # For now, return zeros since we need to calculate from journal entries
        # A proper implementation would sum journal_line balances per account type
        # This requires complex SQL to calculate running balances
        
        # TODO: Implement proper balance calculations from:
        # - journal_entry + journal_line tables
        # - Need to sum debits - credits for each account
        # - Then aggregate by account type (ASSET, LIABILITY, REVENUE, EXPENSE)
        
        logger.warning("Financial metrics calculation from GL not yet implemented - returning zeros")
        
        return {
            "total_revenue": Decimal("0"),
            "total_expenses": Decimal("0"),
            "net_income": Decimal("0"),
            "cash_position": Decimal("0"),
            "accounts_receivable": Decimal("0"),
            "accounts_payable": Decimal("0"),
            "total_assets": None,
            "total_liabilities": None,
            "equity": None
        }
    
    async def _get_operational_metrics(
        self,
        legal_entity_id: UUID,
        book_id: Optional[UUID]
    ) -> Dict:
        """Fetch operational metrics from AR/AP modules"""
        
        # Count pending approvals (from approval workflows)
        pending_approvals = await self._count_pending_approvals(legal_entity_id)
        
        # Count overdue invoices
        overdue_invoices = await self._count_overdue_invoices(legal_entity_id)
        
        # Count upcoming payments
        upcoming_payments = await self._count_upcoming_payments(legal_entity_id)
        
        return {
            "pending_approvals": pending_approvals,
            "overdue_invoices": overdue_invoices,
            "upcoming_payments": upcoming_payments
        }
    
    async def _count_pending_approvals(self, legal_entity_id: UUID) -> int:
        """Count items pending approval"""
        # TODO: Query approval workflow tables
        return 0
    
    async def _count_overdue_invoices(self, legal_entity_id: UUID) -> int:
        """Count overdue AR invoices"""
        from sqlalchemy import text
        
        result = await self.session.execute(
            text("""
                SELECT COUNT(*) as count
                FROM ar_invoice
                WHERE legal_entity_id = :legal_entity_id
                AND status = 'ISSUED'
                AND due_date < CURRENT_DATE
                AND outstanding_amount > 0
            """),
            {"legal_entity_id": legal_entity_id}
        )
        
        count = result.scalar() or 0
        return int(count)
    
    async def _count_upcoming_payments(self, legal_entity_id: UUID) -> int:
        """Count upcoming AP payments due within next 7 days"""
        from sqlalchemy import text
        
        result = await self.session.execute(
            text("""
                SELECT COUNT(*) as count
                FROM ap_bill
                WHERE legal_entity_id = :legal_entity_id
                AND due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                AND status IN ('pending', 'approved')
            """),
            {"legal_entity_id": legal_entity_id}
        )
        
        count = result.scalar() or 0
        return int(count)
