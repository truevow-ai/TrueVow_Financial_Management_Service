# Data Flow Patterns

<cite>
**Referenced Files in This Document**
- [app/main.py](file://app/main.py)
- [app/api/v1/__init__.py](file://app/api/v1/__init__.py)
- [app/core/middleware.py](file://app/core/middleware.py)
- [app/core/config.py](file://app/core/config.py)
- [app/core/database.py](file://app/core/database.py)
- [app/shared/models/base_model.py](file://app/shared/models/base_model.py)
- [app/shared/repositories/base_repository.py](file://app/shared/repositories/base_repository.py)
- [app/modules/general_ledger/models/journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py)
- [app/modules/general_ledger/repositories/journal_entry_repository.py](file://app/modules/general_ledger/repositories/journal_entry_repository.py)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py)
- [app/modules/general_ledger/api/routes/journal_entry_routes.py](file://app/modules/general_ledger/api/routes/journal_entry_routes.py)
- [app/modules/general_ledger/schemas/journal_entry_schemas.py](file://app/modules/general_ledger/schemas/journal_entry_schemas.py)
- [app/modules/core/models/idempotency_model.py](file://app/modules/core/models/idempotency_model.py)
- [app/core/idempotency.py](file://app/core/idempotency.py)
- [app/core/row_version.py](file://app/core/row_version.py)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py)
- [app/core/exceptions.py](file://app/core/exceptions.py)
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

## Introduction
This document explains the system’s data flow patterns and persistence architecture. It covers:
- Repository pattern implementation and ORM integration with SQLAlchemy (async)
- Database connection management and session lifecycle
- Request-response flow from frontend to backend, including API routing, service layer operations, and database interactions
- Idempotency patterns for safe API reprocessing
- Optimistic locking and row version conflict handling
- Concurrent access handling via idempotency locks and database constraints
- Data validation flows and error propagation
- Audit trail generation
- Caching strategies, batch processing patterns, and data synchronization mechanisms

## Project Structure
The application follows a modular, feature-based structure under app/modules with shared infrastructure in app/shared and app/core. API routes are grouped by domain (e.g., general ledger, treasury, payroll) and exposed under a single v1 router.

```mermaid
graph TB
FE["Frontend (Next.js)"] --> API["FastAPI App"]
API --> MW["Middleware<br/>CorrelationID"]
API --> V1["Router v1"]
V1 --> GLR["GL Routes"]
V1 --> TREAS["Treasury Routes"]
V1 --> AR["AR Routes"]
V1 --> PAY["Payroll Routes"]
V1 --> IC["Intercompany Routes"]
V1 --> REP["Reporting Routes"]
V1 --> APR["AP Routes"]
GLR --> SVC_GL["GL Service Layer"]
TREAS --> SVC_TREAS["Treasury Service Layer"]
AR --> SVC_AR["AR Service Layer"]
PAY --> SVC_PAY["Payroll Service Layer"]
IC --> SVC_IC["Intercompany Service Layer"]
REP --> SVC_REP["Reporting Service Layer"]
APR --> SVC_AP["AP Service Layer"]
SVC_GL --> REPO_GL["GL Repositories"]
SVC_TREAS --> REPO_TREAS["Treasury Repositories"]
SVC_AR --> REPO_AR["AR Repositories"]
SVC_PAY --> REPO_PAY["Payroll Repositories"]
SVC_IC --> REPO_IC["Intercompany Repositories"]
SVC_REP --> REPO_REP["Reporting Repositories"]
SVC_AP --> REPO_AP["AP Repositories"]
REPO_GL --> DB["SQLAlchemy Async Engine"]
REPO_TREAS --> DB
REPO_AR --> DB
REPO_PAY --> DB
REPO_IC --> DB
REPO_REP --> DB
REPO_AP --> DB
```

**Diagram sources**
- [app/api/v1/__init__.py](file://app/api/v1/__init__.py#L1-L72)
- [app/modules/general_ledger/api/routes/journal_entry_routes.py](file://app/modules/general_ledger/api/routes/journal_entry_routes.py#L1-L377)

**Section sources**
- [app/api/v1/__init__.py](file://app/api/v1/__init__.py#L1-L72)

## Core Components
- Application entrypoint initializes FastAPI, middleware, and registers routers.
- Middleware injects correlation IDs for observability.
- Configuration centralizes environment-driven settings including database URLs and pool sizing.
- Database module creates an async SQLAlchemy engine and session factory, importing all models for metadata.
- Shared base model and repository provide common fields and CRUD operations.
- Domain modules encapsulate models, repositories, services, schemas, and routes.

**Section sources**
- [app/main.py](file://app/main.py#L1-L54)
- [app/core/middleware.py](file://app/core/middleware.py#L1-L35)
- [app/core/config.py](file://app/core/config.py#L1-L74)
- [app/core/database.py](file://app/core/database.py#L1-L113)
- [app/shared/models/base_model.py](file://app/shared/models/base_model.py#L1-L18)
- [app/shared/repositories/base_repository.py](file://app/shared/repositories/base_repository.py#L1-L54)

## Architecture Overview
The system uses an async-first architecture with SQLAlchemy for ORM and PostgreSQL as the datastore. Requests traverse middleware, API routes, service layer, repositories, and the database. Idempotency ensures safe retries for write operations, while optimistic locking and row version checks protect against concurrent modifications.

```mermaid
graph TB
subgraph "Transport & Routing"
A["FastAPI App"]
B["CorrelationID Middleware"]
C["v1 Router"]
end
subgraph "Domain Layer"
D["Routes (e.g., JournalEntry)"]
E["Service (e.g., JournalEntryService)"]
F["Repositories (e.g., JournalEntryRepository)"]
G["Models (e.g., JournalEntry)"]
end
subgraph "Persistence"
H["SQLAlchemy Async Engine"]
I["Async Session Factory"]
J["PostgreSQL"]
end
subgraph "Infrastructure"
K["Idempotency (apply_idempotency)"]
L["Row Version (check_row_version)"]
M["Audit Log"]
end
A --> B --> C --> D --> E --> F --> G --> H --> I --> J
D --> K
E --> L
E --> M
```

**Diagram sources**
- [app/main.py](file://app/main.py#L1-L54)
- [app/core/middleware.py](file://app/core/middleware.py#L1-L35)
- [app/api/v1/__init__.py](file://app/api/v1/__init__.py#L1-L72)
- [app/modules/general_ledger/api/routes/journal_entry_routes.py](file://app/modules/general_ledger/api/routes/journal_entry_routes.py#L1-L377)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L1-L635)
- [app/modules/general_ledger/repositories/journal_entry_repository.py](file://app/modules/general_ledger/repositories/journal_entry_repository.py#L1-L119)
- [app/modules/general_ledger/models/journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L1-L128)
- [app/core/database.py](file://app/core/database.py#L1-L113)
- [app/core/idempotency.py](file://app/core/idempotency.py#L1-L482)
- [app/core/row_version.py](file://app/core/row_version.py#L1-L31)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)

## Detailed Component Analysis

### Database Connection Management and ORM Integration
- Async engine and session factory are configured with pool sizes and echo based on settings.
- All domain models are imported at startup to populate metadata for Alembic and runtime reflection.
- Sessions are dependency-injected into routes and closed automatically via a context manager.

```mermaid
classDiagram
class Settings {
+string environment
+string app_name
+string app_version
+string effective_database_url()
+int database_pool_size
+int database_max_overflow
}
class AsyncEngine {
+create_async_engine(url, pool_size, max_overflow, echo)
}
class AsyncSessionLocal {
+async_sessionmaker(class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)
}
class get_db_session {
+AsyncSession
}
Settings --> AsyncEngine : "provides URL"
AsyncEngine --> AsyncSessionLocal : "configured with"
AsyncSessionLocal --> get_db_session : "yields"
```

**Diagram sources**
- [app/core/config.py](file://app/core/config.py#L1-L74)
- [app/core/database.py](file://app/core/database.py#L1-L113)

**Section sources**
- [app/core/config.py](file://app/core/config.py#L1-L74)
- [app/core/database.py](file://app/core/database.py#L1-L113)

### Repository Pattern Implementation
- Base repository provides generic CRUD operations with async sessions.
- Domain repositories extend the base to add domain-specific queries and aggregates.
- Example: JournalEntryRepository supports listing by book, fetching by entry number or idempotency key, and verifying balances.

```mermaid
classDiagram
class BaseModel {
<<abstract>>
+UUID id
+DateTime created_at
+DateTime updated_at
+UUID created_by
+UUID updated_by
}
class BaseRepository~T~ {
-AsyncSession session
-Type~T~ model
+get_by_id(UUID) T?
+create(**kwargs) T
+update(UUID, **kwargs) T?
+delete(UUID) bool
+list_all(int, int) T[]
}
class JournalEntry
class JournalLine
class JournalEntryRepository {
+get_by_entry_number(string) JournalEntry?
+get_by_idempotency_key(string) JournalEntry?
+list_by_book(UUID, Status?, UUID?, int, int) JournalEntry[]
+verify_balance(UUID) bool
}
class JournalLineRepository {
+list_by_entry(UUID) JournalLine[]
+get_account_balance(UUID, UUID, date?) dict
}
BaseModel <|-- JournalEntry
BaseModel <|-- JournalLine
BaseRepository~T~ <|-- JournalEntryRepository
BaseRepository~T~ <|-- JournalLineRepository
JournalEntryRepository --> JournalEntry
JournalLineRepository --> JournalLine
```

**Diagram sources**
- [app/shared/models/base_model.py](file://app/shared/models/base_model.py#L1-L18)
- [app/shared/repositories/base_repository.py](file://app/shared/repositories/base_repository.py#L1-L54)
- [app/modules/general_ledger/models/journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L1-L128)
- [app/modules/general_ledger/repositories/journal_entry_repository.py](file://app/modules/general_ledger/repositories/journal_entry_repository.py#L1-L119)

**Section sources**
- [app/shared/repositories/base_repository.py](file://app/shared/repositories/base_repository.py#L1-L54)
- [app/modules/general_ledger/repositories/journal_entry_repository.py](file://app/modules/general_ledger/repositories/journal_entry_repository.py#L1-L119)

### Service Layer Operations and Validation
- Services orchestrate business logic, coordinate repositories, enforce domain rules, and handle transactions.
- Example: JournalEntryService validates periods, balances, and dimensions; posts entries; reverses entries; and supports bulk upserts with per-row error reporting.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Route as "JournalEntry Routes"
participant Service as "JournalEntryService"
participant Repo as "Repositories"
participant DB as "Database"
Client->>Route : POST /books/{book_id}/journal-entries
Route->>Service : create_draft_entry(...)
Service->>Repo : BookRepository.get_by_id()
Service->>Repo : AccountingPeriodRepository.get_by_book_and_date()
Service->>Repo : JournalEntryRepository.create()
Service-->>Route : JournalEntry
Route-->>Client : 201 Created
Client->>Route : POST /books/{book_id}/journal-entries/{entry_id}/post
Route->>Service : post_entry(...)
Service->>Repo : JournalEntryRepository.get_by_id()
Service->>Repo : JournalLineRepository.list_by_entry()
Service->>DB : commit()
Service-->>Route : Posted JournalEntry
Route-->>Client : 200 OK
```

**Diagram sources**
- [app/modules/general_ledger/api/routes/journal_entry_routes.py](file://app/modules/general_ledger/api/routes/journal_entry_routes.py#L1-L377)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L1-L635)
- [app/modules/general_ledger/repositories/journal_entry_repository.py](file://app/modules/general_ledger/repositories/journal_entry_repository.py#L1-L119)

**Section sources**
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L1-L635)
- [app/modules/general_ledger/api/routes/journal_entry_routes.py](file://app/modules/general_ledger/api/routes/journal_entry_routes.py#L1-L377)

### Request-Response Flow: Idempotency, Validation, and Error Propagation
- Idempotency ensures idempotent writes by reserving a key, preventing races, and storing responses for replay.
- Row version checks enforce optimistic concurrency for updates.
- Validation occurs in schemas and services; exceptions propagate to routes as HTTP errors.
- Audit logging captures mutations and critical actions.

```mermaid
flowchart TD
Start(["Incoming Write Request"]) --> CheckHeader["Extract Idempotency-Key"]
CheckHeader --> Reserve["Insert PENDING key (unique constraint)"]
Reserve --> Exists{"Key exists?"}
Exists -- "No" --> Execute["Execute handler (service)"]
Exists -- "Yes" --> CompareHash{"Hash matches?"}
CompareHash -- "No" --> Conflict["409 Conflict"]
CompareHash -- "Yes" --> State{"State?"}
State -- "COMPLETED" --> Replay["Replay stored response"]
State -- "PENDING" --> Stale{"Lock expired?"}
Stale -- "Yes" --> Transition["Mark FAILED and allow takeover"]
Stale -- "No" --> RetryAfter["409 Conflict + Retry-After"]
Execute --> Serialize["Serialize response (canonical JSON)"]
Serialize --> Store["Update to COMPLETED with response"]
Store --> Done(["Return response"])
Conflict --> Done
Replay --> Done
RetryAfter --> Done
Transition --> Execute
```

**Diagram sources**
- [app/core/idempotency.py](file://app/core/idempotency.py#L1-L482)
- [app/modules/core/models/idempotency_model.py](file://app/modules/core/models/idempotency_model.py#L1-L54)

**Section sources**
- [app/core/idempotency.py](file://app/core/idempotency.py#L1-L482)
- [app/modules/core/models/idempotency_model.py](file://app/modules/core/models/idempotency_model.py#L1-L54)
- [app/core/row_version.py](file://app/core/row_version.py#L1-L31)
- [app/core/exceptions.py](file://app/core/exceptions.py#L1-L43)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)

### Data Validation Flows
- Pydantic schemas define request/response contracts and basic validations.
- Service-level validations enforce business rules (e.g., balancing, period locks, dimension requirements).
- Errors are raised as typed exceptions and mapped to HTTP status codes in routes.

```mermaid
flowchart TD
A["Request Body"] --> B["Pydantic Schema Validation"]
B --> C{"Valid?"}
C -- "No" --> D["Raise ValidationError -> 400"]
C -- "Yes" --> E["Service Logic"]
E --> F{"Business Rule OK?"}
F -- "No" --> G["Raise Domain Exception -> 4xx/5xx"]
F -- "Yes" --> H["Commit to DB"]
H --> I["Return Response"]
```

**Diagram sources**
- [app/modules/general_ledger/schemas/journal_entry_schemas.py](file://app/modules/general_ledger/schemas/journal_entry_schemas.py#L1-L136)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L1-L635)
- [app/core/exceptions.py](file://app/core/exceptions.py#L1-L43)

**Section sources**
- [app/modules/general_ledger/schemas/journal_entry_schemas.py](file://app/modules/general_ledger/schemas/journal_entry_schemas.py#L1-L136)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L1-L635)
- [app/core/exceptions.py](file://app/core/exceptions.py#L1-L43)

### Audit Trail Generation
- AuditLog captures actor, action, object type/id, JSON diffs, reason, correlation ID, IP, and timestamps.
- Services can emit audit events around critical mutations.

```mermaid
erDiagram
AUDIT_LOG {
uuid id PK
uuid actor_user_id
string actor_role
string action
string object_type
uuid object_id
json before_json
json after_json
string reason
string correlation_id
string ip_address
text user_agent
timestamptz created_at
}
```

**Diagram sources**
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)

**Section sources**
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)

### Concurrency Control and Safety Mechanisms
- Idempotency keys are unique-scoped by legal entity, book, and endpoint to prevent duplicate writes.
- PENDING state and lock timestamps prevent overlapping executions; stale locks are auto-transitioned.
- Database constraints (e.g., unique source_key on journal entries) prevent duplicate postings.
- Row version checks raise conflicts when clients attempt to update stale records.

```mermaid
flowchart TD
A["POST /journal-entries/{id}/post"] --> B["apply_idempotency(...)"]
B --> C{"Insert PENDING"}
C --> D{"Unique violation?"}
D -- "Yes" --> E["Fetch existing"]
E --> F{"Same request hash?"}
F -- "No" --> G["409 Conflict"]
F -- "Yes" --> H{"State?"}
H -- "COMPLETED" --> I["Replay stored response"]
H -- "PENDING" --> J["409 Conflict + Retry-After"]
H -- "FAILED" --> K{"Safe to retry?"}
K -- "No" --> L["409 Conflict (require header)"]
K -- "Yes" --> M["Take over PENDING"]
D -- "No" --> N["Execute handler"]
N --> O["Store COMPLETED or FAILED"]
```

**Diagram sources**
- [app/core/idempotency.py](file://app/core/idempotency.py#L1-L482)
- [app/modules/general_ledger/models/journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L1-L128)
- [app/core/row_version.py](file://app/core/row_version.py#L1-L31)

**Section sources**
- [app/core/idempotency.py](file://app/core/idempotency.py#L1-L482)
- [app/modules/general_ledger/models/journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L1-L128)
- [app/core/row_version.py](file://app/core/row_version.py#L1-L31)

### Batch Processing and Synchronization
- Bulk upsert endpoints support creating/updating/deleting lines in a single operation with per-row error reporting.
- Idempotency metadata can carry correlation data (e.g., batch_id, cursors) for sync operations.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Route as "Bulk Upsert Route"
participant Service as "JournalEntryService.bulk_upsert_lines"
participant Repo as "Repositories"
participant DB as "Database"
Client->>Route : POST .../lines : bulkUpsert
Route->>Service : bulk_upsert_lines(...)
Service->>Repo : JournalEntryRepository.get_by_id()
Service->>Repo : GLAccountRepository.get_by_code_and_book()
Service->>Repo : DimensionValueRepository.get_by_dimension_and_value()
Service->>Repo : JournalLineRepository.create()/delete()/flush()
Service-->>Route : (lines, errors)
Route-->>Client : 200 OK with errors
```

**Diagram sources**
- [app/modules/general_ledger/api/routes/journal_entry_routes.py](file://app/modules/general_ledger/api/routes/journal_entry_routes.py#L309-L377)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L410-L635)

**Section sources**
- [app/modules/general_ledger/api/routes/journal_entry_routes.py](file://app/modules/general_ledger/api/routes/journal_entry_routes.py#L309-L377)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L410-L635)

## Dependency Analysis
The following diagram highlights key dependencies among modules and layers.

```mermaid
graph LR
Main["app/main.py"] --> APIv1["app/api/v1/__init__.py"]
APIv1 --> Routes["GL Routes"]
Routes --> Service["JournalEntryService"]
Service --> Repo["JournalEntryRepository"]
Repo --> Models["JournalEntry Models"]
Service --> DB["app/core/database.py"]
DB --> Config["app/core/config.py"]
Routes --> Idemp["app/core/idempotency.py"]
Idemp --> IdempModel["app/modules/core/models/idempotency_model.py"]
Service --> Audit["app/modules/core/models/audit_log_model.py"]
Service --> RowVer["app/core/row_version.py"]
Service --> Ex["app/core/exceptions.py"]
```

**Diagram sources**
- [app/main.py](file://app/main.py#L1-L54)
- [app/api/v1/__init__.py](file://app/api/v1/__init__.py#L1-L72)
- [app/modules/general_ledger/api/routes/journal_entry_routes.py](file://app/modules/general_ledger/api/routes/journal_entry_routes.py#L1-L377)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L1-L635)
- [app/modules/general_ledger/repositories/journal_entry_repository.py](file://app/modules/general_ledger/repositories/journal_entry_repository.py#L1-L119)
- [app/modules/general_ledger/models/journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L1-L128)
- [app/core/database.py](file://app/core/database.py#L1-L113)
- [app/core/config.py](file://app/core/config.py#L1-L74)
- [app/core/idempotency.py](file://app/core/idempotency.py#L1-L482)
- [app/modules/core/models/idempotency_model.py](file://app/modules/core/models/idempotency_model.py#L1-L54)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)
- [app/core/row_version.py](file://app/core/row_version.py#L1-L31)
- [app/core/exceptions.py](file://app/core/exceptions.py#L1-L43)

**Section sources**
- [app/main.py](file://app/main.py#L1-L54)
- [app/api/v1/__init__.py](file://app/api/v1/__init__.py#L1-L72)
- [app/core/database.py](file://app/core/database.py#L1-L113)

## Performance Considerations
- Asynchronous I/O: Use async SQLAlchemy to minimize blocking during I/O-bound operations.
- Connection pooling: Tune pool_size and max_overflow according to workload and database capacity.
- Pagination: Repositories support limit/offset to avoid large result sets.
- Canonical JSON serialization: Idempotency uses canonical encoding to stabilize hashes and reduce collisions.
- Constraint enforcement: Database constraints prevent invalid states and reduce application-level checks.
- Audit indexing: AuditLog indexes improve query performance for actor, object, and action filters.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- 409 Conflict on idempotency: Occurs when the same key is reused with a different request payload. Ensure stable idempotency keys and identical payloads.
- 409 Conflict on row version: Indicates concurrent modification. Clients should refresh data and retry.
- Period locked: Posting attempted in a closed period. Open the period or schedule posting for a valid period.
- Unbalanced journal entry: Debits must equal credits; fix line amounts or remove duplicates.
- Duplicate posting prevention: JournalEntry source_key uniqueness prevents double posting; adjust source_key or use idempotency.

**Section sources**
- [app/core/idempotency.py](file://app/core/idempotency.py#L1-L482)
- [app/core/row_version.py](file://app/core/row_version.py#L1-L31)
- [app/modules/general_ledger/services/journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L171-L242)
- [app/modules/general_ledger/models/journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L51-L54)
- [app/core/exceptions.py](file://app/core/exceptions.py#L1-L43)

## Conclusion
The system employs a clean separation of concerns with async SQLAlchemy, a robust repository pattern, and strong safety mechanisms. Idempotency, optimistic locking, and audit trails ensure reliable, observable, and resilient financial data operations. The modular structure supports scalable extension across domains like treasury, AR/AP, payroll, and intercompany.