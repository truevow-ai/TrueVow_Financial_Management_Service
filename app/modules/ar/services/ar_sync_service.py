"""AR Sync Service - Syncs data from Billing service"""
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.ar.integrations.billing_adapter import BillingAdapter
from app.modules.ar.repositories.ar_customer_repository import ARCustomerRepository
from app.modules.ar.repositories.ar_invoice_repository import ARInvoiceRepository
from app.modules.ar.repositories.ar_invoice_line_repository import ARInvoiceLineRepository
from app.modules.ar.repositories.ar_payment_repository import ARPaymentRepository
from app.modules.ar.repositories.ar_allocation_repository import ARAllocationRepository
from app.modules.general_ledger.repositories.external_sync_repository import (
    ExternalSyncCursorRepository,
    SourceObjectMapRepository
)
from app.modules.ar.models.ar_customer_model import ARCustomer
from app.modules.ar.models.ar_invoice_model import ARInvoice, ARInvoiceLine, InvoiceStatus
from app.modules.ar.models.ar_payment_model import ARPayment, ARAllocation, PaymentStatus
from app.core.exceptions import NotFoundError, ValidationError


class ARSyncService:
    """Service for syncing AR data from Billing service"""
    
    def __init__(self, session: AsyncSession, billing_adapter: BillingAdapter):
        self.session = session
        self.billing_adapter = billing_adapter
        self.customer_repo = ARCustomerRepository(session)
        self.invoice_repo = ARInvoiceRepository(session)
        self.payment_repo = ARPaymentRepository(session)
        self.line_repo = ARInvoiceLineRepository(session)
        self.allocation_repo = ARAllocationRepository(session)
        self.cursor_repo = ExternalSyncCursorRepository(session)
        self.mapping_repo = SourceObjectMapRepository(session)
    
    async def sync_customers(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        full_resync: bool = False
    ) -> tuple[int, Optional[str]]:
        """Sync customers from Billing service
        
        Returns: (synced_count, next_cursor)
        """
        # Get cursor
        cursor_obj = await self.cursor_repo.get_cursor(
            entity_id=entity_id,
            source_service="billing",
            object_type="customer"
        )
        
        cursor = since_cursor or (None if full_resync else (cursor_obj.cursor_value if cursor_obj else None))
        
        # Fetch from Billing
        customers, next_cursor = await self.billing_adapter.get_customers(
            entity_id=entity_id,
            since_cursor=cursor,
            limit=100
        )
        
        synced_count = 0
        for customer_data in customers:
            try:
                # Check if customer already exists
                existing = await self.customer_repo.get_by_external_id(customer_data["id"])
                if existing:
                    # Update existing
                    await self.customer_repo.update(
                        existing.id,
                        customer_name=customer_data.get("name", existing.customer_name),
                        customer_email=customer_data.get("email"),
                        customer_code=customer_data.get("code"),
                        is_active=customer_data.get("is_active", True)
                    )
                else:
                    # Create new
                    customer = await self.customer_repo.create(
                        legal_entity_id=entity_id,
                        external_customer_id=customer_data["id"],
                        customer_name=customer_data.get("name", "Unknown"),
                        customer_email=customer_data.get("email"),
                        customer_code=customer_data.get("code"),
                        is_active=customer_data.get("is_active", True)
                    )
                    # Create mapping
                    await self.mapping_repo.create_mapping(
                        entity_id=entity_id,
                        source_service="billing",
                        object_type="customer",
                        external_id=customer_data["id"],
                        internal_id=customer.id
                    )
                synced_count += 1
            except Exception as e:
                # Log error but continue
                continue
        
        # Update cursor
        if next_cursor:
            await self.cursor_repo.update_cursor(
                entity_id=entity_id,
                source_service="billing",
                object_type="customer",
                cursor_value=next_cursor
            )
        
        await self.session.commit()
        return synced_count, next_cursor
    
    async def sync_invoices(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        full_resync: bool = False
    ) -> tuple[int, Optional[str]]:
        """Sync invoices from Billing service"""
        # Get cursor
        cursor_obj = await self.cursor_repo.get_cursor(
            entity_id=entity_id,
            source_service="billing",
            object_type="invoice"
        )
        
        cursor = since_cursor or (None if full_resync else (cursor_obj.cursor_value if cursor_obj else None))
        
        # Fetch from Billing
        invoices, next_cursor = await self.billing_adapter.get_invoices(
            entity_id=entity_id,
            since_cursor=cursor,
            limit=100
        )
        
        synced_count = 0
        for invoice_data in invoices:
            try:
                # Get or create customer
                customer = await self.customer_repo.get_by_external_id(invoice_data["customer_id"])
                if not customer:
                    # Customer should exist, but create if missing
                    customer = await self.customer_repo.create(
                        legal_entity_id=entity_id,
                        external_customer_id=invoice_data["customer_id"],
                        customer_name="Unknown",
                        is_active=True
                    )
                
                # Check if invoice exists
                existing = await self.invoice_repo.get_by_external_id(invoice_data["id"])
                if existing:
                    # Update existing
                    await self.invoice_repo.update(
                        existing.id,
                        status=InvoiceStatus(invoice_data.get("status", "ISSUED")),
                        paid_amount=Decimal(str(invoice_data.get("paid_amount", 0))),
                        outstanding_amount=Decimal(str(invoice_data.get("outstanding_amount", invoice_data["total_amount"])))
                    )
                else:
                    # Create new invoice
                    invoice = await self.invoice_repo.create(
                        legal_entity_id=entity_id,
                        ar_customer_id=customer.id,
                        external_invoice_id=invoice_data["id"],
                        invoice_number=invoice_data.get("invoice_number", invoice_data["id"]),
                        invoice_date=date.fromisoformat(invoice_data["invoice_date"]),
                        due_date=date.fromisoformat(invoice_data["due_date"]) if invoice_data.get("due_date") else None,
                        total_amount=Decimal(str(invoice_data["total_amount"])),
                        currency=invoice_data.get("currency", "USD"),
                        status=InvoiceStatus(invoice_data.get("status", "ISSUED")),
                        paid_amount=Decimal(str(invoice_data.get("paid_amount", 0))),
                        outstanding_amount=Decimal(str(invoice_data.get("outstanding_amount", invoice_data["total_amount"]))),
                        description=invoice_data.get("description")
                    )
                    
                    # Create invoice lines
                    for line_data in invoice_data.get("lines", []):
                        await self._create_invoice_line(invoice.id, line_data, invoice.legal_entity_id)
                    
                    # Create mapping
                    await self.mapping_repo.create_mapping(
                        entity_id=entity_id,
                        source_service="billing",
                        object_type="invoice",
                        external_id=invoice_data["id"],
                        internal_id=invoice.id
                    )
                synced_count += 1
            except Exception as e:
                continue
        
        # Update cursor
        if next_cursor:
            await self.cursor_repo.update_cursor(
                entity_id=entity_id,
                source_service="billing",
                object_type="invoice",
                cursor_value=next_cursor
            )
        
        await self.session.commit()
        return synced_count, next_cursor
    
    async def _create_invoice_line(self, invoice_id: UUID, line_data: Dict, entity_id: UUID) -> ARInvoiceLine:
        """Create invoice line"""
        # Get next line number
        existing_lines = await self.line_repo.list_by_invoice(invoice_id)
        line_number = len(existing_lines) + 1
        
        # Parse dates
        service_start = None
        service_end = None
        if line_data.get("service_start"):
            service_start = date.fromisoformat(line_data["service_start"])
        if line_data.get("service_end"):
            service_end = date.fromisoformat(line_data["service_end"])
        
        line = await self.line_repo.create(
            ar_invoice_id=invoice_id,
            line_number=line_number,
            description=line_data.get("description"),
            quantity=Decimal(str(line_data.get("quantity", 1))),
            unit_price=Decimal(str(line_data["unit_price"])),
            line_amount=Decimal(str(line_data.get("line_amount", line_data["unit_price"]))),
            currency=line_data.get("currency", "USD"),
            service_start=service_start,
            service_end=service_end,
            is_deferrable=line_data.get("is_deferrable", False)
        )
        return line
    
    async def sync_payments(
        self,
        entity_id: UUID,
        since_cursor: Optional[str] = None,
        full_resync: bool = False
    ) -> tuple[int, Optional[str]]:
        """Sync payments from Billing service"""
        # Get cursor
        cursor_obj = await self.cursor_repo.get_cursor(
            entity_id=entity_id,
            source_service="billing",
            object_type="payment"
        )
        
        cursor = since_cursor or (None if full_resync else (cursor_obj.cursor_value if cursor_obj else None))
        
        # Fetch from Billing
        payments, next_cursor = await self.billing_adapter.get_payments(
            entity_id=entity_id,
            since_cursor=cursor,
            limit=100
        )
        
        synced_count = 0
        for payment_data in payments:
            try:
                # Get customer
                customer = await self.customer_repo.get_by_external_id(payment_data["customer_id"])
                if not customer:
                    continue  # Skip if customer not found
                
                # Check if payment exists
                existing = await self.payment_repo.get_by_external_id(payment_data["id"])
                if not existing:
                    # Create payment
                    payment = await self.payment_repo.create(
                        legal_entity_id=entity_id,
                        ar_customer_id=customer.id,
                        external_payment_id=payment_data["id"],
                        payment_date=date.fromisoformat(payment_data["payment_date"]),
                        payment_amount=Decimal(str(payment_data["amount"])),
                        currency=payment_data.get("currency", "USD"),
                        payment_method=payment_data.get("payment_method"),
                        status=PaymentStatus(payment_data.get("status", "COMPLETED")),
                        reference_number=payment_data.get("reference_number"),
                        description=payment_data.get("description")
                    )
                    
                    # Create allocations to invoices
                    for allocation_data in payment_data.get("allocations", []):
                        invoice = await self.invoice_repo.get_by_external_id(allocation_data["invoice_id"])
                        if invoice:
                            await self._create_allocation(payment.id, invoice.id, allocation_data)
                    
                    # Create mapping
                    await self.mapping_repo.create_mapping(
                        entity_id=entity_id,
                        source_service="billing",
                        object_type="payment",
                        external_id=payment_data["id"],
                        internal_id=payment.id
                    )
                synced_count += 1
            except Exception as e:
                continue
        
        # Update cursor
        if next_cursor:
            await self.cursor_repo.update_cursor(
                entity_id=entity_id,
                source_service="billing",
                object_type="payment",
                cursor_value=next_cursor
            )
        
        await self.session.commit()
        return synced_count, next_cursor
    
    async def _create_allocation(
        self,
        payment_id: UUID,
        invoice_id: UUID,
        allocation_data: Dict
    ) -> ARAllocation:
        """Create payment allocation"""
        allocation = await self.allocation_repo.create(
            ar_payment_id=payment_id,
            ar_invoice_id=invoice_id,
            allocated_amount=Decimal(str(allocation_data["amount"])),
            currency=allocation_data.get("currency", "USD"),
            allocation_date=date.fromisoformat(allocation_data.get("allocation_date", date.today().isoformat()))
        )
        return allocation
