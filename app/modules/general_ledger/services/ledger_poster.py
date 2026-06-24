"""Ledger posting interface (the swap seam for the GL core).

Subledgers (AR, AP, payroll, intercompany, treasury cash book, reconciliation)
post into the general ledger through the ``LedgerPoster`` protocol rather than
importing the concrete ``JournalEntryService`` directly.

Today the only implementation is the in-house, Postgres-backed
``JournalEntryService``. When/if the ledger core is moved behind an external
engine (e.g. TigerBeetle or Formance), only ``get_ledger_poster`` needs to
change - no subledger code has to be rewritten.
"""
import os
from typing import List, Optional, Protocol, runtime_checkable
from uuid import UUID
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.general_ledger.models.journal_entry_model import (
    JournalEntry,
    JournalLine,
)


@runtime_checkable
class LedgerPoster(Protocol):
    """Contract every ledger backend must satisfy for subledgers to post."""

    async def create_draft_entry(
        self,
        book_id: UUID,
        entry_date: date,
        description: str,
        reference_number: Optional[str] = None,
        source_service: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None,
        idempotency_key: Optional[str] = None,
    ) -> JournalEntry:
        ...

    async def add_line(
        self,
        journal_entry_id: UUID,
        gl_account_id: UUID,
        debit_fc: Decimal,
        credit_fc: Decimal,
        currency: str,
        description: Optional[str] = None,
        debit_tc: Optional[Decimal] = None,
        credit_tc: Optional[Decimal] = None,
        fx_rate: Optional[Decimal] = None,
        fx_source: Optional[str] = None,
        fx_timestamp: Optional[date] = None,
        dimension_value_ids: Optional[List[UUID]] = None,
    ) -> JournalLine:
        ...

    async def post_entry(
        self,
        journal_entry_id: UUID,
        posted_by: UUID,
        require_dimensions: bool = True,
        source_key: Optional[str] = None,
    ) -> JournalEntry:
        ...

    async def reverse_entry(
        self,
        journal_entry_id: UUID,
        reversed_by: UUID,
        reason: str,
        reversal_date: Optional[date] = None,
        source_key: Optional[str] = None,
    ) -> JournalEntry:
        ...


def get_ledger_poster(session: AsyncSession) -> LedgerPoster:
    """Return the configured ledger poster (single swap point).

    Controlled by the ``LEDGER_BACKEND`` env var. Defaults to the in-house
    Postgres journal-entry engine. Future external backends plug in here.
    """
    backend = os.environ.get("LEDGER_BACKEND", "internal").lower()

    if backend == "internal":
        # Imported lazily to keep the import graph acyclic.
        from app.modules.general_ledger.services.journal_entry_service import (
            JournalEntryService,
        )

        return JournalEntryService(session)

    raise NotImplementedError(
        f"Ledger backend '{backend}' is not implemented. "
        "Implement a LedgerPoster and wire it here (e.g. TigerBeetle/Formance)."
    )
