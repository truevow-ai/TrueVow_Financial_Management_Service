"""Test idempotency replay functionality"""
import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.general_ledger.models.journal_entry_model import JournalEntry, JournalEntryStatus
from app.modules.payroll.models.payroll_run_model import PayrollRun, PayrollRunStatus
from app.modules.core.models.idempotency_model import IdempotencyKey
from app.core.endpoint_keys import JE_POST
from tests.conftest import test_db, test_book, test_period, test_legal_entity, test_user_id, test_gl_accounts, test_pay_group


@pytest.mark.asyncio
async def test_je_post_idempotency_replay_same_key_same_body(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity,
    test_user_id,
    test_gl_accounts,
):
    """Test: Same Idempotency-Key + same body → returns same response and no duplicate JEs"""
    from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
    from app.core.idempotency import apply_idempotency

    dr_account, cr_account = test_gl_accounts
    je_service = JournalEntryService(test_db)
    entry = await je_service.create_draft_entry(
        book_id=test_book.id,
        entry_date=date.today(),
        description="Test entry"
    )
    await je_service.add_line(entry.id, dr_account.id, Decimal("100.00"), Decimal("0"), "USD")
    await je_service.add_line(entry.id, cr_account.id, Decimal("0"), Decimal("100.00"), "USD")

    idempotency_key = str(uuid4())
    legal_entity_id = test_legal_entity.id
    entry_id = entry.id  # Keep id for queries after handler may expire entry

    # First call - should create JE
    async def handler():
        return await je_service.post_entry(entry_id, uuid4(), require_dimensions=False)

    status1, response1 = await apply_idempotency(
        db=test_db,
        idempotency_key=idempotency_key,
        legal_entity_id=legal_entity_id,
        book_id=test_book.id,
        endpoint_key=JE_POST,
        request_body={"posted_by": test_user_id},
        actor_user_id=uuid4(),
        handler_func=handler
    )
    
    # Count JEs
    from sqlalchemy import select
    result = await test_db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    je1 = result.scalar_one()
    assert je1.status == JournalEntryStatus.POSTED

    # Second call with same key and body - should replay
    status2, response2 = await apply_idempotency(
        db=test_db,
        idempotency_key=idempotency_key,
        legal_entity_id=legal_entity_id,
        book_id=test_book.id,
        endpoint_key=JE_POST,
        request_body={"posted_by": test_user_id},  # Same body
        actor_user_id=uuid4(),
        handler_func=handler
    )
    
    # Should return same response
    assert status1 == status2
    assert response1 == response2
    
    # Should NOT create duplicate JE (entry should still be the same one)
    result = await test_db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    je2 = result.scalar_one()
    assert je2.id == je1.id
    assert je2.status == JournalEntryStatus.POSTED


