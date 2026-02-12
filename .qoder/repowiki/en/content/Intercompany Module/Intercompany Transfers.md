# Intercompany Transfers

<cite>
**Referenced Files in This Document**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py)
- [intercompany_schemas.py](file://app/modules/intercompany/schemas/intercompany_schemas.py)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py)
- [endpoint_keys.py](file://app/core/endpoint_keys.py)
- [v1 router](file://app/api/v1/__init__.py)
- [main.py](file://app/main.py)
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
This document describes the Intercompany Transfers functionality in the TrueVow Financial Management system. It covers the end-to-end lifecycle of intercompany transfers: creation, posting, and balance tracking. It explains the IntercompanyTransferService implementation, including transfer creation, posting logic, and dual-entity journal entry generation. It documents the intercompany transfer models, their relationships, transfer types, and posting states. It also lists the API endpoints for creating transfers, posting transfers, listing transfers, retrieving individual transfers, and computing balances. Finally, it provides examples of intercompany fund transfers, loan arrangements, and intercompany receivable/payable management, along with validation rules, currency handling, and audit trail requirements.

## Project Structure
The Intercompany Transfers feature is implemented as part of the intercompany module. The module integrates with general ledger and treasury models and exposes REST endpoints via FastAPI.

```mermaid
graph TB
subgraph "Intercompany Module"
ITM["IntercompanyTransfer<br/>Model"]
IBM["IntercompanyBalance<br/>Model"]
ITS["IntercompanyTransferService"]
IRS["IntercompanyReconciliationService"]
ITR["IntercompanyTransferRoutes"]
ISR["IntercompanyTransferRepository"]
end
subgraph "General Ledger"
JEM["JournalEntry<br/>Model"]
end
subgraph "API Layer"
V1["API v1 Router"]
MAIN["Main App"]
end
ITM --> ISR
ITS --> ISR
ITS --> IRS
ITS --> JEM
ITR --> ITS
V1 --> ITR
MAIN --> V1
```

**Diagram sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L58)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L38)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L17-L27)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L14-L21)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L18-L179)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L12-L16)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)
- [v1 router](file://app/api/v1/__init__.py#L59-L62)
- [main.py](file://app/main.py#L29-L30)

**Section sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L1-L58)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L17-L27)
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L18-L179)
- [v1 router](file://app/api/v1/__init__.py#L59-L62)
- [main.py](file://app/main.py#L29-L30)

## Core Components
- IntercompanyTransfer model: Represents a single intercompany transfer with entity linkage, amount, currency, type, treasury links, and journal entry linkage.
- IntercompanyBalance model: Stores balance snapshots with type (NET, RECEIVABLE, PAYABLE), amount, and currency.
- IntercompanyTransferService: Orchestrates transfer creation and posting, coordinates with books, periods, GL mappings, and journal entry service.
- IntercompanyReconciliationService: Computes balances, creates balance snapshots, reconciles transfers, and generates reconciliation reports.
- IntercompanyTransferRepository: Provides persistence operations for transfers, including filtering, pagination, and balance calculations.
- API routes: Expose endpoints for creating, posting, listing, retrieving, and querying balances for intercompany transfers.
- JournalEntry model: Underpins dual-entity journal entries generated during posting.

**Section sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L58)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L38)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L17-L27)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L14-L21)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L12-L16)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)

