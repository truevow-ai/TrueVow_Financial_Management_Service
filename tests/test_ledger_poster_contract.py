"""Contract tests for the LedgerPoster swap seam.

These guarantee that:
- the configured backend conforms to the LedgerPoster protocol,
- the default backend is the in-house JournalEntryService,
- an unknown backend fails loudly,
- a poster obtained from the factory can actually post a balanced entry.
"""
import os
from uuid import uuid4
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.general_ledger.services.ledger_poster import (
    LedgerPoster,
    get_ledger_poster,
)
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus

ENTRY_DATE = date.today()


@pytest.mark.asyncio
async def test_factory_returns_conforming_poster(test_db: AsyncSession):
    poster = get_ledger_poster(test_db)
    assert isinstance(poster, LedgerPoster)


@pytest.mark.asyncio
async def test_default_backend_is_internal_journal_entry_service(test_db: AsyncSession):
    poster = get_ledger_poster(test_db)
    assert isinstance(poster, JournalEntryService)


@pytest.mark.asyncio
async def test_unknown_backend_raises(test_db: AsyncSession):
    previous = os.environ.get("LEDGER_BACKEND")
    os.environ["LEDGER_BACKEND"] = "tigerbeetle"
    try:
        with pytest.raises(NotImplementedError):
            get_ledger_poster(test_db)
    finally:
        if previous is None:
            os.environ.pop("LEDGER_BACKEND", None)
        else:
            os.environ["LEDGER_BACKEND"] = previous


@pytest.mark.asyncio
async def test_poster_from_factory_can_post_balanced_entry(
    test_db: AsyncSession, test_book, test_period, test_gl_accounts
):
    dr_account, cr_account = test_gl_accounts
    poster = get_ledger_poster(test_db)

    entry = await poster.create_draft_entry(
        book_id=test_book.id,
        entry_date=ENTRY_DATE,
        description="Posted via LedgerPoster seam",
    )
    await poster.add_line(
        journal_entry_id=entry.id,
        gl_account_id=dr_account.id,
        debit_fc=Decimal("100.00"),
        credit_fc=Decimal("0.00"),
        currency="USD",
    )
    await poster.add_line(
        journal_entry_id=entry.id,
        gl_account_id=cr_account.id,
        debit_fc=Decimal("0.00"),
        credit_fc=Decimal("100.00"),
        currency="USD",
    )

    posted = await poster.post_entry(
        entry.id, posted_by=uuid4(), require_dimensions=False
    )
    assert posted.status == JournalEntryStatus.POSTED
