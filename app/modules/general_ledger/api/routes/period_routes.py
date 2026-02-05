"""Accounting Period API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import PERIOD_LOCK
from app.modules.general_ledger.services.period_service import PeriodService
from app.modules.general_ledger.services.period_close_approval_service import (
    PeriodCloseApprovalService,
    PeriodCloseApprovalError
)
from app.modules.general_ledger.services.period_close_checklist_service import (
    PeriodCloseChecklistService
)
from app.modules.general_ledger.schemas.period_schemas import (
    PeriodGenerateRequest,
    PeriodCloseRequest,
    PeriodLockRequest,
    AccountingPeriodResponse,
    PeriodCloseSubmitRequest,
    PeriodCloseApproveRequest,
    PeriodCloseChecklistItemResponse,
    PeriodCloseChecklistMarkCompleteRequest
)
from app.modules.general_ledger.models.period_close_checklist_model import ChecklistItemCode
from app.modules.general_ledger.models.accounting_period_model import PeriodStatus
from app.core.exceptions import NotFoundError, ValidationError, PeriodLockedError
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/books/{book_id}/periods", tags=["Accounting Periods"])


@router.post("/generate", response_model=List[AccountingPeriodResponse], status_code=status.HTTP_201_CREATED)
async def generate_periods(
    book_id: UUID,
    request: PeriodGenerateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate accounting periods for a book"""
    service = PeriodService(db)
    try:
        periods = await service.generate_periods(
            book_id=book_id,
            start_year=request.start_year,
            start_month=request.start_month,
            num_months=request.num_months
        )
        return periods
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[AccountingPeriodResponse])
async def list_periods(
    book_id: UUID,
    status: Optional[PeriodStatus] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """List periods for a book"""
    service = PeriodService(db)
    periods = await service.list_periods(book_id, status=status)
    return periods


@router.get("/{period_id}", response_model=AccountingPeriodResponse)
async def get_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get period by ID"""
    service = PeriodService(db)
    period = await service.get_period(period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    return period


@router.post("/{period_id}/close", response_model=AccountingPeriodResponse)
async def close_period(
    period_id: UUID,
    request: PeriodCloseRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Close an accounting period"""
    service = PeriodService(db)
    try:
        period = await service.close_period(
            period_id=period_id,
            closed_by=request.closed_by,
            reason=request.reason
        )
        return period
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PeriodLockedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{period_id}/submit-close", response_model=AccountingPeriodResponse)
async def submit_period_close(
    period_id: UUID,
    request: PeriodCloseSubmitRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Submit period for close approval"""
    approval_service = PeriodCloseApprovalService(db)
    try:
        submitted = await approval_service.submit_close(
            period_id=period_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return submitted
    except PeriodCloseApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{period_id}/approve-close", response_model=AccountingPeriodResponse)
async def approve_period_close(
    period_id: UUID,
    request: PeriodCloseApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Approve period close"""
    approval_service = PeriodCloseApprovalService(db)
    try:
        approved = await approval_service.approve_close(
            period_id=period_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            override_reason=request.override_reason,
            row_version=request.row_version
        )
        return approved
    except PeriodCloseApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{period_id}/lock", response_model=AccountingPeriodResponse)
async def lock_period(
    book_id: UUID,
    period_id: UUID,
    request: PeriodLockRequest,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Lock an accounting period"""
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    
    service = PeriodService(db)
    
    # Verify period belongs to book
    period = await service.period_repo.get_by_id(period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Accounting period not found")
    if period.book_id != book_id:
        raise HTTPException(status_code=400, detail="Period does not belong to this book")
    
    # Get legal_entity_id from book
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    legal_entity_id = book.legal_entity_id
    actor_user_id = request.locked_by
    
    # Handler function
    async def handler():
        period = await service.lock_period(
            period_id=period_id,
            locked_by=request.locked_by,
            reason=request.reason
        )
        return period
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=PERIOD_LOCK,
            request_body=request.model_dump() if hasattr(request, 'model_dump') else {"locked_by": str(request.locked_by), "reason": request.reason},
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Period Close Checklist Endpoints
@router.get("/{period_id}/checklist", response_model=List[PeriodCloseChecklistItemResponse])
async def get_period_checklist(
    period_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get period close checklist"""
    checklist_service = PeriodCloseChecklistService(db)
    try:
        checklist = await checklist_service.get_checklist(period_id)
        return checklist
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{period_id}/checklist/compute", response_model=List[PeriodCloseChecklistItemResponse])
async def compute_period_checklist(
    period_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Compute period close checklist"""
    checklist_service = PeriodCloseChecklistService(db)
    try:
        checklist = await checklist_service.compute_checklist(
            period_id=period_id,
            computed_by=user.get("user_id")
        )
        return checklist
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{period_id}/checklist/{item_code}/complete", response_model=PeriodCloseChecklistItemResponse)
async def mark_checklist_item_complete(
    period_id: UUID,
    item_code: ChecklistItemCode,
    request: PeriodCloseChecklistMarkCompleteRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Manually mark a checklist item as complete"""
    checklist_service = PeriodCloseChecklistService(db)
    try:
        item = await checklist_service.mark_item_complete(
            period_id=period_id,
            item_code=item_code,
            notes=request.notes,
            user_id=user.get("user_id")
        )
        return item
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
