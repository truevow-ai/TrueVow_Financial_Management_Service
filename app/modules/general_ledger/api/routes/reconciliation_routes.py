"""Reconciliation API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import RECONCILIATION_CLOSE, RECONCILIATION_ADJ_POST
from app.modules.general_ledger.services.reconciliation_service import ReconciliationService
from app.modules.general_ledger.services.reconciliation_approval_service import (
    ReconciliationApprovalService,
    ReconciliationApprovalError
)
from app.modules.general_ledger.services.reconciliation_adjustment_posting_service import (
    ReconciliationAdjustmentPostingService
)
from app.modules.general_ledger.services.reconciliation_matching_service import (
    ReconciliationMatchingService,
    MatchSuggestion
)
from app.modules.general_ledger.schemas.reconciliation_schemas import (
    ReconciliationSessionCreate,
    ReconciliationMatchCreate,
    ReconciliationCloseRequest,
    ReconciliationSessionResponse,
    ReconciliationMatchResponse,
    ReconciliationAdjustmentSubmitRequest,
    ReconciliationAdjustmentApproveRequest,
    ReconciliationAdjustmentRejectRequest,
    ReconciliationAdjustmentPostRequest,
    MatchSuggestionResponse
)
from app.modules.general_ledger.models.reconciliation_model import ReconciliationStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.middleware import get_current_user
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/books/{book_id}/reconciliations", tags=["Bank Reconciliation"], dependencies=[Depends(get_user_context)])


@router.post("", response_model=ReconciliationSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_reconciliation(
    session: ReconciliationSessionCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a reconciliation session"""
    service = ReconciliationService(db)
    try:
        created = await service.create_session(
            bank_account_id=session.bank_account_id,
            period_start=session.period_start,
            period_end=session.period_end,
            statement_ending_balance=session.statement_ending_balance,
            statement_currency=session.statement_currency
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[ReconciliationSessionResponse])
async def list_reconciliations(
    book_id: UUID,
    bank_account_id: UUID,
    status: Optional[ReconciliationStatus] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List reconciliation sessions for a bank account"""
    service = ReconciliationService(db)
    sessions = await service.list_sessions(bank_account_id, status=status)
    return sessions


@router.get("/{session_id}", response_model=ReconciliationSessionResponse)
async def get_reconciliation(
    book_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get reconciliation session by ID"""
    service = ReconciliationService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Reconciliation session not found")
    
    # Load matches
    from app.modules.general_ledger.repositories.reconciliation_repository import ReconciliationMatchRepository
    match_repo = ReconciliationMatchRepository(db)
    matches = await match_repo.list_by_session(session_id)
    session.matches = matches
    
    return session


@router.post("/{session_id}/match", response_model=ReconciliationMatchResponse, status_code=status.HTTP_201_CREATED)
async def match_transaction(
    session_id: UUID,
    match: ReconciliationMatchCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Match a bank transaction to a journal entry"""
    service = ReconciliationService(db)
    try:
        created = await service.match_transaction(
            session_id=session_id,
            bank_transaction_id=match.bank_transaction_id,
            journal_entry_id=match.journal_entry_id,
            match_type=match.match_type,
            notes=match.notes
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/calculate-difference")
async def calculate_difference(
    book_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Calculate reconciliation difference"""
    service = ReconciliationService(db)
    try:
        difference = await service.calculate_difference(session_id)
        return {"difference": float(difference), "session_id": str(session_id)}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{session_id}/close", response_model=ReconciliationSessionResponse)
async def close_reconciliation(
    book_id: UUID,
    session_id: UUID,
    request: ReconciliationCloseRequest,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Close a reconciliation session (does NOT post adjustments - separate endpoint required)"""
    service = ReconciliationService(db)
    
    # Get session to verify it exists and get bank_account
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Reconciliation session not found")
    
    # Get book_id from bank account
    from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
    bank_account_repo = BankAccountRepository(db)
    bank_account = await bank_account_repo.get_by_id(session.bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    # Verify bank account's book_id matches
    if bank_account.book_id != book_id:
        raise HTTPException(status_code=400, detail="Reconciliation session does not belong to this book")
    
    # Get legal_entity_id from book
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    legal_entity_id = book.legal_entity_id
    actor_user_id = request.reconciled_by
    
    # Handler function
    async def handler():
        closed = await service.close_session(
            session_id=session_id,
            reconciled_by=request.reconciled_by,
            notes=request.notes,
            allow_non_zero=request.allow_non_zero
        )
        return closed
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=RECONCILIATION_CLOSE,
            request_body=request.model_dump() if hasattr(request, 'model_dump') else {"reconciled_by": str(request.reconciled_by), "notes": request.notes, "allow_non_zero": request.allow_non_zero},
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Reconciliation Adjustment Approval Endpoints
@router.post("/{rec_id}/adjustments/submit-approval")
async def submit_adjustment_for_approval(
    rec_id: UUID,
    request: ReconciliationAdjustmentSubmitRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Submit reconciliation adjustment batch for approval"""
    approval_service = ReconciliationApprovalService(db)
    try:
        # Get batch ID from reconciliation session
        # TODO: Implement batch lookup from reconciliation session
        batch_id = request.batch_id
        submitted = await approval_service.submit_for_approval(
            batch_id=batch_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return submitted
    except ReconciliationApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{rec_id}/adjustments/approve")
async def approve_adjustment(
    book_id: UUID,
    rec_id: UUID,
    request: ReconciliationAdjustmentApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Approve reconciliation adjustment batch"""
    approval_service = ReconciliationApprovalService(db)
    try:
        batch_id = request.batch_id
        approved = await approval_service.approve(
            batch_id=batch_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            override_reason=request.override_reason,
            row_version=request.row_version
        )
        return approved
    except ReconciliationApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{rec_id}/adjustments/reject")
async def reject_adjustment(
    rec_id: UUID,
    request: ReconciliationAdjustmentRejectRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Reject reconciliation adjustment batch"""
    approval_service = ReconciliationApprovalService(db)
    try:
        batch_id = request.batch_id
        rejected = await approval_service.reject(
            batch_id=batch_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return rejected
    except ReconciliationApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{rec_id}/adjustments/post", status_code=status.HTTP_200_OK)
async def post_adjustment(
    book_id: UUID,
    rec_id: UUID,
    request: ReconciliationAdjustmentPostRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Post reconciliation adjustment batch to journal entry"""
    from app.modules.general_ledger.repositories.reconciliation_adjustment_batch_repository import (
        ReconciliationAdjustmentBatchRepository
    )
    
    posting_service = ReconciliationAdjustmentPostingService(db)
    
    # Get batch to verify it exists and get legal_entity_id
    batch_repo = ReconciliationAdjustmentBatchRepository(db)
    batch = await batch_repo.get_by_id(request.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Reconciliation adjustment batch not found")
    
    # Verify batch belongs to book
    if batch.book_id != book_id:
        raise HTTPException(status_code=400, detail="Adjustment batch does not belong to this book")
    
    legal_entity_id = batch.legal_entity_id
    actor_user_id = UUID(user.get("user_id")) if user.get("user_id") else request.posted_by
    
    # Handler function
    async def handler():
        entry_id = await posting_service.post_adjustment_batch(
            batch_id=request.batch_id,
            posted_by=actor_user_id,
            row_version=request.row_version
        )
        return {
            "batch_id": str(request.batch_id),
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
            endpoint_key=RECONCILIATION_ADJ_POST,
            request_body=request.model_dump() if hasattr(request, 'model_dump') else {
                "batch_id": str(request.batch_id),
                "posted_by": str(request.posted_by),
                "row_version": request.row_version
            },
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Reconciliation Matching Suggestions Endpoint
@router.get("/{session_id}/transactions/{transaction_id}/suggestions", response_model=List[MatchSuggestionResponse])
async def get_matching_suggestions(
    book_id: UUID,
    session_id: UUID,
    transaction_id: UUID,
    top_n: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db_session)
):
    """Get matching suggestions for a bank transaction in a reconciliation session"""
    matching_service = ReconciliationMatchingService(db)
    try:
        suggestions = await matching_service.suggest_matches(
            bank_transaction_id=transaction_id,
            reconciliation_session_id=session_id,
            max_suggestions=top_n
        )
        # Convert MatchSuggestion objects to response format
        return [
            MatchSuggestionResponse(
                journal_entry_id=s.journal_entry_id,
                journal_entry_number=s.journal_entry_number,
                entry_date=s.entry_date,
                total_amount=s.total_amount,
                memo=s.memo,
                reference=s.reference,
                confidence=s.confidence,
                match_reasons=s.match_reasons
            )
            for s in suggestions
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
