"""Financial Report API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List, Optional
from app.core.database import get_db_session
from app.modules.reporting.services.trial_balance_service import TrialBalanceService
from app.modules.reporting.services.pl_balance_sheet_service import PLBalanceSheetService
from app.modules.reporting.services.cash_position_service import CashPositionService
from app.modules.reporting.services.ar_ap_aging_service import ARAgingService
from app.modules.reporting.services.gl_detail_service import GLDetailService
from app.modules.reporting.schemas.report_schemas import (
    TrialBalanceRequest,
    ProfitLossRequest,
    BalanceSheetRequest,
    CashPositionRequest,
    ARAgingRequest,
    GLDetailRequest
)
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/reports", tags=["Financial Reports"], dependencies=[Depends(get_user_context)])


@router.post("/trial-balance", status_code=status.HTTP_200_OK)
async def generate_trial_balance(
    request: TrialBalanceRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate Trial Balance report"""
    service = TrialBalanceService(db)
    try:
        report = await service.generate_trial_balance(
            book_id=request.book_id,
            period_id=request.period_id,
            as_of_date=request.as_of_date,
            include_zero_balance=request.include_zero_balance
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profit-loss", status_code=status.HTTP_200_OK)
async def generate_profit_loss(
    request: ProfitLossRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate Profit & Loss (Income Statement) report"""
    service = PLBalanceSheetService(db)
    try:
        report = await service.generate_profit_loss(
            book_id=request.book_id,
            period_start=request.period_start,
            period_end=request.period_end,
            compare_previous=request.compare_previous
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/balance-sheet", status_code=status.HTTP_200_OK)
async def generate_balance_sheet(
    request: BalanceSheetRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate Balance Sheet report"""
    service = PLBalanceSheetService(db)
    try:
        report = await service.generate_balance_sheet(
            book_id=request.book_id,
            as_of_date=request.as_of_date
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cash-position", status_code=status.HTTP_200_OK)
async def generate_cash_position(
    request: CashPositionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate Cash Position report"""
    service = CashPositionService(db)
    try:
        report = await service.generate_cash_position(
            entity_id=request.entity_id,
            as_of_date=request.as_of_date,
            currency=request.currency
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ar-aging", status_code=status.HTTP_200_OK)
async def generate_ar_aging(
    request: ARAgingRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate AR Aging report"""
    service = ARAgingService(db)
    try:
        report = await service.generate_ar_aging(
            entity_id=request.entity_id,
            as_of_date=request.as_of_date,
            aging_buckets=request.aging_buckets
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gl-detail", status_code=status.HTTP_200_OK)
async def generate_gl_detail(
    request: GLDetailRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate GL Detail report"""
    service = GLDetailService(db)
    try:
        report = await service.generate_gl_detail(
            book_id=request.book_id,
            account_id=request.account_id,
            account_code=request.account_code,
            period_start=request.period_start,
            period_end=request.period_end,
            period_id=request.period_id,
            include_dimensions=request.include_dimensions
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Convenience GET endpoints with query parameters
@router.get("/trial-balance", status_code=status.HTTP_200_OK)
async def get_trial_balance(
    book_id: UUID = Query(...),
    period_id: Optional[UUID] = Query(None),
    as_of_date: Optional[date] = Query(None),
    include_zero_balance: bool = Query(False),
    db: AsyncSession = Depends(get_db_session)
):
    """Get Trial Balance report (GET)"""
    request = TrialBalanceRequest(
        book_id=book_id,
        period_id=period_id,
        as_of_date=as_of_date,
        include_zero_balance=include_zero_balance
    )
    return await generate_trial_balance(request, db)


@router.get("/profit-loss", status_code=status.HTTP_200_OK)
async def get_profit_loss(
    book_id: UUID = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    compare_previous: bool = Query(False),
    db: AsyncSession = Depends(get_db_session)
):
    """Get Profit & Loss report (GET)"""
    request = ProfitLossRequest(
        book_id=book_id,
        period_start=period_start,
        period_end=period_end,
        compare_previous=compare_previous
    )
    return await generate_profit_loss(request, db)


@router.get("/balance-sheet", status_code=status.HTTP_200_OK)
async def get_balance_sheet(
    book_id: UUID = Query(...),
    as_of_date: date = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Get Balance Sheet report (GET)"""
    request = BalanceSheetRequest(
        book_id=book_id,
        as_of_date=as_of_date
    )
    return await generate_balance_sheet(request, db)
