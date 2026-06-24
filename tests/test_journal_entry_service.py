"""Unit tests for the GL core posting engine (JournalEntryService).

Covers the invariants the whole ledger depends on:
- balanced entries post, unbalanced entries are rejected
- empty entries and malformed lines are rejected
- reversal swaps DR/CR and marks the original REVERSED
- locked periods block posting
- source_key dedup prevents double posting
- required dimensions are enforced when requested
"""
import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ValidationError,
    PostingError,
    PeriodLockedError,
    DuplicateEntryError,
)
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.repositories.journal_entry_repository import (
    JournalLineRepository,
)
from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus
from app.modules.general_ledger.models.accounting_period_model import PeriodStatus

# entry date must fall inside the test_period fixture, which spans the current month
ENTRY_DATE = date.today()


async def _draft_with_lines(
    service: JournalEntryService,
    book_id,
    dr_account,
    cr_account,
    debit: Decimal,
    credit: Decimal,
    description: str = "Test entry",
):
    """Create a draft entry with one DR line and one CR line."""
    entry = await service.create_draft_entry(
        book_id=book_id,
        entry_date=ENTRY_DATE,
        description=description,
    )
    await service.add_line(
        journal_entry_id=entry.id,
        gl_account_id=dr_account.id,
        debit_fc=debit,
        credit_fc=Decimal("0.00"),
        currency="USD",
    )
    await service.add_line(
        journal_entry_id=entry.id,
        gl_account_id=cr_account.id,
        debit_fc=Decimal("0.00"),
        credit_fc=credit,
        currency="USD",
    )
    return entry


@pytest.mark.asyncio
async def test_post_balanced_entry_succeeds(
    test_db: AsyncSession, test_book, test_period, test_gl_accounts, test_user_id
):
    dr_account, cr_account = test_gl_accounts
    service = JournalEntryService(test_db)

    entry = await _draft_with_lines(
        service, test_book.id, dr_account, cr_account,
        debit=Decimal("100.00"), credit=Decimal("100.00"),
    )

    posted = await service.post_entry(
        entry.id, posted_by=uuid4(), require_dimensions=False
    )

    assert posted.status == JournalEntryStatus.POSTED
    assert posted.posted_at is not None
    assert len(posted.lines) == 2


@pytest.mark.asyncio
async def test_post_unbalanced_entry_raises_posting_error(
    test_db: AsyncSession, test_book, test_period, test_gl_accounts
):
    dr_account, cr_account = test_gl_accounts
    service = JournalEntryService(test_db)

    # Each line is individually valid (one-sided) but totals do not match.
    entry = await _draft_with_lines(
        service, test_book.id, dr_account, cr_account,
        debit=Decimal("100.00"), credit=Decimal("50.00"),
    )

    with pytest.raises(PostingError) as exc_info:
        await service.post_entry(entry.id, posted_by=uuid4(), require_dimensions=False)

    assert "does not balance" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_post_entry_with_no_lines_raises(
    test_db: AsyncSession, test_book, test_period
):
    service = JournalEntryService(test_db)
    entry = await service.create_draft_entry(
        book_id=test_book.id, entry_date=ENTRY_DATE, description="Empty entry"
    )

    with pytest.raises(ValidationError) as exc_info:
        await service.post_entry(entry.id, posted_by=uuid4(), require_dimensions=False)

    assert "at least one line" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_add_line_rejects_both_debit_and_credit(
    test_db: AsyncSession, test_book, test_period, test_gl_accounts
):
    dr_account, _ = test_gl_accounts
    service = JournalEntryService(test_db)
    entry = await service.create_draft_entry(
        book_id=test_book.id, entry_date=ENTRY_DATE, description="Bad line"
    )

    with pytest.raises(ValidationError):
        await service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=dr_account.id,
            debit_fc=Decimal("100.00"),
            credit_fc=Decimal("100.00"),
            currency="USD",
        )


@pytest.mark.asyncio
async def test_reverse_entry_swaps_dr_cr_and_marks_reversed(
    test_db: AsyncSession, test_book, test_period, test_gl_accounts
):
    dr_account, cr_account = test_gl_accounts
    service = JournalEntryService(test_db)

    entry = await _draft_with_lines(
        service, test_book.id, dr_account, cr_account,
        debit=Decimal("100.00"), credit=Decimal("100.00"),
    )
    await service.post_entry(entry.id, posted_by=uuid4(), require_dimensions=False)

    original = await service.reverse_entry(
        journal_entry_id=entry.id,
        reversed_by=uuid4(),
        reason="correction",
        reversal_date=ENTRY_DATE,
    )

    assert original.status == JournalEntryStatus.REVERSED
    assert original.reversed_by_entry_id is not None

    # Reversal lines must mirror the original with DR/CR swapped.
    line_repo = JournalLineRepository(test_db)
    reversal_lines = await line_repo.list_by_entry(original.reversed_by_entry_id)
    by_account = {line.gl_account_id: line for line in reversal_lines}

    assert by_account[dr_account.id].credit_fc == Decimal("100.00")
    assert by_account[dr_account.id].debit_fc == Decimal("0.00")
    assert by_account[cr_account.id].debit_fc == Decimal("100.00")
    assert by_account[cr_account.id].credit_fc == Decimal("0.00")


@pytest.mark.asyncio
async def test_locked_period_blocks_posting(
    test_db: AsyncSession, test_book, test_period, test_gl_accounts
):
    dr_account, cr_account = test_gl_accounts
    service = JournalEntryService(test_db)

    entry = await _draft_with_lines(
        service, test_book.id, dr_account, cr_account,
        debit=Decimal("100.00"), credit=Decimal("100.00"),
    )

    test_period.status = PeriodStatus.LOCKED
    await test_db.commit()

    with pytest.raises(PeriodLockedError):
        await service.post_entry(entry.id, posted_by=uuid4(), require_dimensions=False)


@pytest.mark.asyncio
async def test_duplicate_source_key_prevents_double_post(
    test_db: AsyncSession, test_book, test_period, test_gl_accounts
):
    dr_account, cr_account = test_gl_accounts
    service = JournalEntryService(test_db)

    first = await _draft_with_lines(
        service, test_book.id, dr_account, cr_account,
        debit=Decimal("100.00"), credit=Decimal("100.00"), description="first",
    )
    await service.post_entry(
        first.id, posted_by=uuid4(), require_dimensions=False, source_key="SRC:DUP"
    )

    second = await _draft_with_lines(
        service, test_book.id, dr_account, cr_account,
        debit=Decimal("100.00"), credit=Decimal("100.00"), description="second",
    )

    with pytest.raises(DuplicateEntryError):
        await service.post_entry(
            second.id, posted_by=uuid4(), require_dimensions=False, source_key="SRC:DUP"
        )


@pytest.mark.asyncio
async def test_post_requires_dimensions_when_enabled(
    test_db: AsyncSession, test_book, test_period, test_gl_accounts
):
    dr_account, cr_account = test_gl_accounts
    service = JournalEntryService(test_db)

    entry = await _draft_with_lines(
        service, test_book.id, dr_account, cr_account,
        debit=Decimal("100.00"), credit=Decimal("100.00"),
    )

    # No dimensions attached -> posting with enforcement must fail.
    with pytest.raises(ValidationError) as exc_info:
        await service.post_entry(entry.id, posted_by=uuid4(), require_dimensions=True)

    assert "dimension" in str(exc_info.value).lower()
