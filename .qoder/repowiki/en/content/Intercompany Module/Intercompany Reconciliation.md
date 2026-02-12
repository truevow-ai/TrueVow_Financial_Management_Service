# Intercompany Reconciliation

<cite>
**Referenced Files in This Document**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py)
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py)
- [reconciliation_routes.py](file://app/modules/intercompany/api/routes/reconciliation_routes.py)
- [intercompany_schemas.py](file://app/modules/intercompany/schemas/intercompany_schemas.py)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py)
- [v1_init.py](file://app/api/v1/__init__.py)
- [main.py](file://app/main.py)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py)
- [reconciliation_matching_service.py](file://app/modules/general_ledger/services/reconciliation_matching_service.py)
- [ADDENDUM_B_RECONCILIATION_MATCHING.md](file://docs/01-main/ADDENDUM_B_RECONCILIATION_MATCHING.md)
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
This document describes the Intercompany Reconciliation system, focusing on balance calculation, elimination procedures, and reconciliation matching. It explains the IntercompanyReconciliationService implementation, intra-entity transaction matching, outstanding balance tracking, and consolidation adjustments. It also documents intercompany balance models, entity pair relationships, balance aging, and reconciliation status tracking. The reconciliation API endpoints for balance queries, reconciliation sessions, and adjustment processing are covered, along with examples of intercompany receivable/payable matching, timing differences resolution, and elimination entries. Finally, reconciliation workflows, exception handling, and audit procedures are addressed.

## Project Structure
The Intercompany Reconciliation system is implemented within the intercompany module and integrates with general ledger and treasury components. The API is exposed under the v1 router and registered in the main application.

```mermaid
graph TB
subgraph "Intercompany Module"
IRoutes["Reconciliation Routes<br/>reconciliation_routes.py"]
IService["IntercompanyReconciliationService<br/>intercompany_reconciliation_service.py"]
ITransferRepo["IntercompanyTransferRepository<br/>intercompany_transfer_repository.py"]
IBalanceRepo["IntercompanyBalanceRepository<br/>intercompany_balance_repository.py"]
ITransferModel["IntercompanyTransfer<br/>intercompany_transfer_model.py"]
IBalanceModel["IntercompanyBalance<br/>intercompany_balance_model.py"]
end
subgraph "General Ledger Module"
GReconModel["ReconciliationSession/Match<br/>reconciliation_model.py"]
GMatchSvc["ReconciliationMatchingService<br/>reconciliation_matching_service.py"]
end
subgraph "API Layer"
V1["API v1 Router<br/>v1_init.py"]
Main["Main App<br/>main.py"]
end
IRoutes --> IService
IService --> ITransferRepo
IService --> IBalanceRepo
ITransferRepo --> ITransferModel
IBalanceRepo --> IBalanceModel
GMatchSvc --> GReconModel
V1 --> IRoutes
Main --> V1
```

**Diagram sources**
- [reconciliation_routes.py](file://app/modules/intercompany/api/routes/reconciliation_routes.py#L1-L109)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L1-L168)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L1-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L1-L55)
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L1-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L1-L39)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L1-L68)
- [reconciliation_matching_service.py](file://app/modules/general_ledger/services/reconciliation_matching_service.py#L1-L270)
- [v1_init.py](file://app/api/v1/__init__.py#L26-L62)
- [main.py](file://app/main.py#L29-L30)

**Section sources**
- [v1_init.py](file://app/api/v1/__init__.py#L26-L62)
- [main.py](file://app/main.py#L29-L30)

## Core Components
- IntercompanyReconciliationService orchestrates reconciliation operations: balance calculation, balance snapshot creation, transfer reconciliation, and reconciliation reporting.
- IntercompanyTransferRepository encapsulates transfer queries and balance computation for entity pairs.
- IntercompanyBalanceRepository manages balance snapshots with uniqueness constraints per entity pair, date, and balance type.
- IntercompanyTransfer and IntercompanyBalance models define the domain entities and their relationships.
- Reconciliation routes expose endpoints for balance snapshots, reconciliation, reporting, and balance queries.

**Section sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L14-L168)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L12-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L14-L55)
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)
- [reconciliation_routes.py](file://app/modules/intercompany/api/routes/reconciliation_routes.py#L15-L109)

## Architecture Overview
The reconciliation workflow connects API routes to the service layer, repositories, and models. Balance snapshots capture the net position between entity pairs as of a given date. Reconciliation marks transfers as settled and updates status for reporting.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Routes as "Reconciliation Routes"
participant Service as "IntercompanyReconciliationService"
participant TRepo as "IntercompanyTransferRepository"
participant BRepo as "IntercompanyBalanceRepository"
Client->>Routes : "GET /intercompany/reconciliation/balance?from_entity_id&to_entity_id&as_of_date"
Routes->>Service : "calculate_balance(...)"
Service->>TRepo : "calculate_balance(...)"
TRepo-->>Service : "Decimal balance"
Service-->>Routes : "Decimal balance"
Routes-->>Client : "JSON {balance}"
Client->>Routes : "POST /intercompany/reconciliation/balance-snapshot"
Routes->>Service : "create_balance_snapshot(...)"
Service->>TRepo : "calculate_balance(...)"
Service->>BRepo : "get_balance(...) or create(...)"
BRepo-->>Service : "IntercompanyBalance"
Service-->>Routes : "IntercompanyBalance"
Routes-->>Client : "JSON {balance snapshot}"
```

**Diagram sources**
- [reconciliation_routes.py](file://app/modules/intercompany/api/routes/reconciliation_routes.py#L88-L109)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L93)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L77-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L20-L36)

## Detailed Component Analysis

### IntercompanyReconciliationService
Responsibilities:
- Balance calculation for an entity pair up to a specific date.
- Creation of balance snapshots with type classification (receivable/payable/net).
- Batch reconciliation of transfers for a specific entity pair.
- Generation of reconciliation reports including counts and transfer details.

Key behaviors:
- Balance type determination based on sign of the computed amount.
- Snapshot existence checks and updates to avoid duplicates.
- Transfer reconciliation updates with atomic commit.

```mermaid
classDiagram
class IntercompanyReconciliationService {
+calculate_balance(from_entity_id, to_entity_id, as_of_date) Decimal
+create_balance_snapshot(from_entity_id, to_entity_id, as_of_date) IntercompanyBalance
+reconcile_transfers(from_entity_id, to_entity_id, transfer_ids, reconciled_at) int
+get_reconciliation_report(from_entity_id, to_entity_id, as_of_date) Dict
}
class IntercompanyTransferRepository {
+calculate_balance(from_entity_id, to_entity_id, as_of_date) Decimal
+list_by_entity_pair(from_entity_id, to_entity_id, ...) IntercompanyTransfer[]
}
class IntercompanyBalanceRepository {
+get_balance(from_entity_id, to_entity_id, as_of_date, balance_type) IntercompanyBalance?
+create(...) IntercompanyBalance
+update(id, balance_amount) void
}
IntercompanyReconciliationService --> IntercompanyTransferRepository : "uses"
IntercompanyReconciliationService --> IntercompanyBalanceRepository : "uses"
```

**Diagram sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L14-L168)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L12-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L14-L55)

**Section sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L168)

### Intercompany Transfer and Balance Models
- IntercompanyTransfer captures intra-entity movements with reconciliation flags and optional treasury/journal links.
- IntercompanyBalance stores snapshots with a unique constraint on entity pair, date, and balance type.

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
uuid from_bank_account_id
uuid to_bank_account_id
uuid from_bank_transaction_id
uuid to_bank_transaction_id
uuid from_entity_je_id
uuid to_entity_je_id
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
LEGAL_ENTITY {
uuid id PK
}
BANK_ACCOUNT {
uuid id PK
}
JOURNAL_ENTRY {
uuid id PK
}
INTERCOMPANY_TRANSFER }o--|| LEGAL_ENTITY : "from_entity"
INTERCOMPANY_TRANSFER }o--|| LEGAL_ENTITY : "to_entity"
INTERCOMPANY_TRANSFER }o--|| BANK_ACCOUNT : "from_bank_account"
INTERCOMPANY_TRANSFER }o--|| BANK_ACCOUNT : "to_bank_account"
INTERCOMPANY_TRANSFER }o--|| JOURNAL_ENTRY : "from_entity_je"
INTERCOMPANY_TRANSFER }o--|| JOURNAL_ENTRY : "to_entity_je"
INTERCOMPANY_BALANCE }o--|| LEGAL_ENTITY : "from_entity"
INTERCOMPANY_BALANCE }o--|| LEGAL_ENTITY : "to_entity"
```

**Diagram sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)

**Section sources**
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L16-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)

### Balance Calculation Algorithm
The balance is computed as the sum of intercompany transfers between a pair of entities up to a specified date. The algorithm:
- Filters transfers by entity pair and optional date cutoff.
- Aggregates amounts to produce a net balance.
- Determines balance type (receivable/payable/net) for snapshot creation.

```mermaid
flowchart TD
Start(["Start"]) --> Fetch["Fetch transfers for entity pair<br/>up to as_of_date"]
Fetch --> Sum["Sum transfer amounts"]
Sum --> Type{"Balance > 0 ?"}
Type --> |Yes| SetRec["Set balance type = RECEIVABLE"]
Type --> |No| Type2{"Balance < 0 ?"}
Type2 --> |Yes| SetPay["Set balance type = PAYABLE"]
Type2 --> |No| SetNet["Set balance type = NET"]
SetRec --> Abs["Use absolute value for snapshot amount"]
SetPay --> Abs
SetNet --> Abs
Abs --> End(["End"])
```

**Diagram sources**
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L77-L101)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L93)

**Section sources**
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L77-L101)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L93)

### Reconciliation Matching and Elimination Procedures
- Intra-entity transaction matching is supported by the general ledger reconciliation matching service, which computes confidence scores based on amount, date proximity, description similarity, and reference matching.
- Elimination entries are generated during intercompany transfer posting, creating intercompany receivable/payable entries per entity and linking to journal entries.

```mermaid
sequenceDiagram
participant Client as "Client"
participant GLMatch as "ReconciliationMatchingService"
participant GLModel as "ReconciliationSession/Match"
participant Repo as "ReconciliationMatchRepository"
Client->>GLMatch : "suggest_matches(bank_transaction_id, session_id)"
GLMatch->>GLModel : "Load session and account"
GLMatch->>GLModel : "Query candidate JE entries"
GLMatch->>GLMatch : "Score matches (amount, date, text, ref)"
GLMatch-->>Client : "Top suggestions with confidence"
Note over Client,GLModel : "Manual or auto-confirm matches stored via GL reconciliation endpoints"
```

**Diagram sources**
- [reconciliation_matching_service.py](file://app/modules/general_ledger/services/reconciliation_matching_service.py#L54-L150)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L18-L68)

**Section sources**
- [reconciliation_matching_service.py](file://app/modules/general_ledger/services/reconciliation_matching_service.py#L54-L270)
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L114-L182)

### Reconciliation API Endpoints
Endpoints:
- POST /api/v1/intercompany/reconciliation/balance-snapshot: Create a balance snapshot for an entity pair as of a date.
- POST /api/v1/intercompany/reconciliation/reconcile: Mark selected transfers as reconciled for an entity pair.
- GET /api/v1/intercompany/reconciliation/report: Retrieve reconciliation report for an entity pair as of a date.
- GET /api/v1/intercompany/reconciliation/balance: Retrieve the net balance for an entity pair (today if not specified).

```mermaid
sequenceDiagram
participant Client as "Client"
participant Routes as "Reconciliation Routes"
participant Service as "IntercompanyReconciliationService"
Client->>Routes : "POST /intercompany/reconciliation/reconcile"
Routes->>Service : "reconcile_transfers(...)"
Service-->>Routes : "count"
Routes-->>Client : "{reconciled_count, status}"
Client->>Routes : "GET /intercompany/reconciliation/report"
Routes->>Service : "get_reconciliation_report(...)"
Service-->>Routes : "report"
Routes-->>Client : "JSON report"
```

**Diagram sources**
- [reconciliation_routes.py](file://app/modules/intercompany/api/routes/reconciliation_routes.py#L43-L86)

**Section sources**
- [reconciliation_routes.py](file://app/modules/intercompany/api/routes/reconciliation_routes.py#L15-L109)
- [v1_init.py](file://app/api/v1/__init__.py#L26-L62)
- [main.py](file://app/main.py#L29-L30)

### Intercompany Receivable/Payable Matching Examples
- Example scenario: Entity A transfers cash to Entity B. The system posts intercompany entries eliminating the balances across entities and links them to journal entries. Reconciliation can mark the underlying transfers as reconciled.
- Timing differences: If a transfer is recorded after the reporting date, it will not appear in the balance until the cutoff date. Snapshots can be created for historical dates to reflect prior positions.

**Section sources**
- [intercompany_transfer_service.py](file://app/modules/intercompany/services/intercompany_transfer_service.py#L114-L182)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L22-L93)

### Consolidation Adjustments
- Balance snapshots capture the net intercompany exposure as of a date, enabling consolidation adjustments by eliminating intra-entity balances.
- Reconciliation reports support variance analysis and adjustments by highlighting unreconciled items.

**Section sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L123-L168)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L17-L39)

## Dependency Analysis
The reconciliation service depends on repositories for transfer and balance operations. The API routes depend on the service and expose standardized endpoints. The general ledger reconciliation components provide complementary matching capabilities.

```mermaid
graph TB
Routes["reconciliation_routes.py"] --> Service["intercompany_reconciliation_service.py"]
Service --> TRepo["intercompany_transfer_repository.py"]
Service --> BRepo["intercompany_balance_repository.py"]
TRepo --> TModel["intercompany_transfer_model.py"]
BRepo --> BModel["intercompany_balance_model.py"]
GMatch["reconciliation_matching_service.py"] --> GModel["reconciliation_model.py"]
V1["v1/__init__.py"] --> Routes
Main["main.py"] --> V1
```

**Diagram sources**
- [reconciliation_routes.py](file://app/modules/intercompany/api/routes/reconciliation_routes.py#L1-L109)
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L1-L168)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L1-L101)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L1-L55)
- [intercompany_transfer_model.py](file://app/modules/intercompany/models/intercompany_transfer_model.py#L1-L59)
- [intercompany_balance_model.py](file://app/modules/intercompany/models/intercompany_balance_model.py#L1-L39)
- [reconciliation_matching_service.py](file://app/modules/general_ledger/services/reconciliation_matching_service.py#L1-L270)
- [reconciliation_model.py](file://app/modules/general_ledger/models/reconciliation_model.py#L1-L68)
- [v1_init.py](file://app/api/v1/__init__.py#L26-L62)
- [main.py](file://app/main.py#L29-L30)

**Section sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L17-L21)
- [intercompany_transfer_repository.py](file://app/modules/intercompany/repositories/intercompany_transfer_repository.py#L12-L16)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L14-L18)

## Performance Considerations
- Balance calculations and listings use indexed filters on entity IDs and dates to minimize scan costs.
- Snapshot creation avoids duplicates via unique constraints and updates existing records when appropriate.
- Recommendations:
  - Add pagination and limits for listing endpoints.
  - Indexes on reconciliation flags and dates improve reconciliation queries.
  - Batch reconciliation operations should be executed within transactions to maintain consistency.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Validation errors: Ensure entity IDs, dates, and amounts meet schema constraints.
- Not found errors: Verify entity pair existence and transfer IDs.
- Duplicate snapshots: The service checks for existing snapshots and updates them; confirm unique constraints are respected.
- Reconciliation mismatches: Confirm entity pair alignment and reconciliation flags before marking as reconciled.

**Section sources**
- [intercompany_reconciliation_service.py](file://app/modules/intercompany/services/intercompany_reconciliation_service.py#L104-L121)
- [intercompany_balance_repository.py](file://app/modules/intercompany/repositories/intercompany_balance_repository.py#L20-L36)
- [intercompany_schemas.py](file://app/modules/intercompany/schemas/intercompany_schemas.py#L9-L21)

## Conclusion
The Intercompany Reconciliation system provides robust mechanisms for calculating balances, capturing snapshots, reconciling transfers, and generating reports. Its integration with general ledger reconciliation services enables intelligent matching and supports elimination procedures during consolidation. The modular design ensures maintainability and extensibility for future enhancements such as automated matching and advanced audit trails.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Reconciliation Workflow Overview
```mermaid
flowchart TD
A["Create Balance Snapshot"] --> B["Review Report"]
B --> C{"Unreconciled Items?"}
C --> |Yes| D["Mark Transfers Reconciled"]
C --> |No| E["Close/Archive"]
D --> F["Update Status & Commit"]
F --> B
```

[No sources needed since this diagram shows conceptual workflow, not actual code structure]

### Matching Algorithm Guidance
- The general ledger reconciliation matching service demonstrates scoring and confidence thresholds suitable for intercompany transfer matching.
- Intercompany-specific matching can leverage amount equality, date tolerance, and reference matching aligned with intercompany transfer attributes.

**Section sources**
- [reconciliation_matching_service.py](file://app/modules/general_ledger/services/reconciliation_matching_service.py#L54-L150)
- [ADDENDUM_B_RECONCILIATION_MATCHING.md](file://docs/01-main/ADDENDUM_B_RECONCILIATION_MATCHING.md#L10-L30)