"""Intercompany Transfer API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List, Optional
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import IC_TRANSFER_POST
from app.modules.intercompany.services.intercompany_transfer_service import IntercompanyTransferService
from app.modules.intercompany.schemas.intercompany_schemas import (
    IntercompanyTransferCreate,
    IntercompanyTransferPostRequest,
    IntercompanyTransferResponse
)
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/intercompany/transfers", tags=["Intercompany Transfers"], dependencies=[Depends(get_user_context)])


@router.post("", response_model=IntercompanyTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_intercompany_transfer(
    transfer: IntercompanyTransferCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create intercompany transfer"""
    service = IntercompanyTransferService(db)
    try:
        created = await service.create_transfer(
            from_entity_id=transfer.from_entity_id,
            to_entity_id=transfer.to_entity_id,
            transfer_date=transfer.transfer_date,
            amount=transfer.amount,
            currency=transfer.currency,
            transfer_type=transfer.transfer_type,
            description=transfer.description,
            reference_number=transfer.reference_number,
            from_bank_account_id=transfer.from_bank_account_id,
            to_bank_account_id=transfer.to_bank_account_id
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{transfer_id}/post", status_code=status.HTTP_200_OK)
async def post_intercompany_transfer(
    transfer_id: UUID,
    request: IntercompanyTransferPostRequest,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Post intercompany transfer to both entities' books"""
    service = IntercompanyTransferService(db)
    
    # Get transfer to retrieve entity_id
    transfer = await service.transfer_repo.get_by_id(transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Intercompany transfer not found")
    
    # Use from_entity_id as primary scope (where the primary journal entry is created)
    legal_entity_id = transfer.from_entity_id
    
    # Get ACCRUAL book for from_entity (for idempotency scope)
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    from app.modules.general_ledger.models.book_model import BookType
    book_repo = BookRepository(db)
    from_book = await book_repo.get_by_entity_and_type(legal_entity_id, BookType.ACCRUAL)
    if not from_book:
        raise HTTPException(status_code=404, detail="ACCRUAL book not found for from entity")
    
    book_id = from_book.id
    actor_user_id = request.posted_by
    
    # Handler function
    async def handler():
        from_je_id, to_je_id = await service.post_transfer(transfer_id, request.posted_by)
        return {
            "transfer_id": str(transfer_id),
            "from_entity_je_id": str(from_je_id),
            "to_entity_je_id": str(to_je_id),
            "status": "posted"
        }
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=IC_TRANSFER_POST,
            request_body=request.model_dump() if hasattr(request, 'model_dump') else {"posted_by": str(request.posted_by)},
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[IntercompanyTransferResponse])
async def list_intercompany_transfers(
    from_entity_id: UUID | None = Query(None),
    to_entity_id: UUID | None = Query(None),
    entity_id: UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """List intercompany transfers"""
    service = IntercompanyTransferService(db)
    
    if from_entity_id and to_entity_id:
        transfers = await service.transfer_repo.list_by_entity_pair(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
    elif entity_id:
        transfers = await service.transfer_repo.list_by_entity(
            entity_id=entity_id,
            limit=limit,
            offset=offset
        )
    else:
        transfers = []
    
    return transfers


@router.get("/{transfer_id}", response_model=IntercompanyTransferResponse)
async def get_intercompany_transfer(
    transfer_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get intercompany transfer by ID"""
    service = IntercompanyTransferService(db)
    transfer = await service.transfer_repo.get_by_id(transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Intercompany transfer not found")
    return transfer


@router.get("/balance")
async def get_intercompany_balance(
    from_entity_id: UUID,
    to_entity_id: UUID,
    as_of_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Get intercompany balance"""
    service = IntercompanyTransferService(db)
    from app.modules.intercompany.services.intercompany_reconciliation_service import IntercompanyReconciliationService
    recon_service = IntercompanyReconciliationService(db)
    
    as_of = as_of_date or date.today()
    balance = await recon_service.calculate_balance(
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