## Architecture Overview
Intercompany transfers are created as draft records and later posted to both entities’ books. Posting generates two journal entries (one per entity) linked back to the transfer record. Balances are tracked and can be queried or snapshotted.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Routes as "IntercompanyTransferRoutes"
participant Service as "IntercompanyTransferService"
participant Repo as "IntercompanyTransferRepository"
participant GL as "JournalEntryService"
participant JE as "JournalEntry"
Client->>Routes : POST /intercompany/transfers
Routes->>Service : create_transfer(...)
Service->>Repo : create(...)
Repo-->>Service : IntercompanyTransfer
Service-->>Routes : IntercompanyTransfer
Routes-->>Client : 201 Created
Client->>Routes : POST /intercompany/transfers/{id}/post
Routes->>Service : post_transfer(id, posted_by)
Service->>GL : create_draft_entry(from_book)
GL-->>Service : JournalEntry (from)
Service->>GL : add_line(..., INTERCO_PAYABLE, debit)
Service->>GL : add_line(..., CASH_BANK, credit) [optional]
Service->>GL : post_entry(from_je, source_key=...)
Service->>GL : create_draft_entry(to_book)
GL-->>Service : JournalEntry (to)
Service->>GL : add_line(..., CASH_BANK, debit) [optional]
Service->>GL : add_line(..., INTERCO_RECEIVABLE, credit)
Service->>GL : post_entry(to_je, source_key=...)
Service->>Repo : update(from_entity_je_id, to_entity_je_id)
Service-->>Routes : (from_je_id, to_je_id)
Routes-->>Client : 200 OK {status, je ids}
```

**Diagram sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L21-L103)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L28-L219)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)

## Detailed Component Analysis

### IntercompanyTransfer Model
- Purpose: Stores intercompany transfer records with entity linkage, amount, currency, type, treasury links, and journal entry linkage.
- Key fields:
  - from_entity_id, to_entity_id: Legal entity identifiers.
  - transfer_date, amount, currency, transfer_type, description, reference_number.
  - Treasury links: from_bank_account_id, to_bank_account_id, from_bank_transaction_id, to_bank_transaction_id.
  - Journal entry linkage: from_entity_je_id, to_entity_je_id.
  - Reconciliation: is_reconciled, reconciled_at.
- Relationships: Links to LegalEntity, BankAccount, BankTransaction, and JournalEntry.

```mermaid
classDiagram
class IntercompanyTransfer {
+UUID id
+UUID from_entity_id
+UUID to_entity_id
+date transfer_date
+Decimal amount
+string currency
+string transfer_type
+string description
+string reference_number
+UUID from_bank_account_id
+UUID to_bank_account_id
+UUID from_bank_transaction_id
+UUID to_bank_transaction_id
+UUID from_entity_je_id
+UUID to_entity_je_id
+boolean is_reconciled
+date reconciled_at
}
class LegalEntity
class BankAccount
class BankTransaction
class JournalEntry
IntercompanyTransfer --> LegalEntity : "from_entity"
IntercompanyTransfer --> LegalEntity : "to_entity"
IntercompanyTransfer --> BankAccount : "from_account"
IntercompanyTransfer --> BankAccount : "to_account"
IntercompanyTransfer --> BankTransaction : "from_transaction"
IntercompanyTransfer --> BankTransaction : "to_transaction"
IntercompanyTransfer --> JournalEntry : "from_je"
IntercompanyTransfer --> JournalEntry : "to_je"
```

**Diagram sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L58)

**Section sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L58)

### IntercompanyBalance Model
- Purpose: Stores balance snapshots for intercompany pairs.
- Key fields:
  - from_entity_id, to_entity_id, as_of_date, balance_type (NET, RECEIVABLE, PAYABLE), balance_amount, currency.
- Constraints: Unique constraint on (from_entity_id, to_entity_id, as_of_date, balance_type).

**Section sources**
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L38)

### IntercompanyTransferService
- Responsibilities:
  - Create transfers with validation (entities exist, distinct, amount positive, currency three-letter).
  - Post transfers to both entities’ ACCRUAL books, generating dual journal entries.
  - Resolve GL account mappings for INTERCO_PAYABLE, INTERCO_RECEIVABLE, and CASH_BANK.
  - Manage periods and books per entity.
  - Update transfer with journal entry IDs upon successful posting.
- Posting logic:
  - From entity: Debit Intercompany Payable, Credit Cash/Bank (if applicable).
  - To entity: Debit Cash/Bank (if applicable), Credit Intercompany Receivable.
  - Journal entries are posted with deterministic source keys scoped to the from entity’s ACCRUAL book.

```mermaid
flowchart TD
Start([Start post_transfer]) --> LoadTransfer["Load transfer by ID"]
LoadTransfer --> ValidateBooks["Get ACCRUAL books for both entities"]
ValidateBooks --> ValidatePeriods["Find accounting periods for transfer_date"]
ValidatePeriods --> MapAccounts["Resolve GL mappings:<br/>INTERCO_PAYABLE (from)<br/>INTERCO_RECEIVABLE (to)<br/>CASH_BANK (optional)"]
MapAccounts --> CreateFromJE["Create draft JE (from entity)"]
CreateFromJE --> AddFromLines["Add lines:<br/>Dr INTERCO_PAYABLE<br/>Cr CASH_BANK (optional)"]
AddFromLines --> PostFrom["Post JE (from entity)"]
PostFrom --> CreateToJE["Create draft JE (to entity)"]
CreateToJE --> AddToLines["Add lines:<br/>Dr CASH_BANK (optional)<br/>Cr INTERCO_RECEIVABLE"]
AddToLines --> PostTo["Post JE (to entity)"]
PostTo --> UpdateTransfer["Update transfer with JE IDs"]
UpdateTransfer --> End([End])
```

**Diagram sources**
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L72-L219)

**Section sources**
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L28-L232)

### IntercompanyReconciliationService
- Responsibilities:
  - Calculate net balance between two entities up to a date.
  - Create balance snapshots with appropriate balance type (RECEIVABLE/PAYABLE/NET).
  - Reconcile transfers by marking them as reconciled.
  - Generate reconciliation reports with counts and transfer details.

**Section sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L168)

### IntercompanyTransferRepository
- Responsibilities:
  - List transfers between an entity pair with optional filters (date range, reconciliation status).
  - List transfers for an entity (from, to, or both directions).
  - Calculate net balance for an entity pair up to a date.

**Section sources**
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L18-L101)

### API Endpoints
- Create transfer
  - Method: POST
  - Path: /intercompany/transfers
  - Request body: IntercompanyTransferCreate
  - Response: IntercompanyTransferResponse
  - Validation: Amount > 0, Currency three-letter, Entities exist and differ.
- Post transfer
  - Method: POST
  - Path: /intercompany/transfers/{transfer_id}/post
  - Request body: IntercompanyTransferPostRequest
  - Response: JSON with transfer_id, from_entity_je_id, to_entity_je_id, status
  - Idempotency: Endpoint key IC_TRANSFER_POST scoped to the from entity’s ACCRUAL book.
- List transfers
  - Method: GET
  - Path: /intercompany/transfers
  - Query params: from_entity_id, to_entity_id, entity_id, start_date, end_date, limit, offset
  - Response: Array of IntercompanyTransferResponse
- Get transfer by ID
  - Method: GET
  - Path: /intercompany/transfers/{transfer_id}
  - Response: IntercompanyTransferResponse
- Get intercompany balance
  - Method: GET
  - Path: /intercompany/transfers/balance
  - Query params: from_entity_id, to_entity_id, as_of_date
  - Response: JSON with from_entity_id, to_entity_id, as_of_date, balance

**Section sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L21-L179)
- [intercompany_schemas.py](file://app/modules/intercompany/schemas/intercompany_schemas.py#L9-L46)
- [endpoint_keys.py](file://app/core/endpoint_keys.py#L17-L19)
- [v1 router](file://app/api/v1/__init__.py#L59-L62)
- [main.py](file://app/main.py#L29-L30)

### Data Models and Relationships
```mermaid
erDiagram
LEGAL_ENTITY {
uuid id PK
string code UK
string name
}
TREASURY_BANK_ACCOUNT {
uuid id PK
uuid legal_entity_id FK
string account_number
}
TREASURY_BANK_TRANSACTION {
uuid id PK
uuid bank_account_id FK
date transaction_date
}
JOURNAL_ENTRY {
uuid id PK
uuid legal_entity_id FK
uuid book_id FK
uuid period_id FK
string entry_number UK
date entry_date
string source_service
string source_type
uuid source_id
string idempotency_key
string source_key
uuid posted_by
date posted_at
}
INTERCOMPANY_TRANSFER {
uuid id PK
uuid from_entity_id FK
uuid to_entity_id FK
date transfer_date
numeric amount
string currency
string transfer_type
uuid from_bank_account_id FK
uuid to_bank_account_id FK
uuid from_bank_transaction_id FK
uuid to_bank_transaction_id FK
uuid from_entity_je_id FK
uuid to_entity_je_id FK
boolean is_reconciled
date reconciled_at
}
INTERCOMPANY_BALANCE {
uuid id PK
uuid from_entity_id FK
uuid to_entity_id FK
date as_of_date
enum balance_type
numeric balance_amount
string currency
}
LEGAL_ENTITY ||--o{ INTERCOMPANY_TRANSFER : "from_entity"
LEGAL_ENTITY ||--o{ INTERCOMPANY_TRANSFER : "to_entity"
TREASURY_BANK_ACCOUNT ||--o{ INTERCOMPANY_TRANSFER : "from_bank_account"
TREASURY_BANK_ACCOUNT ||--o{ INTERCOMPANY_TRANSFER : "to_bank_account"
TREASURY_BANK_TRANSACTION ||--o{ INTERCOMPANY_TRANSFER : "from_bank_transaction"
TREASURY_BANK_TRANSACTION ||--o{ INTERCOMPANY_TRANSFER : "to_bank_transaction"
JOURNAL_ENTRY ||--o{ INTERCOMPANY_TRANSFER : "from_entity_je"
JOURNAL_ENTRY ||--o{ INTERCOMPANY_TRANSFER : "to_entity_je"
LEGAL_ENTITY ||--o{ INTERCOMPANY_BALANCE : "from_entity"
LEGAL_ENTITY ||--o{ INTERCOMPANY_BALANCE : "to_entity"
```

**Diagram sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L58)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L38)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)

## Dependency Analysis
- Routing and inclusion:
  - Intercompany transfer routes are included in the API v1 router and exposed under /api/v1.
- Service dependencies:
  - IntercompanyTransferService depends on repositories for transfers, legal entities, and books, and on JournalEntryService for posting.
- Posting idempotency:
  - The post endpoint uses a dedicated endpoint key and scopes idempotency to the from entity’s ACCRUAL book.

```mermaid
graph LR
Routes["IntercompanyTransferRoutes"] --> Service["IntercompanyTransferService"]
Service --> Repo["IntercompanyTransferRepository"]
Service --> GLSvc["JournalEntryService"]
GLSvc --> JEM["JournalEntry Model"]
Routes --> V1["API v1 Router"]
V1 --> Main["Main App"]
```

**Diagram sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L18-L179)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L17-L27)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)
- [v1 router](file://app/api/v1/__init__.py#L59-L62)
- [main.py](file://app/main.py#L29-L30)

**Section sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L18-L179)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L17-L27)
- [v1 router](file://app/api/v1/__init__.py#L59-L62)
- [main.py](file://app/main.py#L29-L30)

## Performance Considerations
- Indexing: Transfer queries leverage indexed fields (entity IDs, transfer date, reconciliation flag) to optimize filtering and sorting.
- Pagination: Listing endpoints support limit and offset to control payload sizes.
- Single-pass balance calculation: The repository computes net balances in-memory over filtered results.
- Idempotency: Posting uses deterministic source keys and idempotency scoping to avoid duplicate postings.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Transfer not found
  - Symptoms: 404 responses when retrieving or posting transfers.
  - Causes: Invalid transfer ID or missing records.
  - Resolution: Verify transfer ID and existence in the repository.
- Entity not found
  - Symptoms: Validation errors during creation.
  - Causes: from_entity_id or to_entity_id do not correspond to existing legal entities.
  - Resolution: Confirm entity IDs and existence in the legal entity repository.
- Same entity transfer
  - Symptoms: Validation error indicating entities must be different.
  - Resolution: Use distinct from_entity_id and to_entity_id.
- Missing ACCRUAL book
  - Symptoms: Errors when posting transfers.
  - Causes: No ACCRUAL book configured for one or both entities.
  - Resolution: Ensure ACCRUAL books exist for both entities.
- No accounting period
  - Symptoms: Errors when posting due to missing period.
  - Resolution: Confirm accounting periods exist for the transfer date in both entities’ books.
- Account mapping not found
  - Symptoms: Errors resolving INTERCO_PAYABLE, INTERCO_RECEIVABLE, or CASH_BANK.
  - Resolution: Set up GL account mappings for the entities and books.
- Duplicate posting
  - Symptoms: Idempotency errors.
  - Resolution: Retry with the same idempotency key; the system will return the previous result.

**Section sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L42-L103)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L42-L98)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L33)

## Conclusion
The Intercompany Transfers feature provides a robust mechanism for recording, posting, and tracking intercompany movements across entities. It enforces validation, supports dual-entity journal entries, and offers reconciliation capabilities with balance snapshots. The API exposes straightforward endpoints for creation, posting, listing, retrieval, and balance computation, integrating seamlessly with the broader financial management system.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### API Definitions
- Create transfer
  - Method: POST
  - Path: /api/v1/intercompany/transfers
  - Request body: IntercompanyTransferCreate
  - Response: IntercompanyTransferResponse
- Post transfer
  - Method: POST
  - Path: /api/v1/intercompany/transfers/{transfer_id}/post
  - Request body: IntercompanyTransferPostRequest
  - Response: JSON with transfer_id, from_entity_je_id, to_entity_je_id, status
  - Idempotency: Endpoint key IC_TRANSFER_POST scoped to the from entity’s ACCRUAL book
- List transfers
  - Method: GET
  - Path: /api/v1/intercompany/transfers
  - Query params: from_entity_id, to_entity_id, entity_id, start_date, end_date, limit, offset
  - Response: Array of IntercompanyTransferResponse
- Get transfer by ID
  - Method: GET
  - Path: /api/v1/intercompany/transfers/{transfer_id}
  - Response: IntercompanyTransferResponse
- Get intercompany balance
  - Method: GET
  - Path: /api/v1/intercompany/transfers/balance
  - Query params: from_entity_id, to_entity_id, as_of_date
  - Response: JSON with from_entity_id, to_entity_id, as_of_date, balance

**Section sources**
- [intercompany_transfer_routes.py](file://app/modules/intercompany/api/routes/intercompany_transfer_routes.py#L21-L179)
- [endpoint_keys.py](file://app/core/endpoint_keys.py#L17-L19)
- [v1 router](file://app/api/v1/__init__.py#L59-L62)
- [main.py](file://app/main.py#L29-L30)

### Examples
- Intercompany fund transfer
  - Create a transfer with transfer_type set to a cash-related value, optionally linking from_bank_account_id and to_bank_account_id.
  - Post the transfer to generate dual journal entries in both entities’ ACCRUAL books.
- Loan arrangement
  - Use transfer_type to represent loans; maintain intercompany receivable/payable accounts via mappings.
  - Track outstanding balances and reconcile as payments occur.
- Intercompany receivable/payable management
  - Use the balance endpoint to compute net positions between entities.
  - Create balance snapshots for reporting and reconciliation.

[No sources needed since this section provides general guidance]

### Validation Rules and Currency Handling
- Validation rules:
  - Entities must exist and be different.
  - Amount must be greater than zero.
  - Currency must be a three-letter ISO code.
  - Transfer date must resolve to valid accounting periods in both entities’ books.
- Currency handling:
  - Amount and functional currency amounts are stored with two decimal places.
  - Journal lines capture transaction currency and functional currency amounts.

**Section sources**
- [intercompany_schemas.py](file://app/modules/intercompany/schemas/intercompany_schemas.py#L9-L21)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L42-L53)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L68-L107)

### Audit Trail Requirements
- Journal entries capture source tracking (service, type, ID), idempotency keys, and source keys for deterministic posting.
- Posted entries include posted_by and posted_at metadata.
- Intercompany transfers link to journal entries for traceability.

**Section sources**
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L31-L44)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L125-L166)