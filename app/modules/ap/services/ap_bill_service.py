"""AP Bill Service – create, list, get, add lines"""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ap.models.ap_bill_model import APBill, APBillLine, BillStatus
from app.modules.ap.repositories.ap_bill_repository import APBillRepository
from app.modules.ap.repositories.ap_bill_line_repository import APBillLineRepository
from app.core.exceptions import NotFoundError, ValidationError


class APBillService:
    """Service for AP bill CRUD and line management"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.bill_repo = APBillRepository(session)
        self.line_repo = APBillLineRepository(session)

    async def create_bill(
        self,
        legal_entity_id: UUID,
        book_id: UUID,
        vendor_id: UUID,
        bill_number: str,
        bill_date: date,
        due_date: Optional[date] = None,
        currency: str = "USD",
        description: Optional[str] = None,
        reference_number: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> APBill:
        """Create a new AP bill in DRAFT"""
        bill = APBill(
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            ap_vendor_id=vendor_id,
            bill_number=bill_number,
            bill_date=bill_date,
            due_date=due_date or bill_date,
            total_amount=Decimal("0.00"),
            currency=currency,
            status=BillStatus.DRAFT,
            paid_amount=Decimal("0.00"),
            outstanding_amount=Decimal("0.00"),
            description=description,
            reference_number=reference_number,
        )
        self.session.add(bill)
        await self.session.flush()
        return bill

    async def add_line(
        self,
        bill_id: UUID,
        gl_account_id: UUID,
        description: str,
        quantity: Decimal,
        unit_price: Decimal,
        line_number: int = 1,
        currency: str = "USD",
        tax_code: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> APBillLine:
        """Add a line to an AP bill and update bill total"""
        bill = await self.bill_repo.get_by_id(bill_id)
        if not bill:
            raise NotFoundError("AP bill not found")
        if bill.status != BillStatus.DRAFT:
            raise ValidationError("Cannot add lines to a bill that is not in DRAFT")
        line_amount = quantity * unit_price
        line = APBillLine(
            ap_bill_id=bill_id,
            line_number=line_number,
            gl_account_id=gl_account_id,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            line_amount=line_amount,
            currency=currency,
            tax_code=tax_code,
        )
        self.session.add(line)
        await self.session.flush()
        bill.total_amount = (bill.total_amount or Decimal("0.00")) + line_amount
        bill.outstanding_amount = bill.total_amount - (bill.paid_amount or Decimal("0.00"))
        await self.session.flush()
        return line

    async def list_bills(
        self,
        entity_id: UUID,
        book_id: UUID,
        vendor_id: Optional[UUID] = None,
        status: Optional[BillStatus] = None,
    ) -> List[APBill]:
        """List AP bills for a book"""
        return await self.bill_repo.list_by_book(
            entity_id=entity_id,
            book_id=book_id,
            vendor_id=vendor_id,
            status=status,
        )

    async def get_bill(self, bill_id: UUID) -> Optional[APBill]:
        """Get AP bill by ID"""
        return await self.bill_repo.get_by_id(bill_id)
