"""Dashboard Statistics API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.core.database import get_db_session
from app.modules.ar.services.dashboard_stats_service import DashboardStatsService
from app.modules.ar.schemas.dashboard_stats_schemas import DashboardStatsResponse
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/dashboard", tags=["Dashboard Statistics"], dependencies=[Depends(get_user_context)])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_statistics(
    legal_entity_id: UUID,
    book_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive dashboard statistics
    
    Fetches real-time financial and operational metrics from database:
    - Financial: Revenue, expenses, net income, cash position, AR/AP balances
    - Operational: Pending approvals, overdue invoices, upcoming payments
    
    Args:
        legal_entity_id: Legal entity identifier
        book_id: Optional book/filter identifier
        db: Database session
        
    Returns:
        DashboardStatsResponse with all metrics
    """
    try:
        service = DashboardStatsService(db)
        stats = await service.get_dashboard_stats(legal_entity_id, book_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard statistics: {str(e)}"
        )
