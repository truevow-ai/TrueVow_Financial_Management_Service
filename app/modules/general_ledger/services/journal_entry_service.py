"""Journal Entry Service"""
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.general_ledger.repositories.journal_entry_repository import (
    JournalEntryRepository,
    JournalLineRepository
)
from app.modules.general_ledger.repositories.accounting_period_repository import (
    AccountingPeriodRepository
)
from app.modules.general_ledger.repositories.dimension_repository import (
    DimensionValueRepository,
    DimensionRepository
)
from app.modules.general_ledger.repositories.gl_account_repository import (
    GLAccountRepository
)
from app.modules.general_ledger.repositories.book_repository import (
    BookRepository
)
from app.modules.general_ledger.models.journal_entry_model import (
    JournalEntry,
    JournalLine,
    JournalEntryStatus
)
from app.modules.general_ledger.models.accounting_period_model import PeriodStatus
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    PostingError,
    PeriodLockedError,
    DuplicateEntryError
)


class JournalEntryService:
    """Service for journal entry management and posting"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.entry_repo = JournalEntryRepository(session)
        self.line_repo = JournalLineRepository(session)
        self.period_repo = AccountingPeriodRepository(session)
        self.account_repo = GLAccountRepository(session)
        self.dimension_value_repo = DimensionValueRepository(session)
        self.dimension_repo = DimensionRepository(session)
        self.book_repo = BookRepository(session)
    
    async def create_draft_entry(
        self,
        book_id: UUID,
        entry_date: date,
        description: str,
        reference_number: Optional[str] = None,
        source_service: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[UUID] = None,
        idempotency_key: Optional[str] = None
    ) -> JournalEntry:
        """Create a draft journal entry"""
        # Check idempotency
        if idempotency_key:
            existing = await self.entry_repo.get_by_idempotency_key(idempotency_key)
            if existing:
                raise DuplicateEntryError(f"Entry with idempotency key {idempotency_key} already exists")
        
        # Get book to retrieve legal_entity_id
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise NotFoundError(f"Book {book_id} not found")
        
        # Get period for entry date
        period = await self.period_repo.get_by_book_and_date(book_id, entry_date)
        if not period:
            raise NotFoundError(f"No period found for date {entry_date} in book {book_id}")
        
        # Generate entry number
        entry_number = await self._generate_entry_number(book_id, entry_date)
        
        entry = await self.entry_repo.create(
            legal_entity_id=book.legal_entity_id,
            book_id=book_id,
            period_id=period.id,
            entry_number=entry_number,
            entry_date=entry_date,
            description=description,
            reference_number=reference_number,
            status=JournalEntryStatus.DRAFT,
            source_service=source_service,
            source_type=source_type,
            source_id=source_id,
            idempotency_key=idempotency_key
        )
        
        await self.session.flush()
        return entry
    
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
        dimension_value_ids: Optional[List[UUID]] = None
    ) -> JournalLine:
        """Add a line to a journal entry"""
        entry = await self.entry_repo.get_by_id(journal_entry_id)
        if not entry:
            raise NotFoundError(f"Journal entry {journal_entry_id} not found")
        
        if entry.status != JournalEntryStatus.DRAFT:
            raise ValidationError("Can only add lines to DRAFT entries")
        
        # Verify account exists and is in the same book
        account = await self.account_repo.get_by_id(gl_account_id)
        if not account:
            raise NotFoundError(f"Account {gl_account_id} not found")
        if account.book_id != entry.book_id:
            raise ValidationError("Account must be in the same book as entry")
        
        # Validate line: must have either debit or credit, not both
        if debit_fc > 0 and credit_fc > 0:
            raise ValidationError("Line cannot have both debit and credit")
        if debit_fc == 0 and credit_fc == 0:
            raise ValidationError("Line must have either debit or credit")
        
        # Get next line number
        existing_lines = await self.line_repo.list_by_entry(journal_entry_id)
        line_number = len(existing_lines) + 1
        
        # Set transaction currency amounts (default to functional currency if not provided)
        if debit_tc is None:
            debit_tc = debit_fc
        if credit_tc is None:
            credit_tc = credit_fc
        
        line = await self.line_repo.create(
            journal_entry_id=journal_entry_id,
            book_id=entry.book_id,
            gl_account_id=gl_account_id,
            line_number=line_number,
            debit_tc=debit_tc,
            credit_tc=credit_tc,
            currency=currency,
            debit_fc=debit_fc,
            credit_fc=credit_fc,
            fx_rate=fx_rate,
            fx_source=fx_source,
            fx_timestamp=fx_timestamp,
            description=description
        )
        
        # Add dimensions if provided
        if dimension_value_ids:
            await self._add_line_dimensions(line.id, dimension_value_ids)
        
        await self.session.flush()
        return line
    
    async def post_entry(
        self,
        journal_entry_id: UUID,
        posted_by: UUID,
        require_dimensions: bool = True,
        source_key: Optional[str] = None
    ) -> JournalEntry:
        """Post a journal entry (makes it immutable)"""
        entry = await self.entry_repo.get_by_id(journal_entry_id)
        if not entry:
            raise NotFoundError(f"Journal entry {journal_entry_id} not found")
        
        if entry.status != JournalEntryStatus.DRAFT:
            raise ValidationError("Can only post DRAFT entries")
        
        # Check period status
        period = await self.period_repo.get_by_id(entry.period_id)
        if not period:
            raise NotFoundError(f"Period {entry.period_id} not found")
        
        if period.status == PeriodStatus.LOCKED:
            raise PeriodLockedError(f"Period {period.period_name} is locked")
        
        # Get all lines
        lines = await self.line_repo.list_by_entry(journal_entry_id)
        if not lines:
            raise ValidationError("Journal entry must have at least one line")
        
        # Verify balance
        total_debits = sum(line.debit_fc for line in lines)
        total_credits = sum(line.credit_fc for line in lines)
        
        if total_debits != total_credits:
            raise PostingError(
                f"Journal entry does not balance: debits={total_debits}, credits={total_credits}"
            )
        
        # Enforce dimensions if required
        if require_dimensions:
            await self._validate_required_dimensions(lines)
        
        # Set source_key to prevent duplicate postings (use provided or default)
        if not source_key:
            source_key = f"JE:POST:{entry.id}"
        
        # Check for duplicate source_key (prevent double posting even without idempotency header)
        from sqlalchemy import select
        existing_with_source_key = await self.session.execute(
            select(JournalEntry).where(
                JournalEntry.legal_entity_id == entry.legal_entity_id,
                JournalEntry.book_id == entry.book_id,
                JournalEntry.source_key == source_key,
                JournalEntry.status == JournalEntryStatus.POSTED
            )
        )
        if existing_with_source_key.scalar_one_or_none():
            raise DuplicateEntryError(
                f"Journal entry with source_key '{source_key}' already posted. "
                "This prevents duplicate postings."
            )
        
        # Post the entry
        await self.entry_repo.update(
            journal_entry_id,
            status=JournalEntryStatus.POSTED,
            posted_by=posted_by,
            posted_at=date.today(),
            source_key=source_key
        )
        
        await self.session.commit()
        
        # Eager load lines for Pydantic validation
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(JournalEntry)
            .where(JournalEntry.id == journal_entry_id)
            .options(selectinload(JournalEntry.lines))
        )
        return result.scalar_one()
    
    async def reverse_entry(
        self,
        journal_entry_id: UUID,
        reversed_by: UUID,
        reason: str,
        reversal_date: Optional[date] = None
    ) -> JournalEntry:
        """Reverse a posted journal entry"""
        original_entry = await self.entry_repo.get_by_id(journal_entry_id)
        if not original_entry:
            raise NotFoundError(f"Journal entry {journal_entry_id} not found")
        
        if original_entry.status != JournalEntryStatus.POSTED:
            raise ValidationError("Can only reverse POSTED entries")
        
        if original_entry.reversed_by_entry_id:
            raise ValidationError("Entry has already been reversed")
        
        # Get original lines
        original_lines = await self.line_repo.list_by_entry(journal_entry_id)
        
        # Create reversal entry
        reversal_date = reversal_date or date.today()
        reversal_entry = await self.create_draft_entry(
            book_id=original_entry.book_id,
            entry_date=reversal_date,
            description=f"Reversal of {original_entry.entry_number}: {reason}",
            reference_number=f"REV-{original_entry.entry_number}",
            source_service="fm",
            source_type="reversal"
        )
        
        # Create reversal lines (swap debits and credits)
        for original_line in original_lines:
            await self.add_line(
                journal_entry_id=reversal_entry.id,
                gl_account_id=original_line.gl_account_id,
                debit_fc=original_line.credit_fc,  # Swap
                credit_fc=original_line.debit_fc,  # Swap
                currency=original_line.currency,
                description=original_line.description,
                debit_tc=original_line.credit_tc,
                credit_tc=original_line.debit_tc,
                fx_rate=original_line.fx_rate,
                fx_source=original_line.fx_source,
                fx_timestamp=original_line.fx_timestamp
            )
        
        # Post the reversal entry with source_key (use provided or default)
        if not source_key:
            reversal_source_key = f"JE:REVERSE:{journal_entry_id}"
        else:
            reversal_source_key = source_key
        await self.post_entry(
            reversal_entry.id, 
            reversed_by, 
            require_dimensions=False,
            source_key=reversal_source_key
        )
        
        # Mark original entry as reversed
        await self.entry_repo.update(
            journal_entry_id,
            status=JournalEntryStatus.REVERSED,
            reversed_by_entry_id=reversal_entry.id,
            reversal_reason=reason
        )
        
        await self.session.commit()
        return await self.entry_repo.get_by_id(journal_entry_id)
    
    async def _generate_entry_number(self, book_id: UUID, entry_date: date) -> str:
        """Generate unique entry number"""
        from sqlalchemy import select, func
        
        # Format: JE-YYYYMMDD-XXXX
        date_str = entry_date.strftime("%Y%m%d")
        
        # Count entries for this date in this book
        result = await self.session.execute(
            select(func.count(JournalEntry.id))
            .where(
                JournalEntry.book_id == book_id,
                JournalEntry.entry_date == entry_date
            )
        )
        same_date_count = result.scalar() or 0
        
        sequence = same_date_count + 1
        entry_number = f"JE-{date_str}-{sequence:04d}"
        
        # Verify uniqueness (in case of race condition)
        existing = await self.entry_repo.get_by_entry_number(entry_number)
        if existing:
            # If exists, increment sequence
            sequence += 1
            entry_number = f"JE-{date_str}-{sequence:04d}"
        
        return entry_number
    
    async def _validate_required_dimensions(self, lines: List[JournalLine]):
        """Validate that all lines have required dimensions"""
        from app.modules.general_ledger.models.journal_entry_model import JournalLineDimension
        from sqlalchemy import select
        
        # Required dimensions
        required_dimensions = ["COST_CENTER", "DEPARTMENT", "LOCATION"]
        
        for line in lines:
            # Get dimensions for this line
            result = await self.session.execute(
                select(JournalLineDimension)
                .where(JournalLineDimension.journal_line_id == line.id)
            )
            line_dimensions = result.scalars().all()
            
            # Get dimension codes for this line
            if line_dimensions:
                # Get dimension values
                dim_value_ids = [ld.dimension_value_id for ld in line_dimensions]
                result = await self.session.execute(
                    select(DimensionValue)
                    .where(DimensionValue.id.in_(dim_value_ids))
                )
                dimension_values = result.scalars().all()
                
                # Check required dimensions
                found_dimensions = {dv.dimension_code for dv in dimension_values}
                missing = set(required_dimensions) - found_dimensions
                
                if missing:
                    raise ValidationError(
                        f"Journal line {line.line_number} missing required dimensions: {', '.join(missing)}"
                    )
            else:
                raise ValidationError(
                    f"Journal line {line.line_number} has no dimensions. Required: {', '.join(required_dimensions)}"
                )
    
    async def _add_line_dimensions(self, line_id: UUID, dimension_value_ids: List[UUID]):
        """Add dimensions to a journal line"""
        from app.modules.general_ledger.models.journal_entry_model import JournalLineDimension
        
        # Verify dimension values exist
        for dim_value_id in dimension_value_ids:
            dim_value = await self.dimension_value_repo.get_by_id(dim_value_id)
            if not dim_value:
                raise NotFoundError(f"Dimension value {dim_value_id} not found")
            
            # Check if association already exists
            result = await self.session.execute(
                select(JournalLineDimension).where(
                    JournalLineDimension.journal_line_id == line_id,
                    JournalLineDimension.dimension_value_id == dim_value_id
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Create new association
                line_dim = JournalLineDimension(
                    journal_line_id=line_id,
                    dimension_value_id=dim_value_id
                )
                self.session.add(line_dim)
    
    async def bulk_upsert_lines(
        self,
        journal_entry_id: UUID,
        lines_data: List[Dict],
        legal_entity_id: UUID
    ) -> tuple[List[JournalLine], List[Dict]]:
        """
        Bulk upsert journal entry lines.
        
        Returns:
            tuple: (updated_lines, errors)
        """
        from app.modules.general_ledger.models.journal_entry_model import JournalLineDimension
        
        entry = await self.entry_repo.get_by_id(journal_entry_id)
        if not entry:
            raise NotFoundError(f"Journal entry {journal_entry_id} not found")
        
        if entry.status != JournalEntryStatus.DRAFT:
            raise ValidationError("Can only modify lines in DRAFT entries")
        
        errors: List[Dict] = []
        updated_lines: List[JournalLine] = []
        
        # Get existing lines
        existing_lines = await self.line_repo.list_by_entry(journal_entry_id)
        existing_by_id = {line.id: line for line in existing_lines}
        
        # Track which lines to keep (not deleted)
        lines_to_keep: set[UUID] = set()
        
        # Process each line
        for idx, line_data in enumerate(lines_data):
            client_row_id = line_data.get("client_row_id")
            line_id = line_data.get("line_id")
            deleted = line_data.get("deleted", False)
            
            # Handle deletion
            if deleted and line_id:
                try:
                    line = existing_by_id.get(UUID(line_id) if isinstance(line_id, str) else line_id)
                    if line:
                        await self.line_repo.delete(line.id)
                    # Don't add to lines_to_keep
                except Exception as e:
                    errors.append({
                        "client_row_id": client_row_id,
                        "line_id": line_id,
                        "code": "DELETE_ERROR",
                        "message": str(e)
                    })
                continue
            
            # Skip deleted lines without line_id
            if deleted:
                continue
            
            # Determine account
            gl_account_id = None
            if line_data.get("gl_account_id"):
                gl_account_id = UUID(line_data["gl_account_id"]) if isinstance(line_data["gl_account_id"], str) else line_data["gl_account_id"]
            elif line_data.get("account_code"):
                account_code = line_data["account_code"]
                account = await self.account_repo.get_by_code_and_book(account_code, entry.book_id)
                if not account:
                    errors.append({
                        "client_row_id": client_row_id,
                        "line_id": line_id,
                        "field": "account_code",
                        "code": "ACCOUNT_NOT_FOUND",
                        "message": f"Account code '{account_code}' not found in book"
                    })
                    continue
                gl_account_id = account.id
            else:
                errors.append({
                    "client_row_id": client_row_id,
                    "line_id": line_id,
                    "field": "account_code",
                    "code": "ACCOUNT_REQUIRED",
                    "message": "Either gl_account_id or account_code is required"
                })
                continue
            
            # Get amounts
            debit_amount = Decimal(str(line_data.get("debit_amount", 0)))
            credit_amount = Decimal(str(line_data.get("credit_amount", 0)))
            
            # Validate one and only one is > 0
            if debit_amount > 0 and credit_amount > 0:
                errors.append({
                    "client_row_id": client_row_id,
                    "line_id": line_id,
                    "field": "debit_amount",
                    "code": "BOTH_AMOUNTS",
                    "message": "Cannot have both debit and credit amounts"
                })
                continue
            
            if debit_amount == 0 and credit_amount == 0:
                errors.append({
                    "client_row_id": client_row_id,
                    "line_id": line_id,
                    "field": "debit_amount",
                    "code": "NO_AMOUNT",
                    "message": "Either debit_amount or credit_amount must be > 0"
                })
                continue
            
            # Get currency (default to book currency)
            currency = line_data.get("currency") or "USD"
            
            # Get FX rate
            fx_rate = None
            if line_data.get("fx_rate"):
                fx_rate = Decimal(str(line_data["fx_rate"]))
            
            # Calculate functional currency amounts (same as transaction currency for now)
            debit_fc = debit_amount
            credit_fc = credit_amount
            debit_tc = debit_amount
            credit_tc = credit_amount
            
            # Resolve dimension values
            dimension_value_ids: List[UUID] = []
            dimension_mapping = {
                "cost_center": "COST_CENTER",
                "department": "DEPARTMENT",
                "location": "LOCATION",
                "project": "PROJECT"
            }
            
            for dim_key, dim_code in dimension_mapping.items():
                if line_data.get(dim_key):
                    value_code = line_data[dim_key]
                    dim_value = await self.dimension_value_repo.get_by_dimension_and_value(
                        dim_code, value_code
                    )
                    if dim_value:
                        dimension_value_ids.append(dim_value.id)
                    else:
                        errors.append({
                            "client_row_id": client_row_id,
                            "line_id": line_id,
                            "field": dim_key,
                            "code": "DIMENSION_NOT_FOUND",
                            "message": f"Dimension value '{value_code}' not found for dimension '{dim_code}'"
                        })
            
            # Update or create line
            if line_id:
                # Update existing line
                line_uuid = UUID(line_id) if isinstance(line_id, str) else line_id
                line = existing_by_id.get(line_uuid)
                if not line:
                    errors.append({
                        "client_row_id": client_row_id,
                        "line_id": line_id,
                        "code": "LINE_NOT_FOUND",
                        "message": f"Line {line_id} not found"
                    })
                    continue
                
                # Update line
                line.gl_account_id = gl_account_id
                line.debit_tc = debit_tc
                line.credit_tc = credit_tc
                line.debit_fc = debit_fc
                line.credit_fc = credit_fc
                line.currency = currency
                line.fx_rate = fx_rate
                line.description = line_data.get("description")
                
                # Update dimensions (clear old, add new)
                result = await self.session.execute(
                    select(JournalLineDimension).where(
                        JournalLineDimension.journal_line_id == line.id
                    )
                )
                old_dims = result.scalars().all()
                for old_dim in old_dims:
                    await self.session.delete(old_dim)
                
                if dimension_value_ids:
                    await self._add_line_dimensions(line.id, dimension_value_ids)
                
                lines_to_keep.add(line.id)
                updated_lines.append(line)
            else:
                # Create new line
                # Get next line number
                max_line = max([l.line_number for l in existing_lines], default=0)
                line_number = max_line + 1
                
                line = await self.line_repo.create(
                    journal_entry_id=journal_entry_id,
                    book_id=entry.book_id,
                    gl_account_id=gl_account_id,
                    line_number=line_number,
                    debit_tc=debit_tc,
                    credit_tc=credit_tc,
                    currency=currency,
                    debit_fc=debit_fc,
                    credit_fc=credit_fc,
                    fx_rate=fx_rate,
                    description=line_data.get("description")
                )
                
                if dimension_value_ids:
                    await self._add_line_dimensions(line.id, dimension_value_ids)
                
                lines_to_keep.add(line.id)
                updated_lines.append(line)
                existing_lines.append(line)  # Add to existing for next iteration
        
        # Delete lines not in lines_to_keep (orphaned lines)
        for line in existing_lines:
            if line.id not in lines_to_keep:
                await self.line_repo.delete(line.id)
        
        await self.session.flush()
        
        # Reload all lines to return fresh data
        final_lines = await self.line_repo.list_by_entry(journal_entry_id)
        return final_lines, errors
