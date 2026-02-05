"""Test row_version 409 conflict"""
import pytest
from uuid import uuid4
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.row_version import check_row_version
from app.modules.ap.models.ap_bill_model import APBill, BillStatus
from app.modules.ap.models.ap_vendor_model import APVendor
from tests.conftest import test_db, test_book, test_period, test_legal_entity


@pytest.mark.asyncio
async def test_row_version_409_ap_bill_approve(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity
):
    """Test: Stale row_version returns 409 on AP bill approve"""
    # Create AP vendor (required FK for APBill)
    vendor = APVendor(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        vendor_code=f"V-{uuid4().hex[:8]}",
        vendor_name="Test Vendor",
        default_currency="USD",
    )
    test_db.add(vendor)
    await test_db.flush()
    # Create AP bill
    bill = APBill(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        book_id=test_book.id,
        ap_vendor_id=vendor.id,
        bill_number=f"BILL-{uuid4().hex[:8]}",
        bill_date=date.today(),
        due_date=date(2026, 2, 1),
        total_amount=1000.00,
        currency="USD",
        outstanding_amount=1000.00,
        status=BillStatus.DRAFT,
        row_version=1
    )
    test_db.add(bill)
    await test_db.commit()
    await test_db.refresh(bill)
    
    # Simulate concurrent update (someone else updates row_version)
    bill.row_version = 2
    await test_db.commit()
    await test_db.refresh(bill)
    
    # Try to approve with stale row_version
    stale_version = 1
    current_version = bill.row_version
    
    with pytest.raises(HTTPException) as exc_info:
        check_row_version(current_version, stale_version, "AP bill")
    
    assert exc_info.value.status_code == 409
    assert "row version" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_row_version_success_match(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity
):
    """Test: Matching row_version succeeds"""
    vendor = APVendor(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        vendor_code=f"V-{uuid4().hex[:8]}",
        vendor_name="Test Vendor",
        default_currency="USD",
    )
    test_db.add(vendor)
    await test_db.flush()
    bill = APBill(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        book_id=test_book.id,
        ap_vendor_id=vendor.id,
        bill_number=f"BILL-{uuid4().hex[:8]}",
        bill_date=date.today(),
        due_date=date(2026, 2, 1),
        total_amount=1000.00,
        currency="USD",
        outstanding_amount=1000.00,
        status=BillStatus.DRAFT,
        row_version=5
    )
    test_db.add(bill)
    await test_db.commit()
    await test_db.refresh(bill)
    
    # Should not raise
    check_row_version(bill.row_version, 5, "AP bill")
