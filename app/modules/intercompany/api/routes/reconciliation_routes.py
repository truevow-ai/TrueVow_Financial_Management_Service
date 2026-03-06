"""Intercompany Reconciliation API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List
from app.core.database import get_db_session
from app.modules.intercompany.services.intercompany_reconciliation_service import IntercompanyReconciliationService
from app.modules.intercompany.models.intercompany_balance_model import IntercompanyBalance
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/intercompany/reconciliation", tags=["Intercompany Reconciliation"], dependencies=[Depends(get_user_context)])


@router.post("/balance-snapshot", status_code=status.HTTP_201_CREATED)
async def create_balance_snapshot(
    from_entity_id: UUID,
    to_entity_id: UUID,
    as_of_date: date = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Create intercompany balance snapshot"""
    service = IntercompanyReconciliationService(db)
    try:
        balance = await service.create_balance_snapshot(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            as_of_date=as_of_date
        )
        return {
            "id": str(balance.id),
            "from_entity_id": str(balance.from_entity_id),
            "to_entity_id": str(balance.to_entity_id),
            "as_of_date": balance.as_of_date.isoformat(),
            "balance_type": balance.balance_type.value,
            "balance_amount": float(balance.balance_amount),
            "currency": balance.currency
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reconcile", status_code=status.HTTP_200_OK)
async def reconcile_transfers(
    from_entity_id: UUID,
    to_entity_id: UUID,
    transfer_ids: List[UUID],
    reconciled_at: date = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Reconcile intercompany transfers"""
    service = IntercompanyReconciliationService(db)
    try:
        count = await service.reconcile_transfers(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            transfer_ids=transfer_ids,
            reconciled_at=reconciled_at
        )
        return {
            "reconciled_count": count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/report")
async def get_reconciliation_report(
    from_entity_id: UUID,
    to_entity_id: UUID,
    as_of_date: date = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Get intercompany reconciliation report"""
    service = IntercompanyReconciliationService(db)
    try:
        report = await service.get_reconciliation_report(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            as_of_date=as_of_date
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/balance")
async def get_balance(
    from_entity_id: UUID,
    to_entity_id: UUID,
    as_of_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Get intercompany balance"""
    service = IntercompanyReconciliationService(db)
    as_of = as_of_date or date.today()
    balance = await service.calculate_balance(
        from_entity_id=from_entity_id,
        to_entity_id=to_entity_id,
        as_of_date=as_of
    )
    return {
        "from_entity_id": str(from_entity_id),
        "to_entity_id": str(to_entity_id),
        "as_of_date": as_of.isoformat(),
        "balance": float(balance)
    }
