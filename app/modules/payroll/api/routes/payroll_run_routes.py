"""Payroll Run API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import PAYROLL_POST, PAYROLL_REVERSE
from app.modules.payroll.services.payroll_run_service import PayrollRunService
from app.modules.payroll.services.payroll_approval_service import PayrollApprovalService, PayrollApprovalError
from app.modules.payroll.schemas.payroll_run_schemas import (
    PayrollRunCreate,
    PayrollRunApproveRequest,
    PayrollRunPostRequest,
    PayrollRunResponse,
    PayrollRunItemResponse,
    PayrollRunSubmitApprovalRequest,
    PayrollRunRejectRequest,
    PayrollRunReverseRequest
)
from app.modules.payroll.models.payroll_run_model import PayrollRunStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/books/{book_id}/payroll", tags=["Payroll Runs"])


@router.post("/runs", response_model=PayrollRunResponse, status_code=status.HTTP_201_CREATED)
async def create_payroll_run(
    book_id: UUID,
    run: PayrollRunCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new payroll run"""
    service = PayrollRunService(db)
    try:
        created = await service.create_run(
            entity_id=run.entity_id,
            book_id=book_id,
            pay_group_id=run.pay_group_id,
            pay_period_start=run.pay_period_start,
            pay_period_end=run.pay_period_end,
            pay_date=run.pay_date
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/calculate", response_model=PayrollRunResponse)
async def calculate_payroll_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Calculate payroll run"""
    service = PayrollRunService(db)
    try:
        calculated = await service.calculate_run(run_id)
        return calculated
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/submit-approval", response_model=PayrollRunResponse)
async def submit_payroll_run_for_approval(
    run_id: UUID,
    request: PayrollRunSubmitApprovalRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Submit payroll run for approval"""
    approval_service = PayrollApprovalService(db)
    try:
        submitted = await approval_service.submit_for_approval(
            run_id=run_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return submitted
    except PayrollApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs/{run_id}/approve", response_model=PayrollRunResponse)
async def approve_payroll_run(
    run_id: UUID,
    request: PayrollRunApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Approve payroll run"""
    approval_service = PayrollApprovalService(db)
    try:
        approved = await approval_service.approve(
            run_id=run_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            override_reason=request.override_reason,
            row_version=request.row_version
        )
        return approved
    except PayrollApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs/{run_id}/reject", response_model=PayrollRunResponse)
async def reject_payroll_run(
    run_id: UUID,
    request: PayrollRunRejectRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Reject payroll run"""
    approval_service = PayrollApprovalService(db)
    try:
        rejected = await approval_service.reject(
            run_id=run_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return rejected
    except PayrollApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs/{run_id}/post", status_code=status.HTTP_200_OK)
async def post_payroll_run(
    book_id: UUID,
    run_id: UUID,
    request: PayrollRunPostRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Post payroll run to ACCRUAL book"""
    service = PayrollRunService(db)
    
    # Verify run belongs to book
    run = await service.run_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    if run.book_id != book_id:
        raise HTTPException(status_code=400, detail="Payroll run does not belong to this book")
    
    # Get legal_entity_id from run
    legal_entity_id = run.legal_entity_id
    
    # Use user_id from token
    posted_by = UUID(user.get("user_id")) if user.get("user_id") else None
    if not posted_by:
        raise HTTPException(status_code=400, detail="User ID required")
    actor_user_id = posted_by
    
    # Handler function
    async def handler():
        entry_id = await service.post_run(
            run_id=run_id,
            posted_by=posted_by,
            row_version=request.row_version
        )
        return {
            "payroll_run_id": str(run_id),
            "journal_entry_id": str(entry_id),
            "status": "posted"
        }
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=PAYROLL_POST,
            request_body=request.model_dump(),
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/reverse", response_model=PayrollRunResponse)
async def reverse_payroll_run(
    book_id: UUID,
    run_id: UUID,
    request: PayrollRunReverseRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Reverse a posted payroll run (FINANCE_ADMIN only)"""
    service = PayrollRunService(db)
    
    # Verify run belongs to book
    run = await service.run_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    if run.book_id != book_id:
        raise HTTPException(status_code=400, detail="Payroll run does not belong to this book")
    
    # Get legal_entity_id from run
    legal_entity_id = run.legal_entity_id
    
    # Check user role (FINANCE_ADMIN only)
    user_roles = user.get("roles", [])
    if "FINANCE_ADMIN" not in user_roles:
        raise HTTPException(
            status_code=403,
            detail="Only FINANCE_ADMIN can reverse payroll runs"
        )
    
    # Use user_id from token
    reversed_by = UUID(user.get("user_id")) if user.get("user_id") else None
    if not reversed_by:
        raise HTTPException(status_code=400, detail="User ID required")
    actor_user_id = reversed_by
    
    # Handler function
    async def handler():
        reversed_run = await service.reverse_run(
            run_id=run_id,
            reversed_by=reversed_by,
            reason=request.reason,
            reversal_date=request.reversal_date
        )
        return reversed_run
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=PAYROLL_REVERSE,
            request_body=request.model_dump(),
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs", response_model=List[PayrollRunResponse])
async def list_payroll_runs(
    book_id: UUID,
    entity_id: UUID,
    status: Optional[PayrollRunStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """List payroll runs"""
    service = PayrollRunService(db)
    runs = await service.run_repo.list_by_entity(
        entity_id=entity_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return runs


@router.get("/runs/{run_id}", response_model=PayrollRunResponse)
async def get_payroll_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get payroll run by ID"""
    service = PayrollRunService(db)
    run = await service.run_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    # Load items
    items = await service.item_repo.list_by_run(run_id)
    run.items = items
    
    return run
