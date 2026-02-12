# Settlement System

<cite>
**Referenced Files in This Document**
- [settlement_model.py](file://app/modules/treasury/models/settlement_model.py)
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py)
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py)
- [settlement_schemas.py](file://app/modules/treasury/schemas/settlement_schemas.py)
- [settlement_repository.py](file://app/modules/treasury/repositories/settlement_repository.py)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py)
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py)
- [bank_transaction_model.py](file://app/modules/treasury/models/bank_transaction_model.py)
- [endpoint_keys.py](file://app/core/endpoint_keys.py)
- [004_fix_settlement_uniqueness.py](file://database/migrations/versions/004_fix_settlement_uniqueness.py)
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
This document describes the Settlement System within the TrueVow Financial Management platform. It covers settlement processing, cash clearing, and reconciliation workflows. The system supports creation of settlements from external payment gateways (Stripe and TELR) and manual entries, validates data integrity, posts journal entries to the CASH book, and integrates with bank reconciliation.

## Project Structure
The Settlement System spans the Treasury module for persistence and APIs, and the General Ledger module for cash posting and reconciliation.

```mermaid
graph TB
subgraph "Treasury Module"
SM["Settlement Model<br/>app/modules/treasury/models/settlement_model.py"]
SR["Settlement Repository<br/>app/modules/treasury/repositories/settlement_repository.py"]
SS["Settlement Service<br/>app/modules/treasury/services/settlement_service.py"]
SROUTES["Settlement Routes<br/>app/modules/treasury/api/routes/settlement_routes.py"]
SSCH["Settlement Schemas<br/>app/modules/treasury/schemas/settlement_schemas.py"]
end
subgraph "General Ledger Module"
CBPS["Cash Book Posting Service<br/>app/modules/general_ledger/services/cash_book_posting_service.py"]
RS["Reconciliation Service<br/>app/modules/general_ledger/services/reconciliation_service.py"]
RM["Reconciliation Model<br/>app/modules/general_ledger/models/reconciliation_model.py"]
end
subgraph "Related Models"
BTM["Bank Transaction Model<br/>app/modules/treasury/models/bank_transaction_model.py"]
end
SROUTES --> SS
SS --> SR
SS --> SM
SS --> BTM
SS --> CBPS
CBPS --> RM
RS --> RM
RS --> BTM
```

**Diagram sources**
- [settlement_model.py](file://app/modules/treasury/models/settlement_model.py#L17-L47)
- [settlement_repository.py](file://app/modules/treasury/repositories/settlement_repository.py#L11-L47)
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L14-L123)
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L1-L232)
- [settlement_schemas.py](file://app/modules/treasury/schemas/settlement_schemas.py#L9-L57)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L251-L331)
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L22-L187)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L18-L67)
- [bank_transaction_model.py](file://app/modules/treasury/models/bank_transaction_model.py#L21-L51)

**Section sources**
- [settlement_model.py](file://app/modules/treasury/models/settlement_model.py#L1-L48)
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L1-L124)
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L1-L232)
- [settlement_schemas.py](file://app/modules/treasury/schemas/settlement_schemas.py#L1-L58)
- [settlement_repository.py](file://app/modules/treasury/repositories/settlement_repository.py#L1-L48)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L1-L332)
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L1-L188)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L1-L68)
- [bank_transaction_model.py](file://app/modules/treasury/models/bank_transaction_model.py#L1-L52)
- [endpoint_keys.py](file://app/core/endpoint_keys.py#L32-L35)
- [004_fix_settlement_uniqueness.py](file://database/migrations/versions/004_fix_settlement_uniqueness.py#L1-L60)

## Core Components
- Settlement Model: Defines settlement records with amounts, fees, currency, and external identifiers.
- Settlement Service: Validates inputs, ensures referential integrity, and persists settlements.
- Settlement Routes: Expose REST endpoints for creating settlements and importing from gateways.
- Settlement Schemas: Pydantic models for request/response validation.
- Settlement Repository: Data access for settlements with filtering and deduplication by external ID.
- Cash Book Posting Service: Posts settlement journal entries to the CASH book and manages idempotency.
- Reconciliation Service: Manages bank reconciliation sessions and matches, enabling cash clearing verification.

**Section sources**
- [settlement_model.py](file://app/modules/treasury/models/settlement_model.py#L17-L47)
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L14-L123)
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L22-L231)
- [settlement_schemas.py](file://app/modules/treasury/schemas/settlement_schemas.py#L9-L57)
- [settlement_repository.py](file://app/modules/treasury/repositories/settlement_repository.py#L11-L47)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L251-L331)
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L22-L187)

## Architecture Overview
The Settlement System follows a layered architecture:
- API Layer: FastAPI routes handle requests and apply idempotency.
- Service Layer: Business logic validates and orchestrates persistence and posting.
- Persistence Layer: SQLAlchemy models and repositories manage data.
- Integration Layer: General Ledger posting and reconciliation services.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "Settlement Routes"
participant Service as "SettlementService"
participant Repo as "SettlementRepository"
participant GL as "CashBookPostingService"
participant DB as "Database"
Client->>API : POST /settlements
API->>Service : create_settlement(...)
Service->>Repo : create(...)
Repo->>DB : INSERT
DB-->>Repo : Settlement persisted
Repo-->>Service : Settlement
Service-->>API : Settlement
API->>GL : post_settlement(entity_id, settlement, posted_by)
GL->>DB : Create Journal Entry and Lines
DB-->>GL : Entry posted
GL-->>API : Entry ID
API-->>Client : 201 Created SettlementResponse
```

**Diagram sources**
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L22-L90)
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L23-L81)
- [settlement_repository.py](file://app/modules/treasury/repositories/settlement_repository.py#L17-L22)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L251-L331)

## Detailed Component Analysis

### Settlement Model
The Settlement model captures payment gateway payouts and manual cash receipts. It includes:
- Identifiers: legal entity, bank account, settlement date, source (Stripe, TELR, MANUAL).
- Amounts: gross, fees, net, currency.
- External IDs: external_settlement_id and external_payout_id for deduplication and linking.
- Relationships: links to LegalEntity, BankAccount, and BankTransaction.
- Uniqueness: composite constraint on (source, external_settlement_id) where external_settlement_id is not null.

```mermaid
classDiagram
class Settlement {
+UUID id
+UUID legal_entity_id
+UUID bank_account_id
+date settlement_date
+SettlementSource source
+Decimal gross_amount
+Decimal fees
+Decimal net_amount
+string currency
+string external_settlement_id
+string external_payout_id
+UUID bank_transaction_id
+string description
+datetime created_at
+datetime updated_at
}
class SettlementSource {
<<enumeration>>
STRIPE
TELR
MANUAL
}
class LegalEntity
class BankAccount
class BankTransaction
Settlement --> LegalEntity : "belongs to"
Settlement --> BankAccount : "belongs to"
Settlement --> BankTransaction : "links to"
```

**Diagram sources**
- [settlement_model.py](file://app/modules/treasury/models/settlement_model.py#L10-L47)

**Section sources**
- [settlement_model.py](file://app/modules/treasury/models/settlement_model.py#L17-L47)
- [004_fix_settlement_uniqueness.py](file://database/migrations/versions/004_fix_settlement_uniqueness.py#L23-L42)

### Settlement Service
Responsibilities:
- Validation: Ensures legal entity and bank account existence, currency consistency, and amount integrity.
- Deduplication: Prevents duplicate external_settlement_id entries.
- Persistence: Creates settlement records.
- Import: Normalizes manual JSON/CSV imports into standardized settlement records.

```mermaid
flowchart TD
Start([Create Settlement]) --> ValidateEntity["Validate Legal Entity"]
ValidateEntity --> EntityOK{"Entity exists?"}
EntityOK --> |No| RaiseNotFound["Raise NotFoundError"]
EntityOK --> |Yes| ValidateAccount["Validate Bank Account and Currency"]
ValidateAccount --> AccountOK{"Account valid and currency matches?"}
AccountOK --> |No| RaiseValidationError["Raise ValidationError"]
AccountOK --> |Yes| ValidateAmounts["Validate Amounts (non-negative, net=gross-fees)"]
ValidateAmounts --> AmountsOK{"Amounts valid?"}
AmountsOK --> |No| RaiseValidationError
AmountsOK --> |Yes| CheckDuplicate["Check external_settlement_id uniqueness"]
CheckDuplicate --> DuplicateFound{"Duplicate found?"}
DuplicateFound --> |Yes| RaiseDuplicate["Raise DuplicateEntryError"]
DuplicateFound --> |No| Persist["Persist Settlement"]
Persist --> Commit["Commit Session"]
Commit --> Done([Return Settlement])
```

**Diagram sources**
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L23-L81)

**Section sources**
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L14-L123)

### Settlement Routes
Endpoints:
- POST /settlements: Create a settlement (supports idempotency).
- POST /settlements/stripe/import: Import Stripe settlement (manual JSON).
- POST /settlements/telr/import: Import TELR settlement (manual JSON).
- GET /settlements: List settlements with filters.
- GET /settlements/{settlement_id}: Retrieve a settlement.

Idempotency:
- Uses endpoint keys for idempotency: SETTLEMENT_CREATE, SETTLEMENT_STRIPE_IMPORT, SETTLEMENT_TELR_IMPORT.
- Applies idempotency wrapper around handlers to ensure idempotent processing.

**Section sources**
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L22-L231)
- [endpoint_keys.py](file://app/core/endpoint_keys.py#L32-L35)

### Cash Clearing and Journal Posting
The CashBookPostingService posts settlement entries to the CASH book:
- Determines the CASH book and accounting period for the settlement date.
- Retrieves GL account mappings for cash, revenue, and processing fees.
- Creates a draft journal entry with:
  - Debit: Bank Cash (net amount)
  - Credit: Revenue (gross amount)
  - Debit: Processing Fees Expense (fees, if any)
- Posts the entry with idempotency support and generates a source key for reconciliation.

```mermaid
sequenceDiagram
participant API as "Settlement Routes"
participant Service as "SettlementService"
participant GL as "CashBookPostingService"
participant JE as "JournalEntryService"
participant Acc as "AccountingPeriodRepository"
participant Map as "GLAccountMappingRepository"
API->>Service : create_settlement(...)
Service-->>API : Settlement
API->>GL : post_settlement(entity_id, settlement, posted_by)
GL->>Acc : get_by_book_and_date(cash_book.id, settlement_date)
Acc-->>GL : Period
GL->>Map : get_mapping(entity_id, book_id, "CASH_BANK")
Map-->>GL : Cash Account
GL->>Map : get_mapping(entity_id, book_id, "REV_CASH")
Map-->>GL : Revenue Account
GL->>Map : get_mapping(entity_id, book_id, "EXP_PROCESSING_FEES")
Map-->>GL : Fee Account
GL->>JE : create_draft_entry(...)
JE-->>GL : Entry ID
GL->>JE : add_line(Dr Cash, Cr Revenue, Dr Fees)
GL->>JE : post_entry(entry_id, posted_by, source_key)
JE-->>GL : Posted
GL-->>API : Entry ID
```

**Diagram sources**
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L251-L331)

**Section sources**
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L251-L331)

### Reconciliation Workflow
Settlements integrate with bank reconciliation:
- Bank transactions are imported and marked as reconciled upon matching.
- Reconciliation sessions compare statement balances to book totals.
- Matches link bank transactions to journal entries (including settlement postings).
- Sessions can be closed when differences are zero (or allowed to be non-zero).

```mermaid
flowchart TD
CreateSession["Create Reconciliation Session"] --> ImportTx["Import Bank Transactions"]
ImportTx --> MatchTx["Match Transactions to Journal Entries"]
MatchTx --> ReconcileTx["Mark Transactions as Reconciled"]
ReconcileTx --> CalcDiff["Calculate Difference"]
CalcDiff --> CloseSession{"Difference Zero?"}
CloseSession --> |Yes| Close["Close Session"]
CloseSession --> |No| Override["Allow Non-Zero Close"]
Override --> Close
```

**Diagram sources**
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L33-L187)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L18-L67)
- [bank_transaction_model.py](file://app/modules/treasury/models/bank_transaction_model.py#L21-L51)

**Section sources**
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L22-L187)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L18-L67)
- [bank_transaction_model.py](file://app/modules/treasury/models/bank_transaction_model.py#L21-L51)

## Dependency Analysis
- Routes depend on SettlementService and idempotency utilities.
- SettlementService depends on repositories and validation logic.
- CashBookPostingService depends on General Ledger services and mappings.
- ReconciliationService depends on Treasury and General Ledger repositories.

```mermaid
graph LR
SROUTES["Settlement Routes"] --> SS["SettlementService"]
SS --> SR["SettlementRepository"]
SS --> SM["Settlement Model"]
SS --> CBPS["CashBookPostingService"]
CBPS --> JE["JournalEntryService"]
CBPS --> MAP["GLAccountMappingRepository"]
RS["ReconciliationService"] --> RM["Reconciliation Model"]
RS --> BTM["BankTransaction Model"]
```

**Diagram sources**
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L1-L232)
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L1-L124)
- [settlement_repository.py](file://app/modules/treasury/repositories/settlement_repository.py#L1-L48)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L1-L332)
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L1-L188)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L1-L68)
- [bank_transaction_model.py](file://app/modules/treasury/models/bank_transaction_model.py#L1-L52)

**Section sources**
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L1-L232)
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L1-L124)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L1-L332)
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L1-L188)

## Performance Considerations
- Indexes: Settlement model includes indexes on legal_entity_id, bank_account_id, settlement_date, and external_settlement_id to optimize queries.
- Filtering: Repository supports efficient filtering by entity, date range, and source.
- Idempotency: Endpoint keys and idempotency wrappers prevent duplicate processing overhead.
- Journal posting: Batched posting and minimal repository calls reduce transaction overhead.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Not Found Errors: Ensure legal entity and bank account exist and belong to the same legal entity.
- Validation Errors: Verify amounts are non-negative and net equals gross minus fees; currency must match bank account.
- Duplicate Entry Errors: external_settlement_id must be unique per source; for manual entries, external_settlement_id is optional.
- Idempotency Failures: Ensure idempotency_key is provided and consistent for retries.
- Journal Posting Errors: Confirm CASH book exists for the legal entity and the settlement date falls within an open accounting period.

**Section sources**
- [settlement_service.py](file://app/modules/treasury/services/settlement_service.py#L38-L64)
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L84-L89)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L259-L269)

## Conclusion
The Settlement System provides robust settlement creation, validation, and cash posting capabilities. It integrates seamlessly with the General Ledger for journal entries and with bank reconciliation for cash clearing verification. The system’s idempotent endpoints, strong validation, and clear separation of concerns enable reliable settlement processing across payment gateways and manual entries.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### API Route Specifications
- POST /settlements
  - Description: Create a settlement.
  - Body: SettlementCreate schema.
  - Response: SettlementResponse.
  - Idempotency: Enabled via SETTLEMENT_CREATE.
- POST /settlements/stripe/import
  - Description: Import Stripe settlement (manual JSON).
  - Body: SettlementImport schema.
  - Response: SettlementResponse.
  - Idempotency: Enabled via SETTLEMENT_STRIPE_IMPORT.
- POST /settlements/telr/import
  - Description: Import TELR settlement (manual JSON).
  - Body: SettlementImport schema.
  - Response: SettlementResponse.
  - Idempotency: Enabled via SETTLEMENT_TELR_IMPORT.
- GET /settlements
  - Description: List settlements for an entity.
  - Query: entity_id, start_date, end_date, source, limit, offset.
  - Response: Array of SettlementResponse.
- GET /settlements/{settlement_id}
  - Description: Retrieve a settlement by ID.
  - Response: SettlementResponse.

**Section sources**
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L22-L231)
- [settlement_schemas.py](file://app/modules/treasury/schemas/settlement_schemas.py#L9-L57)
- [endpoint_keys.py](file://app/core/endpoint_keys.py#L32-L35)

### Settlement Model Fields
- legal_entity_id: UUID, foreign key to legal entity.
- bank_account_id: UUID, foreign key to bank account.
- settlement_date: Date.
- source: SettlementSource (STRIPE, TELR, MANUAL).
- gross_amount: Numeric(15,2).
- fees: Numeric(15,2).
- net_amount: Numeric(15,2).
- currency: String(3).
- external_settlement_id: String(255), unique per source.
- external_payout_id: String(255).
- bank_transaction_id: UUID, optional link to bank transaction.
- description: String(500).

**Section sources**
- [settlement_model.py](file://app/modules/treasury/models/settlement_model.py#L17-L32)

### Settlement Workflows
- Automated clearing (Stripe/TELR): Import via dedicated endpoints; system posts journal entries to CASH book; reconciliation session can match bank transactions to journal entries.
- Manual intervention: Create settlement manually; if external_settlement_id is omitted, system still posts with internal idempotency key; reconciliation proceeds similarly.

**Section sources**
- [settlement_routes.py](file://app/modules/treasury/api/routes/settlement_routes.py#L92-L195)
- [cash_book_posting_service.py](file://app/modules/general_ledger/services/cash_book_posting_service.py#L316-L328)
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L75-L128)

### Reconciliation Reporting
- Create a reconciliation session for a bank account and period.
- Import bank transactions and match them to journal entries (including settlement entries).
- Calculate difference and close the session when balanced.

**Section sources**
- [reconciliation_service.py](file://app/modules/general_ledger/services/reconciliation_service.py#L33-L187)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L18-L67)