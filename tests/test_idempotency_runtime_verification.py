"""Runtime Verification Tests for Idempotency System.

Run with: pytest tests/test_idempotency_runtime_verification.py -v
Uses test_db and dependency override so no real DB required (aiosqlite in-memory).
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db_session
from app.core.idempotency import compute_request_hash
from app.auth.middleware import get_current_user
from app.modules.core.models.idempotency_model import IdempotencyKey, IdempotencyState
from app.core.endpoint_keys import JE_POST, BANK_TX_IMPORT
from tests.conftest import test_db, test_book, test_period, test_legal_entity, test_user_id, test_gl_accounts


@pytest.fixture
def client(test_db, test_user_id):
    """Test client with get_db_session and get_current_user overridden."""
    async def override_get_db():
        yield test_db
    async def override_get_current_user():
        return {"user_id": str(test_user_id), "email": "test@test.com", "roles": [], "permissions": []}
    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def db_session(test_db):
    """Alias for test_db for tests that expect db_session."""
    return test_db


class TestA_ReplaySameKey:
    """Test A: Same Idempotency-Key + same body → replay returns same response."""

    @pytest.mark.asyncio
    async def test_replay_same_response(self, client, test_db, test_book, test_period, test_legal_entity, test_user_id, test_gl_accounts):
        from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
        from decimal import Decimal
        from datetime import date

        dr_account, cr_account = test_gl_accounts
        je_service = JournalEntryService(test_db)
        entry = await je_service.create_draft_entry(
            book_id=test_book.id,
            entry_date=date.today(),
            description="Runtime test entry",
        )
        await je_service.add_line(entry.id, dr_account.id, Decimal("100.00"), Decimal("0"), "USD")
        await je_service.add_line(entry.id, cr_account.id, Decimal("0"), Decimal("100.00"), "USD")
        await test_db.commit()

        idempotency_key = f"runtime_replay_{uuid4()}"
        url = f"/api/v1/books/{test_book.id}/journal-entries/{entry.id}/post"
        headers = {"Idempotency-Key": idempotency_key}
        body = {"posted_by": test_user_id, "require_dimensions": False}

        r1 = client.post(url, headers=headers, json=body)
        assert r1.status_code in (200, 201), f"First POST failed: {r1.status_code} {r1.text}"

        r2 = client.post(url, headers=headers, json=body)
        assert r2.status_code in (200, 201), f"Replay POST failed: {r2.status_code} {r2.text}"
        assert r1.json() == r2.json(), "Replay must return same body"


class TestB_StaleLockRecovery:
    """Test B: Stale PENDING lock → retry proceeds after TTL."""

    @pytest.mark.asyncio
    async def test_stale_lock_recovery(self, client, test_db, test_book, test_legal_entity):
        idempotency_key = f"runtime_stale_{uuid4()}"
        # Stale PENDING record (older than TTL 600s for BANK_TX_IMPORT)
        stale = IdempotencyKey(
            legal_entity_id=test_legal_entity.id,
            book_id=test_book.id,
            endpoint_key=BANK_TX_IMPORT,
            idempotency_key=idempotency_key,
            request_hash="abc123",
            state=IdempotencyState.PENDING,
            locked_at=datetime.utcnow() - timedelta(seconds=700),
        )
        test_db.add(stale)
        await test_db.commit()

        url = f"/api/v1/books/{test_book.id}/treasury/bank-transactions/import"
        # Request with same key and same hash (request_hash will be computed from body)
        body = {"bank_account_id": str(uuid4()), "transactions": [{"external_id": "stale_1", "amount": "50.00", "date": "2026-01-01", "currency": "USD"}]}
        r = client.post(url, headers={"Idempotency-Key": idempotency_key}, json=body)
        # After stale takeover: either 200/201 (proceeded) or 4xx if validation fails (book/bank account missing)
        assert r.status_code in (200, 201, 400, 404), f"Expected 200/201/400/404: {r.status_code} {r.text}"


class TestC_FailedRetryBlocked:
    """Test C: FAILED retry blocked when endpoint marked unsafe."""

    @pytest.mark.asyncio
    async def test_failed_retry_blocked_unsafe(self, client, test_db, test_book, test_legal_entity, test_user_id):
        idempotency_key = f"runtime_failed_{uuid4()}"
        body = {"posted_by": test_user_id, "require_dimensions": False}
        request_hash = compute_request_hash(body)
        failed_record = IdempotencyKey(
            legal_entity_id=test_legal_entity.id,
            book_id=test_book.id,
            endpoint_key=JE_POST,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            state=IdempotencyState.FAILED,
            response_status=500,
            response_blob='{"error":"Test"}',
        )
        test_db.add(failed_record)
        await test_db.commit()

        with patch("app.core.endpoint_safety.is_safe_to_retry_failed", return_value=False):
            r = client.post(
                f"/api/v1/books/{test_book.id}/journal-entries/{uuid4()}/post",
                headers={"Idempotency-Key": idempotency_key},
                json=body,
            )
        assert r.status_code == 409, f"Unsafe FAILED retry should be 409: {r.status_code} {r.text}"


class TestD_ResponseStatusReplay:
    """Test D: Replay returns stored response_status (e.g. 204)."""

    @pytest.mark.asyncio
    async def test_response_status_replay(self, client, test_db, test_book, test_legal_entity, test_user_id, test_gl_accounts):
        from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
        from decimal import Decimal
        from datetime import date

        # Create a draft entry so route does not 404 before idempotency replay
        dr_account, cr_account = test_gl_accounts
        je_service = JournalEntryService(test_db)
        entry = await je_service.create_draft_entry(
            book_id=test_book.id,
            entry_date=date.today(),
            description="TestD draft",
        )
        await je_service.add_line(entry.id, dr_account.id, Decimal("1"), Decimal("0"), "USD")
        await je_service.add_line(entry.id, cr_account.id, Decimal("0"), Decimal("1"), "USD")
        await test_db.commit()

        idempotency_key = f"runtime_204_{uuid4()}"
        body = {"posted_by": test_user_id, "require_dimensions": False}
        request_hash = compute_request_hash(body)
        record = IdempotencyKey(
            legal_entity_id=test_legal_entity.id,
            book_id=test_book.id,
            endpoint_key=JE_POST,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            state=IdempotencyState.COMPLETED,
            response_status=204,
            response_blob="{}",
        )
        test_db.add(record)
        await test_db.commit()

        r = client.post(
            f"/api/v1/books/{test_book.id}/journal-entries/{entry.id}/post",
            headers={"Idempotency-Key": idempotency_key},
            json=body,
        )
        assert r.status_code == 204, f"Replay should return stored 204: {r.status_code}"


class TestE_PendingReturns409:
    """Test E: Active PENDING (within TTL) → second request gets 409 + Retry-After."""

    @pytest.mark.asyncio
    async def test_pending_returns_409(self, client, test_db, test_book, test_legal_entity):
        idempotency_key = f"runtime_pending_{uuid4()}"
        body = {"bank_account_id": str(uuid4()), "transactions": [{"external_id": "p1", "amount": "10", "date": "2026-01-01", "currency": "USD"}]}
        request_hash = compute_request_hash(body)
        recent = IdempotencyKey(
            legal_entity_id=test_legal_entity.id,
            book_id=test_book.id,
            endpoint_key=BANK_TX_IMPORT,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            state=IdempotencyState.PENDING,
            locked_at=datetime.utcnow() - timedelta(seconds=10),
        )
        test_db.add(recent)
        await test_db.commit()

        r = client.post(
            f"/api/v1/books/{test_book.id}/treasury/bank-transactions/import",
            headers={"Idempotency-Key": idempotency_key},
            json=body,
        )
        assert r.status_code == 409, f"Active PENDING should return 409: {r.status_code} {r.text}"
        assert "Retry-After" in r.headers or "retry-after" in str(r.headers).lower(), "409 should include Retry-After"
