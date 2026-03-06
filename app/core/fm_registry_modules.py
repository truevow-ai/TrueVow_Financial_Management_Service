"""
FM Service Module Definitions for Service Registry

All modules, endpoints, and events built from day one.
Registered with Service Registry on startup for cross-service discovery.
"""

# ============================================================
# FM SERVICE MODULES - Complete list of all built functionality
# ============================================================

FM_MODULES = [
    # ============================================================
    # GENERAL LEDGER MODULE
    # ============================================================
    {
        "module_name": "general_ledger",
        "module_version": "1.0.0",
        "description": "Core accounting: chart of accounts, periods, journal entries, bank reconciliation",
        "endpoints": [
            {"path": "/api/v1/entities", "method": "GET", "description": "List legal entities"},
            {"path": "/api/v1/entities", "method": "POST", "description": "Create legal entity"},
            {"path": "/api/v1/entities/{id}", "method": "GET", "description": "Get legal entity"},
            {"path": "/api/v1/books/{book_id}/accounts", "method": "GET", "description": "List chart of accounts"},
            {"path": "/api/v1/books/{book_id}/accounts", "method": "POST", "description": "Create GL account"},
            {"path": "/api/v1/books/{book_id}/accounts/{id}", "method": "GET", "description": "Get GL account"},
            {"path": "/api/v1/books/{book_id}/accounts/{id}", "method": "PUT", "description": "Update GL account"},
            {"path": "/api/v1/books/{book_id}/periods", "method": "GET", "description": "List accounting periods"},
            {"path": "/api/v1/books/{book_id}/periods", "method": "POST", "description": "Create accounting period"},
            {"path": "/api/v1/books/{book_id}/periods/{id}/close", "method": "POST", "description": "Close period"},
            {"path": "/api/v1/books/{book_id}/journal-entries", "method": "GET", "description": "List journal entries"},
            {"path": "/api/v1/books/{book_id}/journal-entries", "method": "POST", "description": "Create journal entry"},
            {"path": "/api/v1/books/{book_id}/journal-entries/{id}", "method": "GET", "description": "Get journal entry"},
            {"path": "/api/v1/books/{book_id}/journal-entries/{id}/post", "method": "POST", "description": "Post journal entry"},
            {"path": "/api/v1/books/{book_id}/journal-entries/{id}/reverse", "method": "POST", "description": "Reverse journal entry"},
            {"path": "/api/v1/books/{book_id}/reconciliations", "method": "GET", "description": "List reconciliations"},
            {"path": "/api/v1/books/{book_id}/reconciliations", "method": "POST", "description": "Create reconciliation"},
            {"path": "/api/v1/books/{book_id}/reconciliations/{id}/match", "method": "POST", "description": "Match transactions"},
            {"path": "/api/v1/books/{book_id}/reconciliations/{id}/complete", "method": "POST", "description": "Complete reconciliation"},
        ],
        "events_published": [
            {"event": "journal_entry.created", "description": "Journal entry created"},
            {"event": "journal_entry.posted", "description": "Journal entry posted to GL"},
            {"event": "journal_entry.reversed", "description": "Journal entry reversed"},
            {"event": "period.closed", "description": "Accounting period closed"},
            {"event": "reconciliation.completed", "description": "Bank reconciliation completed"},
        ],
        "events_consumed": [],
    },
    # ============================================================
    # TREASURY MODULE
    # ============================================================
    {
        "module_name": "treasury",
        "module_version": "1.0.0",
        "description": "Treasury: bank accounts, transactions, transfers, FX conversions, settlements",
        "endpoints": [
            {"path": "/api/v1/bank-accounts", "method": "GET", "description": "List bank accounts"},
            {"path": "/api/v1/bank-accounts", "method": "POST", "description": "Create bank account"},
            {"path": "/api/v1/bank-accounts/{id}", "method": "GET", "description": "Get bank account"},
            {"path": "/api/v1/bank-accounts/{id}", "method": "PUT", "description": "Update bank account"},
            {"path": "/api/v1/bank-accounts/{id}/balance", "method": "GET", "description": "Get account balance"},
            {"path": "/api/v1/bank-transactions", "method": "GET", "description": "List bank transactions"},
            {"path": "/api/v1/bank-transactions", "method": "POST", "description": "Create bank transaction"},
            {"path": "/api/v1/bank-transactions/{id}", "method": "GET", "description": "Get bank transaction"},
            {"path": "/api/v1/transfers", "method": "GET", "description": "List transfers"},
            {"path": "/api/v1/transfers", "method": "POST", "description": "Create transfer"},
            {"path": "/api/v1/transfers/{id}", "method": "GET", "description": "Get transfer"},
            {"path": "/api/v1/fx/conversions", "method": "GET", "description": "List FX conversions"},
            {"path": "/api/v1/fx/conversions", "method": "POST", "description": "Create FX conversion"},
            {"path": "/api/v1/fx/conversions/{id}", "method": "GET", "description": "Get FX conversion"},
            {"path": "/api/v1/settlements", "method": "GET", "description": "List settlements"},
            {"path": "/api/v1/settlements", "method": "POST", "description": "Create settlement"},
            {"path": "/api/v1/settlements/{id}", "method": "GET", "description": "Get settlement"},
        ],
        "events_published": [
            {"event": "bank_account.created", "description": "Bank account created"},
            {"event": "bank_transaction.created", "description": "Bank transaction recorded"},
            {"event": "transfer.initiated", "description": "Transfer initiated"},
            {"event": "transfer.completed", "description": "Transfer completed"},
            {"event": "fx_conversion.executed", "description": "FX conversion executed"},
            {"event": "settlement.created", "description": "Settlement created"},
        ],
        "events_consumed": [],
    },
    # ============================================================
    # ACCOUNTS RECEIVABLE MODULE
    # ============================================================
    {
        "module_name": "accounts_receivable",
        "module_version": "1.0.0",
        "description": "AR: invoices, customers, payments, deferred revenue, billing sync",
        "endpoints": [
            {"path": "/api/v1/books/{book_id}/ar/customers", "method": "GET", "description": "List AR customers"},
            {"path": "/api/v1/books/{book_id}/ar/customers", "method": "POST", "description": "Create AR customer"},
            {"path": "/api/v1/books/{book_id}/ar/customers/{id}", "method": "GET", "description": "Get AR customer"},
            {"path": "/api/v1/books/{book_id}/ar/invoices", "method": "GET", "description": "List AR invoices"},
            {"path": "/api/v1/books/{book_id}/ar/invoices", "method": "POST", "description": "Create AR invoice"},
            {"path": "/api/v1/books/{book_id}/ar/invoices/{id}", "method": "GET", "description": "Get AR invoice"},
            {"path": "/api/v1/books/{book_id}/ar/invoices/{id}/post", "method": "POST", "description": "Post AR invoice"},
            {"path": "/api/v1/books/{book_id}/ar/payments", "method": "GET", "description": "List AR payments"},
            {"path": "/api/v1/books/{book_id}/ar/payments", "method": "POST", "description": "Create AR payment"},
            {"path": "/api/v1/books/{book_id}/ar/aging", "method": "GET", "description": "Get AR aging report"},
            {"path": "/api/v1/books/{book_id}/revrec/schedules", "method": "GET", "description": "List revenue schedules"},
            {"path": "/api/v1/books/{book_id}/revrec/schedules/{id}/recognize", "method": "POST", "description": "Recognize revenue"},
            {"path": "/api/v1/integrations/billing/sync", "method": "POST", "description": "Sync billing data"},
            {"path": "/api/v1/integrations/billing/webhook", "method": "POST", "description": "Billing webhook"},
            {"path": "/api/v1/pricing", "method": "GET", "description": "Get pricing info"},
            {"path": "/api/v1/dashboard/stats", "method": "GET", "description": "Get dashboard statistics"},
        ],
        "events_published": [
            {"event": "ar_customer.created", "description": "AR customer created"},
            {"event": "ar_invoice.created", "description": "AR invoice created"},
            {"event": "ar_invoice.posted", "description": "AR invoice posted"},
            {"event": "ar_payment.received", "description": "AR payment received"},
            {"event": "revenue.recognized", "description": "Revenue recognized"},
        ],
        "events_consumed": [
            {"event": "billing.invoice.paid", "source_service": "tenant_billing"},
            {"event": "billing.subscription.created", "source_service": "tenant_billing"},
        ],
    },
    # ============================================================
    # ACCOUNTS PAYABLE MODULE
    # ============================================================
    {
        "module_name": "accounts_payable",
        "module_version": "1.0.0",
        "description": "AP: vendors, bills, payments, approvals",
        "endpoints": [
            {"path": "/api/v1/books/{book_id}/ap/vendors", "method": "GET", "description": "List AP vendors"},
            {"path": "/api/v1/books/{book_id}/ap/vendors", "method": "POST", "description": "Create AP vendor"},
            {"path": "/api/v1/books/{book_id}/ap/vendors/{id}", "method": "GET", "description": "Get AP vendor"},
            {"path": "/api/v1/books/{book_id}/ap/bills", "method": "GET", "description": "List AP bills"},
            {"path": "/api/v1/books/{book_id}/ap/bills", "method": "POST", "description": "Create AP bill"},
            {"path": "/api/v1/books/{book_id}/ap/bills/{id}", "method": "GET", "description": "Get AP bill"},
            {"path": "/api/v1/books/{book_id}/ap/bills/{id}/approve", "method": "POST", "description": "Approve AP bill"},
            {"path": "/api/v1/books/{book_id}/ap/bills/{id}/pay", "method": "POST", "description": "Pay AP bill"},
            {"path": "/api/v1/books/{book_id}/ap/payments", "method": "GET", "description": "List AP payments"},
            {"path": "/api/v1/books/{book_id}/ap/payments", "method": "POST", "description": "Create AP payment"},
        ],
        "events_published": [
            {"event": "ap_vendor.created", "description": "AP vendor created"},
            {"event": "ap_bill.created", "description": "AP bill created"},
            {"event": "ap_bill.approved", "description": "AP bill approved"},
            {"event": "ap_payment.made", "description": "AP payment made"},
        ],
        "events_consumed": [],
    },
    # ============================================================
    # PAYROLL MODULE
    # ============================================================
    {
        "module_name": "payroll",
        "module_version": "1.0.0",
        "description": "Payroll: runs, components, payment batches",
        "endpoints": [
            {"path": "/api/v1/books/{book_id}/payroll/runs", "method": "GET", "description": "List payroll runs"},
            {"path": "/api/v1/books/{book_id}/payroll/runs", "method": "POST", "description": "Create payroll run"},
            {"path": "/api/v1/books/{book_id}/payroll/runs/{id}", "method": "GET", "description": "Get payroll run"},
            {"path": "/api/v1/books/{book_id}/payroll/runs/{id}/approve", "method": "POST", "description": "Approve payroll run"},
            {"path": "/api/v1/books/{book_id}/payroll/runs/{id}/process", "method": "POST", "description": "Process payroll run"},
            {"path": "/api/v1/books/{book_id}/payroll/components", "method": "GET", "description": "List payroll components"},
            {"path": "/api/v1/books/{book_id}/payroll/components", "method": "POST", "description": "Create payroll component"},
            {"path": "/api/v1/books/{book_id}/payroll/employees", "method": "GET", "description": "List payroll employees"},
            {"path": "/api/v1/books/{book_id}/payroll/adjustments", "method": "GET", "description": "List payroll adjustments"},
            {"path": "/api/v1/books/{book_id}/payroll/batches", "method": "GET", "description": "List payment batches"},
            {"path": "/api/v1/books/{book_id}/payroll/batches", "method": "POST", "description": "Create payment batch"},
        ],
        "events_published": [
            {"event": "payroll_run.created", "description": "Payroll run created"},
            {"event": "payroll_run.approved", "description": "Payroll run approved"},
            {"event": "payroll_run.processed", "description": "Payroll run processed"},
            {"event": "payment_batch.created", "description": "Payment batch created"},
        ],
        "events_consumed": [
            {"event": "employee.hired", "source_service": "cs_core"},
            {"event": "employee.terminated", "source_service": "cs_core"},
        ],
    },
    # ============================================================
    # INTERCOMPANY MODULE
    # ============================================================
    {
        "module_name": "intercompany",
        "module_version": "1.0.0",
        "description": "Intercompany: transfers, royalties, eliminations, reconciliation",
        "endpoints": [
            {"path": "/api/v1/intercompany/transfers", "method": "GET", "description": "List intercompany transfers"},
            {"path": "/api/v1/intercompany/transfers", "method": "POST", "description": "Create intercompany transfer"},
            {"path": "/api/v1/intercompany/transfers/{id}", "method": "GET", "description": "Get intercompany transfer"},
            {"path": "/api/v1/intercompany/transfers/{id}/settle", "method": "POST", "description": "Settle intercompany transfer"},
            {"path": "/api/v1/intercompany/royalties", "method": "GET", "description": "List royalties"},
            {"path": "/api/v1/intercompany/royalties", "method": "POST", "description": "Create royalty"},
            {"path": "/api/v1/intercompany/royalties/{id}", "method": "GET", "description": "Get royalty"},
            {"path": "/api/v1/intercompany/royalties/{id}/calculate", "method": "POST", "description": "Calculate royalty"},
            {"path": "/api/v1/intercompany/reconciliation", "method": "GET", "description": "List IC reconciliations"},
            {"path": "/api/v1/intercompany/reconciliation", "method": "POST", "description": "Create IC reconciliation"},
            {"path": "/api/v1/intercompany/reconciliation/{id}/eliminate", "method": "POST", "description": "Create elimination entries"},
        ],
        "events_published": [
            {"event": "intercompany_transfer.created", "description": "Intercompany transfer created"},
            {"event": "intercompany_transfer.settled", "description": "Intercompany transfer settled"},
            {"event": "royalty.calculated", "description": "Royalty calculated"},
            {"event": "elimination.entries_created", "description": "Elimination entries created"},
        ],
        "events_consumed": [],
    },
    # ============================================================
    # REPORTING MODULE
    # ============================================================
    {
        "module_name": "reporting",
        "module_version": "1.0.0",
        "description": "Financial reporting: trial balance, P&L, balance sheet, cash flow",
        "endpoints": [
            {"path": "/api/v1/reports/trial-balance", "method": "GET", "description": "Generate trial balance"},
            {"path": "/api/v1/reports/pl", "method": "GET", "description": "Generate profit & loss"},
            {"path": "/api/v1/reports/balance-sheet", "method": "GET", "description": "Generate balance sheet"},
            {"path": "/api/v1/reports/cash-flow", "method": "GET", "description": "Generate cash flow statement"},
            {"path": "/api/v1/reports/gl-detail", "method": "GET", "description": "Generate GL detail report"},
            {"path": "/api/v1/reports/ar-aging", "method": "GET", "description": "Generate AR aging report"},
            {"path": "/api/v1/reports/ap-aging", "method": "GET", "description": "Generate AP aging report"},
            {"path": "/api/v1/reports", "method": "GET", "description": "List available reports"},
            {"path": "/api/v1/reports/{id}", "method": "GET", "description": "Get report by ID"},
            {"path": "/api/v1/reports/{id}/export", "method": "GET", "description": "Export report"},
        ],
        "events_published": [
            {"event": "report.generated", "description": "Financial report generated"},
            {"event": "report.exported", "description": "Report exported"},
        ],
        "events_consumed": [],
    },
]

# ============================================================
# FM SERVICE INTEGRATIONS
# ============================================================

FM_INTEGRATIONS = [
    {
        "target_service": "tenant_billing",
        "integration_type": "event_subscription",
        "purpose": "Sync billing events to AR",
        "event_triggers": ["billing.invoice.paid", "billing.subscription.created"],
    },
    {
        "target_service": "cs_core",
        "integration_type": "event_subscription",
        "purpose": "Employee events for payroll",
        "event_triggers": ["employee.hired", "employee.terminated"],
    },
    {
        "target_service": "internal_ops",
        "integration_type": "service_registry",
        "purpose": "Service discovery and registration",
        "event_triggers": [],
    },
    {
        "target_service": "fm_frontend",
        "integration_type": "api",
        "purpose": "Frontend UI for financial management",
        "event_triggers": [],
    },
]
