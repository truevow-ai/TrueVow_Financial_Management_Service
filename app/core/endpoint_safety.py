"""Endpoint Safety Configuration for FAILED Retry and TTL

Maps each endpoint to:
1. Whether it's safe to auto-retry FAILED requests
2. Expected handler runtime (for TTL calculation)
"""
from app.core.endpoint_keys import (
    JE_POST, JE_REVERSE,
    AP_BILL_POST,
    PAYROLL_POST, PAYROLL_REVERSE,
    ROYALTY_POST, IC_TRANSFER_POST,
    AR_INVOICE_POST,
    PERIOD_LOCK,
    TREASURY_SYNC_POST_TX, TREASURY_SYNC,
    BANK_TX_IMPORT,
    SETTLEMENT_CREATE, SETTLEMENT_STRIPE_IMPORT, SETTLEMENT_TELR_IMPORT,
    RECONCILIATION_CLOSE, RECONCILIATION_ADJ_POST,
    BILLING_SYNC
)

# Endpoints that are safe to auto-retry FAILED requests
# Safe = has business-level uniqueness (source_key, external_id, etc.) that prevents duplicates
SAFE_TO_RETRY_FAILED = {
    # Journal Entry - has source_key unique constraint
    JE_POST: True,  # source_key = "JE:POST:{entry_id}" prevents duplicates
    JE_REVERSE: True,  # source_key = "JE:REVERSE:{entry_id}" prevents duplicates
    
    # AP Bill - has source_key
    AP_BILL_POST: True,  # source_key = "AP_BILL:POST:{bill_id}" prevents duplicates
    
    # Payroll - has source_key
    PAYROLL_POST: True,  # source_key = "PAYROLL:POST:{run_id}" prevents duplicates
    PAYROLL_REVERSE: True,  # source_key = "PAYROLL:REVERSE:{run_id}" prevents duplicates
    
    # Royalty - has source_key
    ROYALTY_POST: True,  # source_key = "ROYALTY:POST:{calculation_id}" prevents duplicates
    
    # Intercompany Transfer - has source_key
    IC_TRANSFER_POST: True,  # source_key = "IC_TRANSFER:POST:{transfer_id}" prevents duplicates
    
    # AR Invoice - has source_key
    AR_INVOICE_POST: True,  # source_key = "AR_INVOICE:POST:{invoice_id}" prevents duplicates
    
    # Period Lock - idempotent by design (locking same period twice is safe)
    PERIOD_LOCK: True,  # Locking is idempotent
    
    # Treasury Sync - uses sync_batch_id for uniqueness
    TREASURY_SYNC: True,  # Uses sync_batch_id to prevent duplicate syncs
    TREASURY_SYNC_POST_TX: True,  # Uses source_key for posted transactions
    
    # Bank TX Import - uses file_hash + external_id for uniqueness
    BANK_TX_IMPORT: True,  # external_id unique constraint prevents duplicate imports
    
    # Settlement - uses external_settlement_id for uniqueness
    SETTLEMENT_CREATE: True,  # external_settlement_id unique constraint
    SETTLEMENT_STRIPE_IMPORT: True,  # external_payout_id unique constraint
    SETTLEMENT_TELR_IMPORT: True,  # external_payout_id unique constraint
    
    # Reconciliation - idempotent by design
    RECONCILIATION_CLOSE: True,  # Closing same session twice is safe (no side effects)
    RECONCILIATION_ADJ_POST: True,  # source_key = "RECON_ADJ:POST:{batch_id}" prevents duplicates
    
    # Billing Sync - uses sync cursor for uniqueness
    BILLING_SYNC: True,  # Uses since_cursor to prevent duplicate syncs
}


def is_safe_to_retry_failed(endpoint_key: str) -> bool:
    """
    Check if an endpoint is safe to auto-retry FAILED requests.
    
    Returns True if the endpoint has business-level uniqueness guards
    that prevent duplicate side effects.
    """
    return SAFE_TO_RETRY_FAILED.get(endpoint_key, False)


# Endpoint-specific TTL (in seconds)
# TTL should be 2-3x expected handler runtime to account for slow systems
ENDPOINT_TTL_SECONDS = {
    # Posting endpoints (fast: 1-5 seconds typical)
    JE_POST: 60,  # 1 minute (30s typical, 2x buffer)
    JE_REVERSE: 60,
    AP_BILL_POST: 60,
    PAYROLL_POST: 90,  # Slightly longer (may process many employees)
    PAYROLL_REVERSE: 90,
    ROYALTY_POST: 60,
    IC_TRANSFER_POST: 60,
    AR_INVOICE_POST: 60,
    PERIOD_LOCK: 30,  # Very fast (just updates period status)
    RECONCILIATION_CLOSE: 30,  # Fast (no side effects)
    RECONCILIATION_ADJ_POST: 60,
    
    # Import/Sync endpoints (slow: 30 seconds to 10+ minutes)
    BANK_TX_IMPORT: 600,  # 10 minutes (CSV imports can be large)
    TREASURY_SYNC: 900,  # 15 minutes (full sync can take time)
    TREASURY_SYNC_POST_TX: 300,  # 5 minutes (posting batches)
    SETTLEMENT_CREATE: 60,  # Fast (single settlement)
    SETTLEMENT_STRIPE_IMPORT: 120,  # 2 minutes (may process multiple)
    SETTLEMENT_TELR_IMPORT: 120,
    BILLING_SYNC: 900,  # 15 minutes (can sync large date ranges)
}


def get_lock_ttl_seconds(endpoint_key: str) -> int:
    """
    Get the TTL (time-to-live) in seconds for PENDING locks for an endpoint.
    
    TTL is set to 2-3x expected handler runtime to account for:
    - Slow database queries
    - Network latency
    - System load
    
    Returns:
        TTL in seconds (default: 120 if endpoint not found)
    """
    return ENDPOINT_TTL_SECONDS.get(endpoint_key, 120)  # Default 2 minutes
