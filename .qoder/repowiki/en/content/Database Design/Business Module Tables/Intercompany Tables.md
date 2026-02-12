# Intercompany Tables

<cite>
**Referenced Files in This Document**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py)
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py)
- [royalty_repository.py](file://app/modules/intercompany/repositories/royalty_repository.py)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py)
- [royalty_calculation_service.py](file://app/modules/intercompany/services/royalty_calculation_service.py)
- [royalty_approval_service.py](file://app/modules/intercompany/services/royalty_approval_service.py)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py)
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py)
- [intercompany_schemas.py](file://app/modules/intercompany/schemas/intercompany_schemas.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the Intercompany tables and workflows that manage cross-entity transactions and royalty calculations. It covers:
- Intercompany Transfer table and cash movements
- Intercompany Balance table and account tracking
- Royalty Agreement and Calculation tables, plus the royalty approval workflow and posting to journal entries
- Validation rules, transfer categorization, and consolidation implications
- Impact on financial reporting and tax considerations

## Project Structure
The intercompany domain is organized by concerns:
- Models define the persistent entities and relationships
- Repositories encapsulate data access and queries
- Services orchestrate business logic and integrate with other modules (general ledger, treasury)
- APIs expose routes for CRUD, posting, and reconciliation
- Schemas validate request/response payloads

```mermaid
graph TB
subgraph "Models"
ITM["IntercompanyTransfer<br/>(intercompany_transfer_model.py)"]
IBM["IntercompanyBalance<br/>(intercompany_balance_model.py)"]
RA["RoyaltyAgreement<br/>(royalty_model.py)"]
RC["RoyaltyCalculation<br/>(royalty_model.py)"]
end
subgraph "Repositories"
ITR["IntercompanyTransferRepository<br/>(intercompany_transfer_repository.py)"]
IBr["IntercompanyBalanceRepository<br/>(intercompany_balance_repository.py)"]
RAr["RoyaltyAgreementRepository<br/>(royalty_repository.py)"]
RCr["RoyaltyCalculationRepository<br/>(royalty_repository.py)"]
end
subgraph "Services"
ITS["IntercompanyTransferService<br/>(intercompany_transfer_service.py)"]
IRS["IntercompanyReconciliationService<br/>(intercompany_reconciliation_service.py)"]
RCS["RoyaltyCalculationService<br/>(royalty_calculation_service.py)"]
RAS["RoyaltyApprovalService<br/>(royalty_approval_service.py)"]
end
subgraph "API"
ITRT["Intercompany Transfer Routes<br/>(intercompany_transfer_routes.py)"]
RR["Royalty Routes<br/>(royalty_routes.py)"]
end
ITM --> ITR
IBM --> IBr
RA --> RAr
RC --> RCr
ITR --> ITS
IBr --> IRS
RAr --> RCS
RCr --> RCS
RCr --> RAS
ITRT --> ITS
RR --> RCS
RR --> RAS
```

**Diagram sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py#L27-L98)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L12-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L14-L55)
- [royalty_repository.py](file://app/modules/intercompany/repositories/royalty_repository.py#L15-L107)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L17-L232)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L14-L168)
- [royalty_calculation_service.py](file://app/modules/intercompany/services/royalty_calculation_service.py#L21-L202)
- [royalty_approval_service.py](file://app/modules/intercompany/services/royalty_approval_service.py#L25-L254)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L18-L179)
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py#L29-L269)

**Section sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L1-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L1-L39)
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py#L1-L98)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L1-L179)
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py#L1-L269)

## Core Components
This section documents the three core tables and their relationships.

### Intercompany Transfer Table
- Purpose: Records cross-entity cash and non-cash movements (e.g., CASH, ROYALTY, LOAN).
- Key fields:
  - Identifiers: from_entity_id, to_entity_id, transfer_date, amount, currency
  - Classification: transfer_type (e.g., CASH, ROYALTY)
  - Reference: reference_number, description
  - Treasury linkage: from_bank_account_id, to_bank_account_id, from_bank_transaction_id, to_bank_transaction_id
  - Journal entries: from_entity_je_id, to_entity_je_id
  - Reconciliation: is_reconciled, reconciled_at

```mermaid
erDiagram
INTERCOMPANY_TRANSFER {
uuid id PK
uuid from_entity_id FK
uuid to_entity_id FK
date transfer_date
numeric amount
string currency
string transfer_type
text description
string reference_number
uuid from_bank_account_id FK
uuid to_bank_account_id FK
uuid from_bank_transaction_id FK
uuid to_bank_transaction_id FK
uuid from_entity_je_id FK
uuid to_entity_je_id FK
boolean is_reconciled
date reconciled_at
}
LEGAL_ENTITY ||--o{ INTERCOMPANY_TRANSFER : "from_entity"
LEGAL_ENTITY ||--o{ INTERCOMPANY_TRANSFER : "to_entity"
TREASURY_BANK_ACCOUNT ||--o{ INTERCOMPANY_TRANSFER : "from_account"
TREASURY_BANK_ACCOUNT ||--o{ INTERCOMPANY_TRANSFER : "to_account"
TREASURY_BANK_TRANSACTION ||--o{ INTERCOMPANY_TRANSFER : "from_transaction"
TREASURY_BANK_TRANSACTION ||--o{ INTERCOMPANY_TRANSFER : "to_transaction"
JOURNAL_ENTRY ||--o{ INTERCOMPANY_TRANSFER : "from_je"
JOURNAL_ENTRY ||--o{ INTERCOMPANY_TRANSFER : "to_je"
```

**Diagram sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L59)

**Section sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L59)

### Intercompany Balance Table
- Purpose: Stores balance snapshots between entity pairs as of a specific date, supporting receivable/payable tracking.
- Key fields:
  - from_entity_id, to_entity_id, as_of_date, balance_type (NET, RECEIVABLE, PAYABLE), balance_amount, currency
  - Unique constraint ensures one snapshot per entity pair/date/type

```mermaid
erDiagram
INTERCOMPANY_BALANCE {
uuid id PK
uuid from_entity_id FK
uuid to_entity_id FK
date as_of_date
enum balance_type
numeric balance_amount
string currency
}
LEGAL_ENTITY ||--o{ INTERCOMPANY_BALANCE : "from_entity"
LEGAL_ENTITY ||--o{ INTERCOMPANY_BALANCE : "to_entity"
INTERCOMPANY_BALANCE o|--|| BALANCE_TYPE : "balance_type"
```

**Diagram sources**
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)

**Section sources**
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)

### Royalty Tables
- RoyaltyAgreement: Defines the terms between entities (from_entity_id, to_entity_id), basis (REVENUE, RECOGNIZED_REVENUE, COLLECTED_REVENUE, FIXED), rate/fixed_amount, currency, effective dates, and activity flag.
- RoyaltyCalculation: Per-period calculation with revenue bases, calculated_amount, currency, and approval workflow fields (status, submitted/approved/rejected timestamps and actors, decision_reason, row_version), plus legacy posting fields and intercompany_transfer_id linkage.

```mermaid
erDiagram
ROYALTY_AGREEMENT {
uuid id PK
uuid from_entity_id FK
uuid to_entity_id FK
string agreement_code UK
string agreement_name
enum basis
numeric rate
numeric fixed_amount
date effective_from
date effective_to
string currency
boolean is_active
text description
}
ROYALTY_CALCULATION {
uuid id PK
uuid royalty_agreement_id FK
date period_start
date period_end
numeric revenue_base
numeric recognized_revenue_base
numeric collected_revenue_base
numeric calculated_amount
string currency
enum status
uuid submitted_by
timestamptz submitted_at
uuid approved_by
timestamptz approved_at
uuid rejected_by
timestamptz rejected_at
text decision_reason
int row_version
boolean is_posted
timestamptz posted_at
uuid posted_by
uuid journal_entry_id FK
uuid intercompany_transfer_id FK
}
ROYALTY_AGREEMENT ||--o{ ROYALTY_CALCULATION : "calculations"
LEGAL_ENTITY ||--o{ ROYALTY_AGREEMENT : "from_entity"
LEGAL_ENTITY ||--o{ ROYALTY_AGREEMENT : "to_entity"
JOURNAL_ENTRY ||--o{ ROYALTY_CALCULATION : "journal_entry"
INTERCOMPANY_TRANSFER ||--o{ ROYALTY_CALCULATION : "intercompany_transfer"
```

**Diagram sources**
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py#L27-L98)

**Section sources**
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py#L27-L98)

## Architecture Overview
The intercompany subsystem integrates with general ledger and treasury modules to post journal entries and link to bank accounts/transactions. The service layer enforces business rules, while repositories encapsulate persistence.

```mermaid
graph TB
Client["Client"]
API_IC["Intercompany Transfer Routes"]
API_R["Royalty Routes"]
SVC_IC["IntercompanyTransferService"]
SVC_RC["RoyaltyCalculationService"]
SVC_RA["RoyaltyApprovalService"]
SVC_IR["IntercompanyReconciliationService"]
REP_IC["IntercompanyTransferRepository"]
REP_IB["IntercompanyBalanceRepository"]
REP_RA["RoyaltyAgreementRepository"]
REP_RC["RoyaltyCalculationRepository"]
GL["General Ledger (Books, Journal Entries)"]
TREAS["Treasury (Bank Accounts, Transactions)"]
Client --> API_IC
Client --> API_R
API_IC --> SVC_IC
API_R --> SVC_RC
API_R --> SVC_RA
SVC_IC --> REP_IC
SVC_IC --> GL
SVC_IC --> TREAS
SVC_RC --> REP_RC
SVC_RC --> REP_RA
SVC_RC --> SVC_IC
SVC_RA --> REP_RC
SVC_IR --> REP_IC
SVC_IR --> REP_IB
```

**Diagram sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L18-L179)
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py#L29-L269)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L17-L232)
- [royalty_calculation_service.py](file://app/modules/intercompany/services/royalty_calculation_service.py#L21-L202)
- [royalty_approval_service.py](file://app/modules/intercompany/services/royalty_approval_service.py#L25-L254)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L14-L168)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L12-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L14-L55)
- [royalty_repository.py](file://app/modules/intercompany/repositories/royalty_repository.py#L15-L107)

## Detailed Component Analysis

### Intercompany Transfer Service and Posting
- Creation validates entities differ, persists the transfer, and sets reconciliation flags.
- Posting creates dual journal entries (accrual books) with intercompany accounts and optional cash/bank accounts, then updates the transfer with journal entry IDs.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "Intercompany Transfer Routes"
participant Svc as "IntercompanyTransferService"
participant Repo as "IntercompanyTransferRepository"
participant GL as "JournalEntryService"
participant Acc as "GL Account Mapping"
participant Tre as "Treasury Entities"
Client->>API : POST /intercompany/transfers
API->>Svc : create_transfer(...)
Svc->>Repo : create(...)
Repo-->>Svc : transfer
Svc-->>API : transfer
Client->>API : POST /intercompany/transfers/{id}/post
API->>Svc : post_transfer(id, posted_by)
Svc->>GL : create_draft_entry(from_book,...)
Svc->>Acc : get INTERCO_PAYABLE
Svc->>GL : add_line(Dr Interco Payable)
Svc->>Acc : get CASH_BANK (optional)
Svc->>GL : add_line(Cr Cash/Bank)
Svc->>GL : post_entry(source_key=...)
Svc->>GL : create_draft_entry(to_book,...)
Svc->>Acc : get INTERCO_RECEIVABLE
Svc->>GL : add_line(Cr Interco Receivable)
Svc->>Acc : get CASH_BANK (optional)
Svc->>GL : add_line(Debit Cash/Bank)
Svc->>GL : post_entry(source_key=...)
Svc->>Repo : update(from_entity_je_id, to_entity_je_id)
Repo-->>Svc : ok
Svc-->>API : (from_je_id, to_je_id)
```

**Diagram sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L48-L104)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L28-L219)

**Section sources**
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L28-L219)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L48-L104)

### Intercompany Reconciliation and Balance Tracking
- Calculates net balance between entity pairs up to a date.
- Creates or updates a balance snapshot with RECEIVABLE/PAYABLE/NET classification.
- Supports reconciliation marking and generating a reconciliation report.

```mermaid
flowchart TD
Start(["Start"]) --> Calc["Calculate Net Balance"]
Calc --> Type{"Balance > 0 ?"}
Type --> |Yes| SetRecv["Set BalanceType = RECEIVABLE"]
Type --> |No| Type2{"Balance < 0 ?"}
Type2 --> |Yes| SetPay["Set BalanceType = PAYABLE"]
Type2 --> |No| SetNet["Set BalanceType = NET"]
SetRecv --> Snap["Create/Update Balance Snapshot"]
SetPay --> Snap
SetNet --> Snap
Snap --> End(["End"])
```

**Diagram sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L93)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L77-L101)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)

**Section sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L168)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L77-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L20-L55)

### Royalty Calculation Mechanics
- Determines revenue base depending on basis (RECOGNIZED_REVENUE, COLLECTED_REVENUE, REVENUE).
- Computes calculated_amount using rate or fixed amount.
- Persists the calculation and supports posting as an intercompany transfer.

```mermaid
flowchart TD
A["Start"] --> B["Load Agreement"]
B --> C{"Agreement Active?"}
C --> |No| E["Error: Inactive Agreement"]
C --> |Yes| D["Check Existing Calculation"]
D --> F{"Exists?"}
F --> |Yes| G["Return Existing"]
F --> |No| H["Compute Revenue Base(s)"]
H --> I{"Basis = FIXED?"}
I --> |Yes| J["calculated_amount = fixed_amount"]
I --> |No| K["calculated_amount = base × rate%"]
J --> L["Create Calculation Record"]
K --> L
L --> M["Commit and Return"]
```

**Diagram sources**
- [royalty_calculation_service.py](file://app/modules/intercompany/services/royalty_calculation_service.py#L31-L104)

**Section sources**
- [royalty_calculation_service.py](file://app/modules/intercompany/services/royalty_calculation_service.py#L31-L104)

### Royalty Approval Workflow
- State machine: DRAFT → PENDING_APPROVAL → APPROVED/REJECTED.
- Enforces SoD checks and row-version optimistic locking.
- Logs audit actions.

```mermaid
stateDiagram-v2
[*] --> DRAFT
DRAFT --> PENDING_APPROVAL : "submit_for_approval()"
PENDING_APPROVAL --> APPROVED : "approve()"
PENDING_APPROVAL --> REJECTED : "reject()"
APPROVED --> [*]
REJECTED --> [*]
```

**Diagram sources**
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py#L18-L25)
- [royalty_approval_service.py](file://app/modules/intercompany/services/royalty_approval_service.py#L33-L231)

**Section sources**
- [royalty_approval_service.py](file://app/modules/intercompany/services/royalty_approval_service.py#L33-L231)
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py#L18-L25)

### Royalty Posting to Journal Entries
- Posts royalty calculation as an intercompany transfer with transfer_type set to ROYALTY.
- Creates dual journal entries and updates the calculation with journal entry and transfer IDs.

```mermaid
sequenceDiagram
participant API as "Royalty Routes"
participant RCS as "RoyaltyCalculationService"
participant ITS as "IntercompanyTransferService"
participant Repo as "Repositories"
participant GL as "JournalEntryService"
API->>RCS : post_royalty(calculation_id, posted_by)
RCS->>Repo : get_by_id(calculation_id)
RCS->>ITS : create_transfer(..., transfer_type="ROYALTY")
ITS->>GL : create/post dual entries
RCS->>Repo : update(is_posted, posted_at, journal_entry_id, intercompany_transfer_id)
```

**Diagram sources**
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py#L200-L256)
- [royalty_calculation_service.py](file://app/modules/intercompany/services/royalty_calculation_service.py#L160-L202)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L72-L219)

**Section sources**
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py#L200-L256)
- [royalty_calculation_service.py](file://app/modules/intercompany/services/royalty_calculation_service.py#L160-L202)

## Dependency Analysis
- Models define foreign keys to legal entities, journal entries, and treasury entities.
- Repositories depend on SQLAlchemy async sessions and encapsulate queries.
- Services orchestrate cross-module dependencies (books, periods, GL mapping).
- APIs depend on schemas for validation and on idempotency for safe reprocessing.

```mermaid
graph LR
ITM["IntercompanyTransfer"] --> ITR["IntercompanyTransferRepository"]
IBM["IntercompanyBalance"] --> IBr["IntercompanyBalanceRepository"]
RA["RoyaltyAgreement"] --> RAr["RoyaltyAgreementRepository"]
RC["RoyaltyCalculation"] --> RCr["RoyaltyCalculationRepository"]
ITR --> ITS["IntercompanyTransferService"]
IBr --> IRS["IntercompanyReconciliationService"]
RAr --> RCS["RoyaltyCalculationService"]
RCr --> RCS
RCr --> RAS["RoyaltyApprovalService"]
ITRT["IntercompanyTransferRoutes"] --> ITS
RR["RoyaltyRoutes"] --> RCS
RR --> RAS
```

**Diagram sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py#L27-L98)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L12-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L14-L55)
- [royalty_repository.py](file://app/modules/intercompany/repositories/royalty_repository.py#L15-L107)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L18-L179)
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py#L29-L269)

**Section sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)
- [royalty_model.py](file://app/modules/intercompany/models/royalty_model.py#L27-L98)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L18-L179)
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py#L29-L269)

## Performance Considerations
- Indexes on frequently filtered columns (entity IDs, dates, reconciliation flags) improve query performance for lists and balances.
- Batch operations for reconciliation and balance snapshots reduce repeated scans.
- Idempotency keys prevent duplicate postings and redundant journal entries.
- Consider partitioning or materialized summaries for large-scale intercompany reporting.

## Troubleshooting Guide
Common issues and resolutions:
- Missing ACCRUAL book for an entity during posting: ensure books are configured per legal entity.
- Account mapping missing: verify GL account mappings for INTERCO_PAYABLE, INTERCO_RECEIVABLE, and CASH_BANK.
- Duplicate posting attempts: rely on idempotency keys and source keys to avoid duplicates.
- Reconciliation mismatches: use reconciliation report and mark transfers as reconciled to align balances.
- Approval errors: confirm SoD compliance and row version freshness before approvals.

**Section sources**
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L85-L122)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L94-L168)
- [royalty_approval_service.py](file://app/modules/intercompany/services/royalty_approval_service.py#L128-L141)

## Conclusion
The intercompany subsystem provides robust mechanisms to record cross-entity transfers, track balances, and automate royalty calculations with approval workflows and dual journal entries. Proper configuration of books, mappings, and adherence to validation and reconciliation processes ensures accurate consolidation and reporting.

## Appendices

### Intercompany Transaction Validation Rules
- Entities must differ for transfers.
- Agreements must be active for calculations.
- Fixed basis requires a fixed amount.
- Approval workflow requires proper SoD checks and row version handling.

**Section sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L42-L45)
- [royalty_routes.py](file://app/modules/intercompany/api/routes/royalty_routes.py#L45-L48)
- [royalty_approval_service.py](file://app/modules/intercompany/services/royalty_approval_service.py#L54-L58)

### Transfer Categorization and Consolidation Implications
- Intercompany vs intra-entity vs external:
  - Intercompany: from_entity_id ≠ to_entity_id; recorded with intercompany accounts and reconciled.
  - Intra-entity: from_entity_id = to_entity_id; validated at creation.
  - External: not modeled here; typically handled via AR/AP or treasury modules.
- Consolidation:
  - Intercompany balances and transfers must be eliminated in consolidated financial statements.
  - Dual journal entries ensure proper reversal entries per entity’s books.

**Section sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L51-L58)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L58-L72)

### Financial Reporting and Tax Considerations
- Dual journal entries per entity ensure local reporting accuracy.
- Intercompany balances support monthly/quarterly reconciliations and management reporting.
- Tax jurisdictions may require separate intercompany documentation; ensure adequate descriptions and reference numbers for audit trails.

**Section sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L128-L133)
- [intercompany_schemas.py](file://app/modules/intercompany/schemas/intercompany_schemas.py#L9-L46)