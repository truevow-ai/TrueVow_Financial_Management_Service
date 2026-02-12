"""AP Bill API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import AP_BILL_POST
from app.modules.ap.services.ap_bill_service import APBillService
from app.modules.ap.services.ap_bill_approval_service import (
    APBillApprovalService,
    APBillApprovalError
)
from app.modules.ap.services.ap_bill_posting_service import APBillPostingService
from app.modules.ap.schemas.ap_bill_schemas import (
    APBillCreate,
    APBillResponse,
    APBillLineCreate,
    APBillSubmitApprovalRequest,
    APBillApproveRequest,
    APBillRejectRequest,
    APBillPostRequest
)
from app.modules.ap.models.ap_bill_model import BillStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/books/{book_id}/ap/bills", tags=["AP Bills"])


@router.post("", response_model=APBillResponse, status_code=status.HTTP_201_CREATED)
async def create_ap_bill(
    book_id: UUID,
    bill: APBillCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Create a new AP bill"""
    service = APBillService(db)
    try:
        created = await service.create_bill(
            legal_entity_id=bill.legal_entity_id,
            book_id=book_id,
            vendor_id=bill.ap_vendor_id,
            bill_number=bill.bill_number,
            bill_date=bill.bill_date,
            due_date=bill.due_date,
            currency=bill.currency,
            description=bill.description,
            reference_number=bill.reference_number,
            created_by=user.get("user_id")
        )
        
        # Add lines
        for line_data in bill.lines:
            await service.add_line(
                bill_id=created.id,
                gl_account_id=line_data.gl_account_id,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                line_number=line_data.line_number,
                currency=line_data.currency,
                tax_code=line_data.tax_code,
                created_by=user.get("user_id")
            )
        
        await db.commit()
        
        # Reload with lines
        from app.modules.ap.repositories.ap_bill_line_repository import APBillLineRepository
        line_repo = APBillLineRepository(db)
        lines = await line_repo.list_by_bill(created.id)
        created.lines = lines
        
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[APBillResponse])
async def list_ap_bills(
    book_id: UUID,
    vendor_id: Optional[UUID] = Query(None),
    status: Optional[BillStatus] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List AP bills for a book"""
    service = APBillService(db)
    # Get entity_id from book (would need book lookup)
    # For now, assume book_id is sufficient
    bills = await service.list_bills(
        entity_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: Get from book
        book_id=book_id,
        vendor_id=vendor_id,
        status=status
    )
    return bills


@router.get("/{bill_id}", response_model=APBillResponse)
async def get_ap_bill(
    bill_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get AP bill by ID"""
    service = APBillService(db)
    bill = await service.get_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="AP bill not found")
    
    # Load lines
    from app.modules.ap.repositories.ap_bill_line_repository import APBillLineRepository
    line_repo = APBillLineRepository(db)
    lines = await line_repo.list_by_bill(bill_id)
    bill.lines = lines
    
    return bill


@router.post("/{bill_id}/submit-approval", response_model=APBillResponse)
async def submit_bill_for_approval(
    bill_id: UUID,
    request: APBillSubmitApprovalRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Submit AP bill for approval"""
    approval_service = APBillApprovalService(db)
    try:
        submitted = await approval_service.submit_for_approval(
            bill_id=bill_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return submitted
    except APBillApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{bill_id}/approve", response_model=APBillResponse)
async def approve_bill(
    bill_id: UUID,
    request: APBillApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Approve AP bill"""
    approval_service = APBillApprovalService(db)
    try:
        approved = await approval_service.approve(
            bill_id=bill_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            override_reason=request.override_reason,
            row_version=request.row_version
        )
        return approved
    except APBillApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{bill_id}/reject", response_model=APBillResponse)
async def reject_bill(
    bill_id: UUID,
    request: APBillRejectRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user)
):
    """Reject AP bill"""
    approval_service = APBillApprovalService(db)
    try:
        rejected = await approval_service.reject(
            bill_id=bill_id,
            user_id=user["user_id"],
            user_role=user.get("roles", [""])[0] if user.get("roles") else "",
            reason=request.reason,
            row_version=request.row_version
        )
        return rejected
    except APBillApprovalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{bill_id}/post", response_model=APBillResponse)
async def post_bill(
    book_id: UUID,
    bill_id: UUID,
    request: APBillPostRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Post AP bill to journal"""
    service = APBillService(db)
    bill = await service.get_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="AP bill not found")
    
    if bill.book_id != book_id:
        raise HTTPException(status_code=400, detail="AP bill does not belong to this book")
    
    # Check row_version before posting
    from app.core.row_version import check_row_version
    check_row_version(bill.row_version, request.row_version, "AP bill")
    
    # Get legal_entity_id from bill
    legal_entity_id = bill.legal_entity_id
    actor_user_id = UUID(user.get("user_id")) if user.get("user_id") else None
    
    # Handler function
    async def handler():
        posting_service = APBillPostingService(db)
        entry_id = await posting_service.post_bill(
            bill_id=bill_id,
            posted_by=actor_user_id,
            row_version=request.row_version
        )
        
        # Return updated bill
        service = APBillService(db)
        bill = await service.get_bill(bill_id)
        if not bill:
            raise HTTPException(status_code=404, detail="AP bill not found")
        
        # Load lines
        from app.modules.ap.repositories.ap_bill_line_repository import APBillLineRepository
        line_repo = APBillLineRepository(db)
        lines = await line_repo.list_by_bill(bill_id)
        bill.lines = lines
        
        return bill
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=AP_BILL_POST,
            request_body=request.model_dump(),
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
