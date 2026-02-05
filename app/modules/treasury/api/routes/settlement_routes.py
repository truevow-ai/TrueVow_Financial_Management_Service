"""Settlement API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List, Optional
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import SETTLEMENT_CREATE, SETTLEMENT_STRIPE_IMPORT, SETTLEMENT_TELR_IMPORT
from app.modules.treasury.services.settlement_service import SettlementService
from app.modules.treasury.schemas.settlement_schemas import (
    SettlementCreate,
    SettlementImport,
    SettlementResponse
)
from app.modules.treasury.models.settlement_model import SettlementSource
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError

router = APIRouter(prefix="/settlements", tags=["Settlements"])


@router.post("", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def create_settlement(
    settlement: SettlementCreate,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Create a settlement"""
    from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
    
    service = SettlementService(db)
    
    # Get bank_account to retrieve book_id
    # Note: BankAccount model may need book_id field added
    # For now, get book_id from CASH book for the entity
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    from app.modules.general_ledger.models.book_model import BookType
    
    bank_account_repo = BankAccountRepository(db)
    bank_account = await bank_account_repo.get_by_id(settlement.bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    legal_entity_id = settlement.legal_entity_id
    
    # Get CASH book for entity (settlements post to CASH book)
    book_repo = BookRepository(db)
    cash_book = await book_repo.get_by_entity_and_type(legal_entity_id, BookType.CASH)
    if not cash_book:
        raise HTTPException(status_code=404, detail="CASH book not found for entity")
    book_id = cash_book.id
    actor_user_id = None  # System-initiated
    
    # Handler function
    async def handler():
        created = await service.create_settlement(
            legal_entity_id=settlement.legal_entity_id,
            bank_account_id=settlement.bank_account_id,
            settlement_date=settlement.settlement_date,
            source=settlement.source,
            gross_amount=settlement.gross_amount,
            fees=settlement.fees,
            net_amount=settlement.net_amount,
            currency=settlement.currency,
            external_settlement_id=settlement.external_settlement_id,
            external_payout_id=settlement.external_payout_id,
            description=settlement.description
        )
        return created
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=SETTLEMENT_CREATE,
            request_body=settlement.model_dump() if hasattr(settlement, 'model_dump') else settlement.dict(),
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/stripe/import", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def import_stripe_settlement(
    settlement_data: SettlementImport,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Import Stripe settlement (manual JSON)"""
    from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
    
    service = SettlementService(db)
    
    # Get bank_account to retrieve book_id
    bank_account_repo = BankAccountRepository(db)
    bank_account = await bank_account_repo.get_by_id(settlement_data.bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    legal_entity_id = settlement_data.legal_entity_id
    book_id = bank_account.book_id  # Get book_id from bank_account
    if not book_id:
        raise HTTPException(status_code=400, detail="Bank account must have a book_id")
    actor_user_id = None  # System-initiated
    
    # Handler function
    async def handler():
        settlement_dict = settlement_data.model_dump()
        settlement_dict["source"] = SettlementSource.STRIPE
        created = await service.import_settlement(settlement_dict)
        return created
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=SETTLEMENT_STRIPE_IMPORT,
            request_body=settlement_data.model_dump() if hasattr(settlement_data, 'model_dump') else settlement_data.dict(),
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/telr/import", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def import_telr_settlement(
    settlement_data: SettlementImport,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Import TELR settlement (manual JSON)"""
    # Get CASH book for entity (settlements post to CASH book)
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    from app.modules.general_ledger.models.book_model import BookType
    
    service = SettlementService(db)
    
    bank_account_repo = BankAccountRepository(db)
    bank_account = await bank_account_repo.get_by_id(settlement_data.bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    legal_entity_id = settlement_data.legal_entity_id
    
    book_repo = BookRepository(db)
    cash_book = await book_repo.get_by_entity_and_type(legal_entity_id, BookType.CASH)
    if not cash_book:
        raise HTTPException(status_code=404, detail="CASH book not found for entity")
    book_id = cash_book.id
    actor_user_id = None  # System-initiated
    
    # Handler function
    async def handler():
        settlement_dict = settlement_data.model_dump()
        settlement_dict["source"] = SettlementSource.TELR
        created = await service.import_settlement(settlement_dict)
        return created
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=SETTLEMENT_TELR_IMPORT,
            request_body=settlement_data.model_dump() if hasattr(settlement_data, 'model_dump') else settlement_data.dict(),
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[SettlementResponse])
async def list_settlements(
    entity_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    source: Optional[SettlementSource] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """List settlements for an entity"""
    service = SettlementService(db)
    settlements = await service.list_settlements(
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        source=source,
        limit=limit,
        offset=offset
    )
    return settlements


@router.get("/{settlement_id}", response_model=SettlementResponse)
async def get_settlement(
    settlement_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get settlement by ID"""
    service = SettlementService(db)
    settlement = await service.get_settlement(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return settlement