@pytest.mark.asyncio
async def test_je_post_idempotency_409_different_body(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity,
    test_user_id,
    test_gl_accounts,
):
    """Test: Same key + different body hash → 409"""
    from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
    from app.core.idempotency import apply_idempotency
    from fastapi import HTTPException

    dr_account, cr_account = test_gl_accounts
    je_service = JournalEntryService(test_db)
    entry = await je_service.create_draft_entry(
        book_id=test_book.id,
        entry_date=date.today(),
        description="Test entry"
    )
    await je_service.add_line(entry.id, dr_account.id, Decimal("100.00"), Decimal("0"), "USD")
    await je_service.add_line(entry.id, cr_account.id, Decimal("0"), Decimal("100.00"), "USD")

    idempotency_key = str(uuid4())
    legal_entity_id = test_legal_entity.id
    
    # First call
    async def handler():
        return await je_service.post_entry(entry.id, uuid4(), require_dimensions=False)
    
    await apply_idempotency(
        db=test_db,
        idempotency_key=idempotency_key,
        legal_entity_id=legal_entity_id,
        book_id=test_book.id,
        endpoint_key=JE_POST,
        request_body={"posted_by": test_user_id},
        actor_user_id=uuid4(),
        handler_func=handler
    )
    
    # Second call with different body - should raise 409
    with pytest.raises(HTTPException) as exc_info:
        await apply_idempotency(
            db=test_db,
            idempotency_key=idempotency_key,
            legal_entity_id=legal_entity_id,
            book_id=test_book.id,
            endpoint_key=JE_POST,
            request_body={"posted_by": "different_user"},  # Different body
            actor_user_id=uuid4(),
            handler_func=handler
        )
    
    assert exc_info.value.status_code == 409
    assert "different request payload" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_source_key_duplicate_prevention(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity,
    test_user_id,
    test_gl_accounts,
    test_pay_group,
):
    """Test: Call payroll post twice with different Idempotency-Key → only one JE exists due to source_key constraint"""
    from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
    from sqlalchemy import select
    from decimal import Decimal

    run = PayrollRun(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        book_id=test_book.id,
        pay_group_id=test_pay_group.id,
        run_number=f"RUN-{uuid4().hex[:8]}",
        pay_period_start=date(2026, 1, 1),
        pay_period_end=date(2026, 1, 15),
        pay_date=date.today(),
        status=PayrollRunStatus.APPROVED,
        total_gross=Decimal("10000.00"),
        total_deductions=Decimal("2000.00"),
        total_net=Decimal("8000.00"),
        total_employer_contrib=Decimal("0.00"),
        currency="USD"
    )
    test_db.add(run)
    await test_db.commit()
    await test_db.refresh(run)

    je_service = JournalEntryService(test_db)
    dr_account, cr_account = test_gl_accounts
    source_key = f"PAYROLL:POST:{run.id}"

    entry1 = await je_service.create_draft_entry(
        book_id=test_book.id,
        entry_date=date.today(),
        description=f"Payroll run {run.id}"
    )
    await je_service.add_line(entry1.id, dr_account.id, Decimal("100.00"), Decimal("0"), "USD")
    await je_service.add_line(entry1.id, cr_account.id, Decimal("0"), Decimal("100.00"), "USD")

    await je_service.post_entry(
        entry1.id,
        uuid4(),
        require_dimensions=False,
        source_key=source_key
    )
    
    entry2 = await je_service.create_draft_entry(
        book_id=test_book.id,
        entry_date=date.today(),
        description=f"Payroll run {run.id} (duplicate attempt)"
    )
    await je_service.add_line(entry2.id, dr_account.id, Decimal("100.00"), Decimal("0"), "USD")
    await je_service.add_line(entry2.id, cr_account.id, Decimal("0"), Decimal("100.00"), "USD")

    # Attempting to post with same source_key should raise DuplicateEntryError (service checks before DB)
    from app.core.exceptions import DuplicateEntryError
    with pytest.raises(DuplicateEntryError):
        await je_service.post_entry(
            entry2.id,
            uuid4(),
            require_dimensions=False,
            source_key=source_key  # Same source_key
        )
    
    # Verify only one JE exists
    result = await test_db.execute(
        select(JournalEntry).where(JournalEntry.source_key == source_key)
    )
    entries = result.scalars().all()
    assert len(entries) == 1, "Only one journal entry should exist per source_key"


