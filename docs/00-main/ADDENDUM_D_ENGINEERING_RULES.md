# ADDENDUM D — "Don't Screw This Up" Engineering Rules (Finance Grade)

**Date:** January 25, 2026  
**Status:** Mandatory Implementation Rules

These are rules the agent must follow or the system will become unfixable.

---

## D1) Money Types & Rounding (Mandatory)

### Rules:
- **Never use float for money.** Use DECIMAL/NUMERIC in DB and Decimal in code.
- **Store currency code on every monetary field.**
- Define per-currency precision table:
  - `currency_code`, `scale` (USD=2, AED=2, PKR=2)
- Define rounding mode in config:
  - `HALF_UP` (default) or `BANKERS`
- Validation balance tolerance:
  - exactly 0.00 in functional currency (preferred)
  - allow tiny tolerance only if multi-currency rounding requires it (config flag)

### Implementation:
```python
# app/core/money.py
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from typing import Dict

CURRENCY_SCALE: Dict[str, int] = {
    "USD": 2,
    "AED": 2,
    "PKR": 2,
    "EUR": 2,
}

ROUNDING_MODE = ROUND_HALF_UP  # or ROUND_HALF_EVEN for BANKERS

def round_money(amount: Decimal, currency: str) -> Decimal:
    scale = CURRENCY_SCALE.get(currency, 2)
    quantizer = Decimal(10) ** -scale
    return amount.quantize(quantizer, rounding=ROUNDING_MODE)
```

---

## D2) Posting Atomicity (Mandatory)

All posting operations must run in a single DB transaction:
- validate
- generate journal lines
- insert journal entry + lines
- mark source object as posted with posted_at/by

**If any step fails → rollback everything.**

### Implementation Pattern:
```python
async def post_journal_entry(...):
    async with session.begin():  # Single transaction
        # 1. Validate
        errors = await validate(...)
        if errors:
            raise ValidationError(errors)
        
        # 2. Generate lines
        lines = generate_lines(...)
        
        # 3. Insert JE + lines
        je = await je_repo.create(...)
        await line_repo.bulk_create(lines)
        
        # 4. Mark source as posted
        await source_repo.mark_posted(source_id, user_id)
        
        # Transaction commits automatically on success
        # Rolls back automatically on any exception
```

---

## D3) Deterministic IDs for System Postings (Mandatory)

For generated postings, compute a stable `posting_key`:
- e.g., `PAYROLL:{run_id}:{book_id}`
- e.g., `REVREC:{schedule_period_id}:{book_id}`
- e.g., `ROYALTY:{period_id}:{from_entity}:{to_entity}:{book_id}`

Store `posting_key` with unique constraint to guarantee idempotency.

### Implementation:
```python
# In JournalEntry model
posting_key = Column(String(255), unique=True, nullable=True, index=True)

# When posting
posting_key = f"{source_service}:{source_type}:{source_id}:{book_id}"
# Check if exists, if yes return existing JE
```

---

## D4) No Silent Deletes

- **Never hard-delete posted objects.**
- Soft-delete drafts is allowed, but keep audit trail.

### Implementation:
```python
# Add to BaseModel
deleted_at = Column(DateTime(timezone=True), nullable=True)
deleted_by = Column(UUID(as_uuid=True), nullable=True)

# Soft delete
async def soft_delete(self, user_id: UUID):
    self.deleted_at = func.now()
    self.deleted_by = user_id
    # Audit log the deletion
```

---

## D5) Migration Discipline

- All schema changes via migrations.
- Add indexes for:
  - `journal_line(book_id, account_id, posted_at)`
  - `source_object_map(source, object_type, external_id, entity_id)`
  - `treasury_bank_transaction(bank_account_id, txn_date, amount, reference_hash)`

### Index Checklist:
- [ ] `journal_line(book_id, account_id, posted_at)` - for GL detail queries
- [ ] `journal_line(book_id, period_id, posted_at)` - for period reports
- [ ] `source_object_map(source, object_type, external_id, entity_id)` - for sync lookups
- [ ] `treasury_bank_transaction(bank_account_id, txn_date, amount)` - for reconciliation
- [ ] `treasury_bank_transaction(reference_hash)` - for duplicate detection
- [ ] `payroll_run(legal_entity_id, pay_period_end, status)` - for payroll queries
- [ ] `reconciliation_session(bank_account_id, period_end, status)` - for reconciliation queries

---

## D6) Error Handling

- Never return generic "500 Internal Server Error" to finance users.
- Return specific error codes:
  - `PERIOD_CLOSED` - Cannot post into closed period
  - `UNBALANCED` - Debits != Credits
  - `MISSING_DIMENSION` - Required dimension missing
  - `DUPLICATE_POSTING` - Posting already exists
  - `SOD_VIOLATION` - Segregation of duties violation
  - `APPROVAL_REQUIRED` - Must be approved before posting

---

## D7) Audit Logging

- Every approval action must log:
  - `PAYROLL_SUBMIT`, `PAYROLL_APPROVE`, `PAYROLL_REJECT`
  - `REC_ADJUSTMENT_SUBMIT`, `REC_ADJUSTMENT_APPROVE`, `REC_ADJUSTMENT_REJECT`
  - `PERIOD_CLOSE_SUBMIT`, `PERIOD_CLOSE_APPROVE`
  - `ROYALTY_SUBMIT`, `ROYALTY_APPROVE`, `ROYALTY_REJECT`
- Every posting must log:
  - `JE_POST`, `PAYROLL_POST`, `REC_ADJUSTMENT_POST`, `ROYALTY_POST`
- Include `before_json` and `after_json` for state transitions.

---

**END OF ADDENDUM D**
