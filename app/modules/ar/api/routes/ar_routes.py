"""AR API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List, Optional
from app.core.database import get_db_session
from app.core.idempotency import require_idempotency_key, apply_idempotency
from app.core.endpoint_keys import AR_INVOICE_POST
from app.modules.ar.services.ar_posting_service import ARPostingService
from app.modules.ar.repositories.ar_invoice_repository import ARInvoiceRepository
from app.modules.ar.repositories.ar_customer_repository import ARCustomerRepository
from app.modules.ar.models.ar_invoice_model import InvoiceStatus
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/books/{book_id}/ar", tags=["Accounts Receivable"])


@router.post("/invoices/{invoice_id}/post", status_code=status.HTTP_200_OK)
async def post_invoice(
    book_id: UUID,
    invoice_id: UUID,
    posted_by: UUID,
    db: AsyncSession = Depends(get_db_session),
    idempotency_key: str = Depends(require_idempotency_key)
):
    """Post invoice to ACCRUAL book"""
    from app.modules.ar.repositories.ar_invoice_repository import ARInvoiceRepository
    
    service = ARPostingService(db)
    
    # Get invoice to verify it exists and get legal_entity_id
    invoice_repo = ARInvoiceRepository(db)
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="AR invoice not found")
    
    # Verify invoice belongs to book (get book from invoice's legal_entity_id)
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    from app.modules.general_ledger.models.book_model import BookType
    book_repo = BookRepository(db)
    accrual_book = await book_repo.get_by_entity_and_type(invoice.legal_entity_id, BookType.ACCRUAL)
    if not accrual_book or accrual_book.id != book_id:
        raise HTTPException(status_code=400, detail="Invoice does not belong to this book")
    
    legal_entity_id = invoice.legal_entity_id
    actor_user_id = posted_by
    
    # Handler function
    async def handler():
        entry_id = await service.post_invoice(invoice_id, posted_by)
        return {
            "invoice_id": str(invoice_id),
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
            endpoint_key=AR_INVOICE_POST,
            request_body={"posted_by": str(posted_by)},
            actor_user_id=actor_user_id,
            handler_func=handler
        )
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invoices", response_model=List[dict])
async def list_ar_invoices(
    book_id: UUID,
    customer_id: Optional[UUID] = Query(None),
    status: Optional[InvoiceStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """List AR invoices"""
    invoice_repo = ARInvoiceRepository(db)
    
    # Get entity from book
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if customer_id:
        invoices = await invoice_repo.list_by_customer(customer_id, status=status, limit=limit, offset=offset)
    else:
        # List all invoices for entity (simplified - would need entity-based query)
        invoices = []
    
    return invoices


@router.get("/customers/{customer_id}/balance")
async def get_customer_balance(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get customer AR balance"""
    customer_repo = ARCustomerRepository(db)
    customer = await customer_repo.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    invoice_repo = ARInvoiceRepository(db)
    invoices = await invoice_repo.list_by_customer(customer_id, limit=1000)
    
    total_outstanding = sum(inv.outstanding_amount for inv in invoices)
    
    return {
        "customer_id": str(customer_id),
        "customer_name": customer.customer_name,
        "total_outstanding": float(total_outstanding),
        "currency": invoices[0].currency if invoices else "USD",
        "invoice_count": len(invoices)
    }


@router.get("/aging")
async def get_ar_aging(
    book_id: UUID,
    as_of_date: date = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Get AR aging report"""
    # Get entity from book
    from app.modules.general_ledger.repositories.book_repository import BookRepository
    book_repo = BookRepository(db)
    book = await book_repo.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    as_of = as_of_date or date.today()
    
    invoice_repo = ARInvoiceRepository(db)
    overdue = await invoice_repo.list_overdue(book.legal_entity_id, as_of)
    
    # Calculate aging buckets
    aging_buckets = {
        "0-30": [],
        "31-60": [],
        "61-90": [],
        "90+": []
    }
    
    for invoice in overdue:
        days_overdue = (as_of - invoice.due_date).days
        if days_overdue <= 30:
            aging_buckets["0-30"].append(invoice)
        elif days_overdue <= 60:
            aging_buckets["31-60"].append(invoice)
        elif days_overdue <= 90:
            aging_buckets["61-90"].append(invoice)
        else:
            aging_buckets["90+"].append(invoice)
    
    return {
        "as_of_date": as_of.isoformat(),
        "aging_buckets": {
            bucket: {
                "count": len(invoices),
                "total": float(sum(inv.outstanding_amount for inv in invoices))
            }
            for bucket, invoices in aging_buckets.items()
        }
    }