@pytest.mark.asyncio
async def test_idempotency_replay_same_status_code_and_body(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity,
    test_user_id,
    test_gl_accounts,
):
    """Test: Idempotency replay returns exact same status code and body"""
    from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
    from app.core.idempotency import apply_idempotency
    from app.core.endpoint_keys import JE_POST
    from sqlalchemy import select

    dr_account, cr_account = test_gl_accounts
    je_service = JournalEntryService(test_db)
    entry = await je_service.create_draft_entry(
        book_id=test_book.id,
        entry_date=date.today(),
        description="Test entry for status code replay"
    )
    await je_service.add_line(entry.id, dr_account.id, Decimal("100.00"), Decimal("0"), "USD")
    await je_service.add_line(entry.id, cr_account.id, Decimal("0"), Decimal("100.00"), "USD")

    idempotency_key = str(uuid4())
    legal_entity_id = test_legal_entity.id
    
    async def handler():
        return await je_service.post_entry(entry.id, uuid4(), require_dimensions=False)
    
    # First call
    status1, response1 = await apply_idempotency(
        db=test_db,
        idempotency_key=idempotency_key,
        legal_entity_id=legal_entity_id,
        book_id=test_book.id,
        endpoint_key=JE_POST,
        request_body={"posted_by": test_user_id},
        actor_user_id=uuid4(),
        handler_func=handler
    )
    
    # Second call - should replay exact same status and body
    status2, response2 = await apply_idempotency(
        db=test_db,
        idempotency_key=idempotency_key,
        legal_entity_id=legal_entity_id,
        book_id=test_book.id,
        endpoint_key=JE_POST,
        request_body={"posted_by": test_user_id},
        actor_user_id=uuid4(),
        handler_func=handler
    )
    
    # Verify exact match
    assert status1 == status2, f"Status codes must match exactly: {status1} != {status2}"
    assert response1 == response2, "Response bodies must match exactly"
    
    # Verify stored response in database
    from app.modules.core.models.idempotency_model import IdempotencyKey
    result = await test_db.execute(
        select(IdempotencyKey).where(IdempotencyKey.idempotency_key == idempotency_key)
    )
    stored = result.scalar_one()
    assert stored.response_status == status1
    import json
    stored_body = json.loads(stored.response_blob)
    assert stored_body == response1


@pytest.mark.asyncio
async def test_source_key_blocks_duplicate_with_different_idempotency_keys(
    test_db: AsyncSession,
    test_book,
    test_period,
    test_legal_entity,
    test_user_id,
    test_gl_accounts,
):
    """Test: Second posting blocked by source_key even with different idempotency keys (JE post + source_key)."""
    from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
    from app.core.idempotency import apply_idempotency
    from app.core.endpoint_keys import JE_POST
    from app.core.exceptions import DuplicateEntryError
    from sqlalchemy import select
    from decimal import Decimal

    dr_account, cr_account = test_gl_accounts
    je_service = JournalEntryService(test_db)
    source_key = f"TEST:POST:{uuid4()}"

    entry1 = await je_service.create_draft_entry(
        book_id=test_book.id,
        entry_date=date.today(),
        description="First entry"
    )
    await je_service.add_line(entry1.id, dr_account.id, Decimal("100.00"), Decimal("0"), "USD")
    await je_service.add_line(entry1.id, cr_account.id, Decimal("0"), Decimal("100.00"), "USD")

    idempotency_key_1 = str(uuid4())
    idempotency_key_2 = str(uuid4())

    async def handler_first():
        return await je_service.post_entry(entry1.id, uuid4(), require_dimensions=False, source_key=source_key)

    status1, _ = await apply_idempotency(
        db=test_db,
        idempotency_key=idempotency_key_1,
        legal_entity_id=test_legal_entity.id,
        book_id=test_book.id,
        endpoint_key=JE_POST,
        request_body={"posted_by": test_user_id},
        actor_user_id=uuid4(),
        handler_func=handler_first
    )

    result = await test_db.execute(
        select(JournalEntry).where(JournalEntry.source_key == source_key)
    )
    entries = result.scalars().all()
    assert len(entries) == 1, "First post should create one JE"

    entry2 = await je_service.create_draft_entry(
        book_id=test_book.id,
        entry_date=date.today(),
        description="Second entry (duplicate source_key attempt)"
    )
    await je_service.add_line(entry2.id, dr_account.id, Decimal("50.00"), Decimal("0"), "USD")
    await je_service.add_line(entry2.id, cr_account.id, Decimal("0"), Decimal("50.00"), "USD")

    async def handler_second():
        return await je_service.post_entry(entry2.id, uuid4(), require_dimensions=False, source_key=source_key)

    with pytest.raises(DuplicateEntryError):
        await apply_idempotency(
            db=test_db,
            idempotency_key=idempotency_key_2,
            legal_entity_id=test_legal_entity.id,
            book_id=test_book.id,
            endpoint_key=JE_POST,
            request_body={"posted_by": test_user_id},
            actor_user_id=uuid4(),
            handler_func=handler_second
        )

    result = await test_db.execute(
        select(JournalEntry).where(JournalEntry.source_key == source_key)
    )
    entries = result.scalars().all()
    assert len(entries) == 1, "source_key constraint should prevent duplicate posting"
