"""Treasury Sync API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import TREASURY_SYNC, TREASURY_SYNC_POST_TX
from app.modules.general_ledger.services.treasury_sync_service import TreasurySyncService
from app.modules.general_ledger.services.cash_book_posting_service import CashBookPostingService
from app.modules.general_ledger.schemas.treasury_sync_schemas import (
    TreasurySyncRequest,
    TreasurySyncResponse
)
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/books/{book_id}/integrations/treasury", tags=["Treasury Sync"], dependencies=[Depends(get_user_context)])


@router.post("/sync", response_model=TreasurySyncResponse, status_code=status.HTTP_200_OK)
async def sync_treasury(
    book_id: UUID,
    request: TreasurySyncRequest,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Sync Treasury data to FM"""
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    
    # Get legal_entity_id from book
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.legal_entity_id != request.entity_id:
        raise HTTPException(status_code=400, detail="Book does not belong to this entity")
    
    legal_entity_id = book.legal_entity_id
    actor_user_id = None  # Sync operations are system-initiated
    
    # Create sync batch BEFORE idempotency (for correlation metadata)
    from app.modules.general_ledger.repositories.treasury_sync_batch_repository import TreasurySyncBatchRepository
    from app.modules.general_ledger.models.treasury_sync_batch_model import SyncBatchStatus
    
    batch_repo = TreasurySyncBatchRepository(db)
    batch_number = await batch_repo.generate_batch_number(legal_entity_id)
    
    batch = await batch_repo.create(
        legal_entity_id=legal_entity_id,
        book_id=book_id,
        batch_number=batch_number,
        status=SyncBatchStatus.PROCESSING,
        cursor_start=request.since_cursor,
        started_at=datetime.now()
    )
    await db.flush()
    batch_id = str(batch.id)
    
    # Prepare metadata for idempotency correlation
    metadata = {
        "batch_id": batch_id,
        "batch_number": batch_number,
        "cursor_start": request.since_cursor
    }
    
    # Handler function
    async def handler():
        
        sync_service = TreasurySyncService(db)
        posting_service = CashBookPostingService(db)
        
        # Sync transactions
        transactions, tx_cursor = await sync_service.sync_transactions(
            entity_id=request.entity_id,
            since_cursor=request.since_cursor if not request.full_resync else None,
            limit=1000
        )
        
        # Sync settlements
        settlements, _ = await sync_service.sync_settlements(
            entity_id=request.entity_id,
            limit=100
        )
        
        # Sync FX conversions
        fx_conversions, _ = await sync_service.sync_fx_conversions(
            entity_id=request.entity_id,
            limit=100
        )
        
        # Sync transfers
        transfers, _ = await sync_service.sync_transfers(
            entity_id=request.entity_id,
            limit=100
        )
        
        # Update batch
        await batch_repo.update(
            batch.id,
            status=SyncBatchStatus.COMPLETED,
            cursor_end=tx_cursor,
            transactions_count=len(transactions),
            completed_at=datetime.now()
        )
        
        # Update metadata with cursor_end for final storage
        metadata["cursor_end"] = tx_cursor
        
        return TreasurySyncResponse(
            entity_id=request.entity_id,
            transactions_count=len(transactions),
            settlements_count=len(settlements),
            fx_conversions_count=len(fx_conversions),
            transfers_count=len(transfers),
            next_cursor=tx_cursor,
            sync_timestamp=datetime.now()
        )
    
    try:
        # Apply idempotency with batch metadata for correlation
        # Metadata includes batch_id for audit/debug correlation
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=TREASURY_SYNC,
            request_body=request.model_dump() if hasattr(request, 'model_dump') else {
                "entity_id": str(request.entity_id),
                "since_cursor": request.since_cursor,
                "full_resync": request.full_resync
            },
            actor_user_id=actor_user_id,
            handler_func=handler,
            metadata=metadata  # batch_id, cursor_start stored on creation
        )
        
        # Update metadata with final cursor_end after handler completes
        if isinstance(response, dict) and "next_cursor" in response:
            from sqlalchemy import update
            from app.modules.core.models.idempotency_model import IdempotencyKey
            import json
            
            metadata["cursor_end"] = response["next_cursor"]
            metadata_json = json.dumps(metadata, separators=(',', ':'), ensure_ascii=False)
            
            await db.execute(
                update(IdempotencyKey).where(
                    IdempotencyKey.legal_entity_id == legal_entity_id,
                    IdempotencyKey.book_id == book_id,
                    IdempotencyKey.endpoint_key == TREASURY_SYNC,
                    IdempotencyKey.idempotency_key == idempotency_key
                ).values(metadata_json=metadata_json)
            )
            await db.commit()
        
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync/post-transactions", status_code=status.HTTP_200_OK)
async def sync_and_post_transactions(
    book_id: UUID,
    entity_id: UUID,
    posted_by: UUID,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Sync and post Treasury transactions to CASH book"""
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    from app.modules.general_ledger.repositories.treasury_sync_batch_repository import TreasurySyncBatchRepository
    from app.modules.general_ledger.models.treasury_sync_batch_model import SyncBatchStatus
    from datetime import datetime
    
    # Get legal_entity_id from book
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.legal_entity_id != entity_id:
        raise HTTPException(status_code=400, detail="Book does not belong to this entity")
    
    legal_entity_id = book.legal_entity_id
    actor_user_id = posted_by
    
    # Handler function
    async def handler():
        # Create sync batch for tracking
        batch_repo = TreasurySyncBatchRepository(db)
        batch_number = await batch_repo.generate_batch_number(legal_entity_id)
        
        batch = await batch_repo.create(
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            batch_number=batch_number,
            status=SyncBatchStatus.PROCESSING,
            started_at=datetime.now()
        )
        await db.flush()
        
        sync_service = TreasurySyncService(db)
        posting_service = CashBookPostingService(db)
        
        # Sync transactions
        transactions, cursor_end = await sync_service.sync_transactions(
            entity_id=entity_id,
            limit=limit
        )
        
        # Batch-level idempotency check: if batch already completed, skip all transactions
        if batch.status == SyncBatchStatus.COMPLETED:
            # Batch already completed - return existing results
            from sqlalchemy import select
            from app.modules.general_ledger.models.journal_entry_model import JournalEntry, JournalEntryStatus
            # Find JEs posted for this batch (using batch_id in source_key pattern)
            batch_source_key_pattern = f"TREASURY:POST_TX:{entity_id}:{batch.id}:"
            all_batch_jes = await db.execute(
                select(JournalEntry).where(
                    JournalEntry.legal_entity_id == legal_entity_id,
                    JournalEntry.book_id == book_id,
                    JournalEntry.source_key.like(f"{batch_source_key_pattern}%"),  # Pattern match
                    JournalEntry.status == JournalEntryStatus.POSTED
                )
            )
            existing_entry_ids = [str(je.id) for je in all_batch_jes.scalars().all()]
            
            return {
                "batch_id": str(batch.id),
                "batch_number": batch_number,
                "synced": len(transactions),
                "posted": len(existing_entry_ids),
                "failed": 0,
                "entry_ids": existing_entry_ids,
                "already_posted": True
            }
        
        # Post each transaction with batch-level source_key format
        # Format: TREASURY:POST_TX:{entity_id}:{batch.id}:{external_id or tx.id}
        # This ensures batch-level idempotency (check batch status first) while maintaining
        # per-transaction uniqueness via source_key constraint
        posted_entries = []
        failed_count = 0
        
        for tx in transactions:
            try:
                # Use batch-level source_key with transaction identifier for uniqueness
                # Batch-level idempotency handled by batch status check above
                # Per-transaction uniqueness handled by source_key + external_id
                tx_identifier = tx.external_id if tx.external_id else str(tx.id)
                source_key = f"TREASURY:POST_TX:{entity_id}:{batch.id}:{tx_identifier}"
                entry_id = await posting_service.post_bank_transaction(
                    entity_id=entity_id,
                    bank_transaction=tx,
                    posted_by=posted_by,
                    source_key=source_key
                )
                posted_entries.append(entry_id)
            except Exception as e:
                failed_count += 1
                continue
        
        # Update batch
        await batch_repo.update(
            batch.id,
            status=SyncBatchStatus.COMPLETED,
            cursor_end=cursor_end,
            transactions_count=len(transactions),
            posted_count=len(posted_entries),
            failed_count=failed_count,
            completed_at=datetime.now()
        )
        
        return {
            "batch_id": str(batch.id),
            "batch_number": batch_number,
            "synced": len(transactions),
            "posted": len(posted_entries),
            "failed": failed_count,
            "entry_ids": posted_entries
        }
    
    try:
        # Apply idempotency
        status_code, response = await apply_idempotency(
            db=db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=TREASURY_SYNC_POST_TX,
            request_body={"entity_id": str(entity_id), "posted_by": str(posted_by), "limit": limit},
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sync/status")
async def get_sync_status(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get Treasury sync status"""
    sync_service = TreasurySyncService(db)
    
    # Get cursors
    from app.modules.treasury.repositories.sync_cursor_repository import SyncCursorRepository
    cursor_repo = SyncCursorRepository(db)
    
    tx_cursor = await cursor_repo.get_cursor(entity_id, "treasury", "transaction")
    settlement_cursor = await cursor_repo.get_cursor(entity_id, "treasury", "settlement")
    
    return {
        "entity_id": str(entity_id),
        "transaction_cursor": tx_cursor.cursor_value if tx_cursor else None,
        "transaction_last_sync": tx_cursor.last_sync_at.isoformat() if tx_cursor and tx_cursor.last_sync_at else None,
        "settlement_cursor": settlement_cursor.cursor_value if settlement_cursor else None,
        "settlement_last_sync": settlement_cursor.last_sync_at.isoformat() if settlement_cursor and settlement_cursor.last_sync_at else None,
    }
