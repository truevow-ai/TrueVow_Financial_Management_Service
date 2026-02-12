"""AR/AP Aging Report Service"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from app.modules.ar.repositories.ar_invoice_repository import ARInvoiceRepository
from app.modules.ar.repositories.ar_customer_repository import ARCustomerRepository
from app.modules.general_ledger.repositories.legal_entity_repository import LegalEntityRepository


class ARAgingService:
    """Service for generating AR Aging reports"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.invoice_repo = ARInvoiceRepository(session)
        self.customer_repo = ARCustomerRepository(session)
        self.entity_repo = LegalEntityRepository(session)
    
    async def generate_ar_aging(
        self,
        entity_id: UUID,
        as_of_date: date,
        aging_buckets: Optional[List[int]] = None
    ) -> Dict:
        """Generate AR Aging report
        
        Args:
            entity_id: Legal entity ID
            as_of_date: Report as-of date
            aging_buckets: Days for aging buckets (default: [0, 30, 60, 90])
        """
        if aging_buckets is None:
            aging_buckets = [0, 30, 60, 90]
        
        # Get all outstanding invoices
        invoices = await self.invoice_repo.list_by_entity(
            entity_id=entity_id,
            status=None,  # Get all
            limit=10000
        )
        
        # Filter to outstanding invoices
        outstanding = [
            inv for inv in invoices
            if inv.outstanding_amount > Decimal("0.00")
        ]
        
        # Calculate aging per invoice
        customer_aging: Dict[UUID, Dict] = {}
        
        for invoice in outstanding:
            customer_id = invoice.ar_customer_id
            
            if customer_id not in customer_aging:
                customer = await self.customer_repo.get_by_id(customer_id)
                customer_aging[customer_id] = {
                    "customer_id": str(customer_id),
                    "customer_name": customer.customer_name if customer else "Unknown",
                    "customer_code": customer.customer_code if customer else "",
                    "total_outstanding": Decimal("0.00"),
                    "buckets": {f"over_{bucket}": Decimal("0.00") for bucket in aging_buckets},
                    "invoices": []
                }
            
            # Calculate days overdue
            due_date = invoice.due_date or invoice.invoice_date
            days_overdue = (as_of_date - due_date).days
            
            # Determine bucket
            bucket = "current"
            for i, bucket_days in enumerate(sorted(aging_buckets, reverse=True)):
                if days_overdue > bucket_days:
                    bucket = f"over_{bucket_days}"
                    break
            
            amount = invoice.outstanding_amount
            
            customer_aging[customer_id]["total_outstanding"] += amount
            customer_aging[customer_id]["buckets"][bucket] = customer_aging[customer_id]["buckets"].get(bucket, Decimal("0.00")) + amount
            
            customer_aging[customer_id]["invoices"].append({
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date.isoformat(),
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "days_overdue": days_overdue,
                "outstanding_amount": float(amount),
                "currency": invoice.currency,
                "bucket": bucket
            })
        
        # Calculate totals
        total_outstanding = sum(c["total_outstanding"] for c in customer_aging.values())
        bucket_totals = {}
        for bucket in [f"over_{b}" for b in aging_buckets] + ["current"]:
            bucket_totals[bucket] = sum(
                c["buckets"].get(bucket, Decimal("0.00"))
                for c in customer_aging.values()
            )
        
        # Convert to float for JSON
        for customer_id in customer_aging:
            customer_aging[customer_id]["total_outstanding"] = float(customer_aging[customer_id]["total_outstanding"])
            for bucket in customer_aging[customer_id]["buckets"]:
                customer_aging[customer_id]["buckets"][bucket] = float(customer_aging[customer_id]["buckets"][bucket])
        
        bucket_totals = {k: float(v) for k, v in bucket_totals.items()}
        
        return {
            "entity_id": str(entity_id),
            "as_of_date": as_of_date.isoformat(),
            "aging_buckets": aging_buckets,
            "total_outstanding": float(total_outstanding),
            "bucket_totals": bucket_totals,
            "customers": list(customer_aging.values())
        }
