"""Bank Transaction API Routes"""
import json
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import BANK_TX_IMPORT
from app.modules.treasury.services.bank_transaction_service import BankTransactionService
from app.modules.treasury.schemas.bank_transaction_schemas import (
    BankTransactionCreate,
    BankTransactionCSVImport,
    BankTransactionResponse,
    BankTransactionListResponse
)
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/bank-transactions", tags=["Bank Transactions"], dependencies=[Depends(get_user_context)])


@router.post("", response_model=BankTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_bank_transaction(
    transaction: BankTransactionCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new bank transaction"""
    service = BankTransactionService(db)
    try:
        created = await service.create_transaction(
            bank_account_id=transaction.bank_account_id,
            transaction_date=transaction.transaction_date,
            amount=transaction.amount,
            currency=transaction.currency,
            transaction_type=transaction.transaction_type,
            description=transaction.description,
            value_date=transaction.value_date,
            reference_number=transaction.reference_number,
            counterparty_name=transaction.counterparty_name,
            counterparty_account=transaction.counterparty_account,
            balance_after=transaction.balance_after,
            external_id=transaction.external_id
        )
        return created
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_csv_transactions(
    import_request: BankTransactionCSVImport,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Import bank transactions from CSV data"""
    from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    
    service = BankTransactionService(db)
    
    # Get bank account to retrieve book_id and legal_entity_id
    bank_account_repo = BankAccountRepository(db)
    bank_account = await bank_account_repo.get_by_id(import_request.bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    # Get book to get legal_entity_id
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(bank_account.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    legal_entity_id = book.legal_entity_id
    book_id = bank_account.book_id
    actor_user_id = None  # Import operations are system-initiated
    
    # Compute file hash from transactions data for source_key
    transactions_json = json.dumps(
        [t.model_dump() if hasattr(t, 'model_dump') else dict(t) for t in import_request.transactions],
        sort_keys=True
    )
    file_hash = hashlib.sha256(transactions_json.encode('utf-8')).hexdigest()[:16]
    
    # Handler function
    async def handler():
        created, skipped = await service.import_csv_transactions(
            bank_account_id=import_request.bank_account_id,
            transactions_data=[t.model_dump() if hasattr(t, 'model_dump') else dict(t) for t in import_request.transactions],
            import_batch_id=import_request.import_batch_id or f"import_{file_hash}"
        )
        return {
            "created": created,
            "skipped": skipped,
            "total": len(import_request.transactions)
        }
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=BANK_TX_IMPORT,
            request_body=import_request.model_dump() if hasattr(import_request, 'model_dump') else {
                "bank_account_id": str(import_request.bank_account_id),
                "transactions": [t.model_dump() if hasattr(t, 'model_dump') else dict(t) for t in import_request.transactions],
                "import_batch_id": import_request.import_batch_id
            },
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=BankTransactionListResponse)
async def list_bank_transactions(
    bank_account_id: Optional[UUID] = Query(None),
    updated_after: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    cursor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List bank transactions with cursor pagination"""
    service = BankTransactionService(db)
    transactions, next_cursor = await service.list_with_cursor(
        bank_account_id=bank_account_id,
        updated_after=updated_after,
        limit=limit,
        cursor=cursor
    )
    return BankTransactionListResponse(
        transactions=transactions,
        next_cursor=next_cursor,
        limit=limit,
        has_more=next_cursor is not None
    )


@router.get("/{transaction_id}", response_model=BankTransactionResponse)
async def get_bank_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get bank transaction by ID"""
    service = BankTransactionService(db)
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    return transaction


@router.get("/accounts/{bank_account_id}/transactions", response_model=List[BankTransactionResponse])
async def list_account_transactions(
    bank_account_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    is_reconciled: Optional[bool] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """List transactions for a specific bank account"""
    service = BankTransactionService(db)
    transactions = await service.list_transactions(
        bank_account_id=bank_account_id,
        start_date=start_date,
        end_date=end_date,
        is_reconciled=is_reconciled,
        limit=limit,
        offset=offset
    )
    return transactions
