"""Test reconciliation safety - close does NOT post adjustments"""
import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.general_ledger.services.reconciliation_service import ReconciliationService
from app.modules.general_ledger.models.reconciliation_model import ReconciliationSession, ReconciliationStatus
from app.modules.general_ledger.models.journal_entry_model import JournalEntry
from app.modules.treasury.models.bank_account_model import BankAccount
from tests.conftest import test_db, test_book, test_period, test_legal_entity


@pytest.mark.asyncio
async def test_reconciliation_close_does_not_post_adjustments(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity
):
    """Test: Reconciliation close does NOT post adjustments automatically"""
    # Create bank account
    bank_account = BankAccount(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        account_name="Test Bank Account",
        bank_name="Test Bank",
        currency="USD",
        is_active=True
    )
    test_db.add(bank_account)
    await test_db.commit()
    
    # Create reconciliation session
    session = ReconciliationSession(
        id=uuid4(),
        bank_account_id=bank_account.id,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        statement_ending_balance=Decimal("10000.00"),
        statement_currency="USD",
        status=ReconciliationStatus.IN_PROGRESS,
        difference=Decimal("0.00")
    )
    test_db.add(session)
    await test_db.commit()
    
    # Close session (allow_non_zero=True so close succeeds; test verifies close does NOT post JEs)
    reconciliation_service = ReconciliationService(test_db)
    closed = await reconciliation_service.close_session(
        session_id=session.id,
        reconciled_by=uuid4(),
        notes="Test close",
        allow_non_zero=True
    )
    
    assert closed.status == ReconciliationStatus.CLOSED
    
    # Verify NO journal entries were created by close
    result = await test_db.execute(
        select(JournalEntry).where(
            JournalEntry.source_key.like("RECONCILIATION:CLOSE:%")
        )
    )
    adjustment_entries = result.scalars().all()
    
    # Close should NOT create any journal entries
    assert len(adjustment_entries) == 0


@pytest.mark.asyncio
async def test_reconciliation_close_fails_if_difference_non_zero(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity
):
    """Test: Reconciliation close fails if difference != 0 (unless override)"""
    from app.core.exceptions import ValidationError
    
    bank_account = BankAccount(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        account_name="Test Bank Account",
        bank_name="Test Bank",
        currency="USD",
        is_active=True
    )
    test_db.add(bank_account)
    await test_db.commit()
    
    session = ReconciliationSession(
        id=uuid4(),
        bank_account_id=bank_account.id,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        statement_ending_balance=Decimal("10000.00"),
        statement_currency="USD",
        status=ReconciliationStatus.IN_PROGRESS,
        difference=Decimal("100.00")  # Non-zero difference
    )
    test_db.add(session)
    await test_db.commit()
    
    reconciliation_service = ReconciliationService(test_db)
    
    # Should fail without allow_non_zero
    with pytest.raises(ValidationError) as exc_info:
        await reconciliation_service.close_session(
            session_id=session.id,
            reconciled_by=uuid4(),
            allow_non_zero=False
        )
    
    assert "non-zero difference" in str(exc_info.value).lower()
    
    # Should succeed with allow_non_zero=True
    closed = await reconciliation_service.close_session(
        session_id=session.id,
        reconciled_by=uuid4(),
        allow_non_zero=True
    )
    assert closed.status == ReconciliationStatus.CLOSED
