"""Hardcoded endpoint key constants for idempotency

These constants ensure stable endpoint identification regardless of path changes.
Each idempotent endpoint should use its corresponding constant.
"""
# Journal Entry endpoints
JE_POST = "JE_POST"
JE_REVERSE = "JE_REVERSE"

# AP endpoints
AP_BILL_POST = "AP_BILL_POST"

# Payroll endpoints
PAYROLL_POST = "PAYROLL_POST"
PAYROLL_REVERSE = "PAYROLL_REVERSE"

# Intercompany endpoints
ROYALTY_POST = "ROYALTY_POST"
IC_TRANSFER_POST = "IC_TRANSFER_POST"

# AR endpoints
AR_INVOICE_POST = "AR_INVOICE_POST"

# Period endpoints
PERIOD_LOCK = "PERIOD_LOCK"

# Treasury endpoints
TREASURY_SYNC_POST_TX = "TREASURY_SYNC_POST_TX"
TREASURY_SYNC = "TREASURY_SYNC"
BANK_TX_IMPORT = "BANK_TX_IMPORT"

# Settlement endpoints
SETTLEMENT_CREATE = "SETTLEMENT_CREATE"
SETTLEMENT_STRIPE_IMPORT = "SETTLEMENT_STRIPE_IMPORT"
SETTLEMENT_TELR_IMPORT = "SETTLEMENT_TELR_IMPORT"

# Reconciliation endpoints
RECONCILIATION_CLOSE = "RECONCILIATION_CLOSE"
RECONCILIATION_ADJ_POST = "RECONCILIATION_ADJ_POST"

# Billing sync
BILLING_SYNC = "BILLING_SYNC"
