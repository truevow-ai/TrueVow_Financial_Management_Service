"""Royalty API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import ROYALTY_POST
from app.modules.intercompany.services.royalty_calculation_service import RoyaltyCalculationService
from app.modules.intercompany.services.royalty_approval_service import (
    RoyaltyApprovalService,
    RoyaltyApprovalError
)
from app.modules.intercompany.repositories.royalty_repository import RoyaltyAgreementRepository
from app.modules.intercompany.schemas.intercompany_schemas import (
    RoyaltyAgreementCreate,
    RoyaltyCalculationRequest,
    RoyaltyCalculationPostRequest,
    RoyaltyAgreementResponse,
    RoyaltyCalculationResponse,
    RoyaltyRunSubmitApprovalRequest,
    RoyaltyRunApproveRequest,
    RoyaltyRunRejectRequest
)
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/intercompany/royalties", tags=["Royalties"])


@router.post("/agreements", response_model=RoyaltyAgreementResponse, status_code=status.HTTP_201_CREATED)
async def create_royalty_agreement(
    agreement: RoyaltyAgreementCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create royalty agreement"""
    repo = RoyaltyAgreementRepository(db)
    
    # Check if code exists
    existing = await repo.get_by_code(agreement.agreement_code)
    if existing:
        raise HTTPException(status_code=400, detail="Agreement code already exists")
    
    # Validate fixed amount if basis is FIXED
    if agreement.basis.value == "FIXED" and not agreement.fixed_amount:
        raise HTTPException(status_code=400, detail="Fixed amount required for FIXED basis")
    
    try:
        created = await repo.create(
            from_entity_id=agreement.from_entity_id,
            to_entity_id=agreement.to_entity_id,
            agreement_code=agreement.agreement_code,
            agreement_name=agreement.agreement_name,
            basis=agreement.basis,
            rate=agreement.rate,
            fixed_amount=agreement.fixed_amount,
            effective_from=agreement.effective_from,
            effective_to=agreement.effective_to,
            currency=agreement.currency,
            description=agreement.description,
            is_active=True
        )
        await db.commit()
        return created
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agreements", response_model=List[RoyaltyAgreementResponse])
async def list_royalty_agreements(
    from_entity_id: UUID | None = Query(None),
    to_entity_id: UUID | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db_session)
):
    """List royalty agreements"""
    repo = RoyaltyAgreementRepository(db)
    
    if from_entity_id and to_entity_id:
        agreements = await repo.list_by_entity_pair(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            active_only=active_only
        )
    else:
        # List all (would need a general list method)
        agreements = []
    
    return agreements


@router.get("/agreements/{agreement_id}", response_model=RoyaltyAgreementResponse)
async def get_royalty_agreement(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get royalty agreement by ID"""
    repo = RoyaltyAgreementRepository(db)
    agreement = await repo.get_by_id(agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="Royalty agreement not found")
    return agreement


@router.post("/calculate", response_model=RoyaltyCalculationResponse, status_code=status.HTTP_201_CREATED)
async def calculate_royalty(
    request: RoyaltyCalculationRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Calculate royalty for a period"""
    service = RoyaltyCalculationService(db)
    try:
        calculation = await service.calculate_royalty(
            agreement_id=request.agreement_id,
            period_start=request.period_start,
            period_end=request.period_end
        )
        return calculation
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/submit-approval", response_model=RoyaltyCalculationResponse)
async def submit_royalty_run_for_approval(
    run_id: UUID,
    request: RoyaltyRunSubmitApprovalRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Submit royalty run for approval"""
    approval_service = RoyaltyApprovalService(db)
    try:
        submitted = await approval_service.submit_for_approval(
            run_id=run_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return submitted
    except RoyaltyApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs/{run_id}/approve", response_model=RoyaltyCalculationResponse)
async def approve_royalty_run(
    run_id: UUID,
    request: RoyaltyRunApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Approve royalty run"""
    approval_service = RoyaltyApprovalService(db)
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
    except RoyaltyApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs/{run_id}/reject", response_model=RoyaltyCalculationResponse)
async def reject_royalty_run(
    run_id: UUID,
    request: RoyaltyRunRejectRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Reject royalty run"""
    approval_service = RoyaltyApprovalService(db)
    try:
        rejected = await approval_service.reject(
            run_id=run_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return rejected
    except RoyaltyApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/calculations/{calculation_id}/post", status_code=status.HTTP_200_OK)
async def post_royalty_calculation(
    calculation_id: UUID,
    request: RoyaltyCalculationPostRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Post royalty calculation as intercompany transfer"""
    service = RoyaltyCalculationService(db)
    
    # Get calculation to retrieve entity_id
    calculation = await service.calc_repo.get_by_id(calculation_id)
    if not calculation:
        raise HTTPException(status_code=404, detail="Royalty calculation not found")
    
    # Get from_entity_id from agreement (this is the primary entity for idempotency scope)
    legal_entity_id = calculation.agreement.from_entity_id
    
    # Get ACCRUAL book for from_entity (for idempotency scope)
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    from app.modules.general_ledger.models.book_model import BookType
    book_repo = BookRepository(db)
    from_book = await book_repo.get_by_entity_and_type(legal_entity_id, BookType.ACCRUAL)
    if not from_book:
        raise HTTPException(status_code=404, detail="ACCRUAL book not found for entity")
    
    book_id = from_book.id
    actor_user_id = UUID(user.get("user_id")) if user.get("user_id") else None
    
    # Handler function
    async def handler():
        je_id = await service.post_royalty(calculation_id, user["user_id"])
        return {
            "calculation_id": str(calculation_id),
            "journal_entry_id": str(je_id),
            "status": "posted"
        }
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=ROYALTY_POST,
            request_body=request.model_dump() if hasattr(request, 'model_dump') else {},
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calculations/unposted", response_model=List[RoyaltyCalculationResponse])
async def list_unposted_calculations(
    entity_id: UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
):
    """List unposted royalty calculations"""
    from app.modules.intercompany.repositories.royalty_repository import RoyaltyCalculationRepository
    repo = RoyaltyCalculationRepository(db)
    calculations = await repo.list_unposted(entity_id=entity_id, limit=limit)
    return calculations
