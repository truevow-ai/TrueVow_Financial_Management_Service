"""Billing Sync API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import BILLING_SYNC
from app.modules.ar.services.ar_sync_service import ARSyncService
from app.modules.ar.integrations.billing_adapter import BillingAdapter, HTTPBillingAdapter
from app.modules.ar.schemas.ar_sync_schemas import (
    BillingSyncRequest,
    BillingSyncResponse
)
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/integrations/billing", tags=["Billing Sync"], dependencies=[Depends(get_user_context)])


def get_billing_adapter() -> BillingAdapter:
    """Get billing adapter instance"""
    if settings.billing_service_url:
        return HTTPBillingAdapter()
    else:
        return MockBillingAdapter()


@router.post("/sync", response_model=BillingSyncResponse, status_code=status.HTTP_200_OK)
async def sync_billing(
    book_id: UUID,
    request: BillingSyncRequest,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Sync AR data from Billing service"""
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
    from app.modules.ar.repositories.billing_sync_batch_repository import BillingSyncBatchRepository
    from app.modules.general_ledger.models.treasury_sync_batch_model import SyncBatchStatus
    
    batch_repo = BillingSyncBatchRepository(db)
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
        adapter = get_billing_adapter()
        sync_service = ARSyncService(db, adapter)
        
        # Sync customers
        customers_count, _ = await sync_service.sync_customers(
            entity_id=request.entity_id,
            since_cursor=request.since_cursor if not request.full_resync else None,
            full_resync=request.full_resync
        )
        
        # Sync invoices
        invoices_count, invoice_cursor = await sync_service.sync_invoices(
            entity_id=request.entity_id,
            since_cursor=request.since_cursor if not request.full_resync else None,
            full_resync=request.full_resync
        )
        
        # Sync payments
        payments_count, _ = await sync_service.sync_payments(
            entity_id=request.entity_id,
            since_cursor=request.since_cursor if not request.full_resync else None,
            full_resync=request.full_resync
        )
        
        # Update batch
        await batch_repo.update(
            batch.id,
            status=SyncBatchStatus.COMPLETED,
            cursor_end=invoice_cursor,
            customers_count=customers_count,
            invoices_count=invoices_count,
            payments_count=payments_count,
            completed_at=datetime.now()
        )
        
        # Update metadata with cursor_end for final storage
        metadata["cursor_end"] = invoice_cursor
        
        return BillingSyncResponse(
            entity_id=request.entity_id,
            customers_synced=customers_count,
            invoices_synced=invoices_count,
            payments_synced=payments_count,
            next_cursor=invoice_cursor,
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
            endpoint_key=BILLING_SYNC,
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
                    IdempotencyKey.endpoint_key == BILLING_SYNC,
                    IdempotencyKey.idempotency_key == idempotency_key
                ).values(metadata_json=metadata_json)
            )
            await db.commit()
        
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sync/status")
async def get_billing_sync_status(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get Billing sync status"""
    from app.modules.general_ledger.repositories.external_sync_repository import ExternalSyncCursorRepository
    cursor_repo = ExternalSyncCursorRepository(db)
    
    customer_cursor = await cursor_repo.get_cursor(entity_id, "billing", "customer")
    invoice_cursor = await cursor_repo.get_cursor(entity_id, "billing", "invoice")
    payment_cursor = await cursor_repo.get_cursor(entity_id, "billing", "payment")
    
    return {
        "entity_id": str(entity_id),
        "customer_cursor": customer_cursor.cursor_value if customer_cursor else None,
        "customer_last_sync": customer_cursor.last_sync_at.isoformat() if customer_cursor and customer_cursor.last_sync_at else None,
        "invoice_cursor": invoice_cursor.cursor_value if invoice_cursor else None,
        "invoice_last_sync": invoice_cursor.last_sync_at.isoformat() if invoice_cursor and invoice_cursor.last_sync_at else None,
        "payment_cursor": payment_cursor.cursor_value if payment_cursor else None,
        "payment_last_sync": payment_cursor.last_sync_at.isoformat() if payment_cursor and payment_cursor.last_sync_at else None,
    }
