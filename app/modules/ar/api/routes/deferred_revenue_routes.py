"""Deferred Revenue API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List
from app.core.database import get_db_session
from app.modules.ar.services.deferred_revenue_service import DeferredRevenueService
from app.modules.ar.schemas.deferred_revenue_schemas import (
    RevenueRecognitionRequest,
    RevenueScheduleResponse,
    RevenueSchedulePeriodResponse
)
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/books/{book_id}/revrec", tags=["Deferred Revenue"], dependencies=[Depends(get_user_context)])


@router.post("/schedules/{invoice_line_id}", response_model=RevenueScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_revenue_schedule(
    book_id: UUID,
    invoice_line_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Create revenue schedule from invoice line"""
    service = DeferredRevenueService(db)
    try:
        schedule = await service.create_schedule_from_invoice_line(
            invoice_line_id=invoice_line_id,
            book_id=book_id
        )
        return schedule
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedules", response_model=List[RevenueScheduleResponse])
async def list_revenue_schedules(
    book_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """List revenue schedules for a book"""
    service = DeferredRevenueService(db)
    schedules = await service.schedule_repo.list_active_by_book(book_id)
    return schedules


@router.post("/run", status_code=status.HTTP_200_OK)
async def run_revenue_recognition(
    book_id: UUID,
    request: RevenueRecognitionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Run revenue recognition for a period"""
    service = DeferredRevenueService(db)
    try:
        recognized_count, entry_ids = await service.run_revenue_recognition(
            book_id=book_id,
            period_start=request.period_start,
            period_end=request.period_end,
            posted_by=request.posted_by
        )
        return {
            "recognized_count": recognized_count,
            "journal_entry_ids": [str(eid) for eid in entry_ids],
            "period_start": request.period_start,
            "period_end": request.period_end
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
