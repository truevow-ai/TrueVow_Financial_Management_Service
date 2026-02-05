"""Journal Entry API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import JE_POST, JE_REVERSE
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.schemas.journal_entry_schemas import (
    JournalEntryCreate,
    JournalEntryPostRequest,
    JournalEntryReverseRequest,
    JournalEntryResponse,
    JournalLineBulkUpsertRequest,
    JournalLineBulkUpsertResponse
)
from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    PostingError,
    PeriodLockedError,
    DuplicateEntryError
)
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/books/{book_id}/journal-entries", tags=["Journal Entries"])


@router.post("", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    book_id: UUID,
    entry: JournalEntryCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new journal entry"""
    service = JournalEntryService(db)
    
    # Use header idempotency key if provided, otherwise use request body
    key = idempotency_key or entry.idempotency_key
    
    try:
        # Create draft entry
        created_entry = await service.create_draft_entry(
            book_id=book_id,
            entry_date=entry.entry_date,
            description=entry.description,
            reference_number=entry.reference_number,
            source_service=entry.source_service,
            source_type=entry.source_type,
            source_id=entry.source_id,
            idempotency_key=key
        )
        
        # Add lines
        for line in entry.lines:
            await service.add_line(
                journal_entry_id=created_entry.id,
                gl_account_id=line.gl_account_id,
                debit_fc=line.debit_fc,
                credit_fc=line.credit_fc,
                currency=line.currency,
                description=line.description,
                debit_tc=line.debit_tc,
                credit_tc=line.credit_tc,
                fx_rate=line.fx_rate,
                fx_source=line.fx_source,
                fx_timestamp=line.fx_timestamp,
                dimension_value_ids=line.dimension_value_ids
            )
        
        # Refresh entry with lines
        await db.refresh(created_entry)
        return created_entry
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[JournalEntryResponse])
async def list_journal_entries(
    book_id: UUID,
    status: Optional[JournalEntryStatus] = None,
    period_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """List journal entries for a book"""
    service = JournalEntryService(db)
    entries = await service.entry_repo.list_by_book(
        book_id=book_id,
        status=status,
        period_id=period_id,
        limit=limit,
        offset=offset
    )
    return entries


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get journal entry by ID"""
    service = JournalEntryService(db)
    entry = await service.entry_repo.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    # Load lines
    lines = await service.line_repo.list_by_entry(entry_id)
    entry.lines = lines
    return entry


@router.post("/{entry_id}/post", response_model=JournalEntryResponse)
async def post_journal_entry(
    book_id: UUID,
    entry_id: UUID,
    request: JournalEntryPostRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Post a journal entry (makes it immutable)"""
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    
    service = JournalEntryService(db)
    
    # Verify entry belongs to book
    entry = await service.entry_repo.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.book_id != book_id:
        raise HTTPException(status_code=400, detail="Journal entry does not belong to this book")
    
    # Get legal_entity_id from book
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Use user_id from token, fallback to request if provided
    posted_by = UUID(user.get("user_id")) if user.get("user_id") else request.posted_by
    actor_user_id = UUID(user.get("user_id")) if user.get("user_id") else None
    
    # Handler function (return serializable so idempotency store + response_model work)
    async def handler():
        posted_entry = await service.post_entry(
            journal_entry_id=entry_id,
            posted_by=posted_by,
            require_dimensions=request.require_dimensions
        )
        return JournalEntryResponse.model_validate(posted_entry)
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=book.legal_entity_id,
            book_id=book_id,
            endpoint_key=JE_POST,
            request_body=request.model_dump(),
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return JSONResponse(content=response, status_code=status_code)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PostingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PeriodLockedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{entry_id}/reverse", response_model=JournalEntryResponse)
async def reverse_journal_entry(
    book_id: UUID,
    entry_id: UUID,
    request: JournalEntryReverseRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Reverse a posted journal entry"""
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    
    service = JournalEntryService(db)
    
    # Verify entry belongs to book
    entry = await service.entry_repo.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.book_id != book_id:
        raise HTTPException(status_code=400, detail="Journal entry does not belong to this book")
    
    # Get legal_entity_id from book
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Use user_id from token, fallback to request if provided
    reversed_by = UUID(user.get("user_id")) if user.get("user_id") else request.reversed_by
    actor_user_id = UUID(user.get("user_id")) if user.get("user_id") else None
    
    # Handler function
    async def handler():
        reversed_entry = await service.reverse_entry(
            journal_entry_id=entry_id,
            reversed_by=reversed_by,
            reason=request.reason,
            reversal_date=request.reversal_date
        )
        return reversed_entry
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=book.legal_entity_id,
            book_id=book_id,
            endpoint_key=JE_REVERSE,
            request_body=request.model_dump(),
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}:validate")
async def validate_journal_entry(
    book_id: UUID,
    entry_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Validate a journal entry (check balance, dimensions, etc.)
    Returns validation result with errors.
    """
    service = JournalEntryService(db)
    
    entry = await service.entry_repo.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    if entry.book_id != book_id:
        raise HTTPException(status_code=400, detail="Journal entry does not belong to this book")
    
    # Get all lines
    lines = await service.line_repo.list_by_entry(entry_id)
    
    errors = []
    total_debits = sum(line.debit_fc for line in lines)
    total_credits = sum(line.credit_fc for line in lines)
    balance = total_debits - total_credits
    
    # Check balance
    if total_debits != total_credits:
        errors.append({
            "scope": "header",
            "field": "balance",
            "code": "UNBALANCED",
            "message": f"Journal entry does not balance: debits={total_debits}, credits={total_credits}"
        })
    
    # Check dimensions (if entry is draft and will require dimensions on post)
    if entry.status == JournalEntryStatus.DRAFT:
        try:
            await service._validate_required_dimensions(lines)
        except ValidationError as e:
            # Extract dimension errors per line
            for idx, line in enumerate(lines):
                errors.append({
                    "scope": "line",
                    "line_id": str(line.id),
                    "field": "dimensions",
                    "code": "MISSING_DIMENSIONS",
                    "message": f"Line {line.line_number}: {str(e)}"
                })
    
    return {
        "is_valid": len(errors) == 0,
        "totals": {
            "debit": float(total_debits),
            "credit": float(total_credits),
            "balance": float(balance)
        },
        "errors": errors
    }


@router.post("/{entry_id}/lines:bulkUpsert", response_model=JournalLineBulkUpsertResponse)
async def bulk_upsert_journal_lines(
    book_id: UUID,
    entry_id: UUID,
    request: JournalLineBulkUpsertRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Bulk upsert journal entry lines.
    Supports UPSERT (create/update) and DELETE operations.
    Returns per-row errors for validation issues.
    """
    service = JournalEntryService(db)
    
    # Get entry to verify it exists
    entry = await service.entry_repo.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    if entry.book_id != book_id:
        raise HTTPException(status_code=400, detail="Journal entry does not belong to this book")
    
    # Get legal_entity_id from book
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(entry.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    legal_entity_id = book.legal_entity_id
    
    try:
        # Convert request lines to dict format
        lines_data = [line.model_dump() for line in request.lines]
        
        # Call bulk upsert
        updated_lines, errors = await service.bulk_upsert_lines(
            journal_entry_id=entry_id,
            lines_data=lines_data,
            legal_entity_id=legal_entity_id
        )
        
        await db.commit()
        
        # Convert errors to response format
        error_responses = [
            {
                "client_row_id": err.get("client_row_id"),
                "line_id": err.get("line_id"),
                "field": err.get("field"),
                "code": err["code"],
                "message": err["message"]
            }
            for err in errors
        ]
        
        return JournalLineBulkUpsertResponse(
            lines=updated_lines,
            row_version=None,  # TODO: Add row_version to JournalEntry if needed
            errors=error_responses
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
