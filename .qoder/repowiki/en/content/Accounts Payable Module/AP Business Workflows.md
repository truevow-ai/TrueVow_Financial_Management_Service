# AP Business Workflows

<cite>
**Referenced Files in This Document**
- [ap_bill_model.py](file://app/modules/ap/models/ap_bill_model.py)
- [ap_vendor_model.py](file://app/modules/ap/models/ap_vendor_model.py)
- [ap_withholding_model.py](file://app/modules/ap/models/ap_withholding_model.py)
- [ap_bill_service.py](file://app/modules/ap/services/ap_bill_service.py)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py)
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py)
- [ap_bill_schemas.py](file://app/modules/ap/schemas/ap_bill_schemas.py)
- [ap_bill_repository.py](file://app/modules/ap/repositories/ap_bill_repository.py)
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py)
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py)
- [sod_validator.py](file://app/modules/core/services/sod_validator.py)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py)
- [fm_schema.sql](file://database/fm_schema.sql)
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
This document describes the Accounts Payable (AP) business workflows and processes implemented in the system. It covers the complete bill lifecycle from vendor onboarding through payment processing, including approval workflows, policy enforcement, authorization patterns, and posting to the general ledger with journal entry generation. It also documents exception handling, rollback mechanisms, error recovery, compliance requirements, and audit trail generation.

## Project Structure
The AP domain is organized around models, repositories, services, schemas, and API routes. Supporting modules include approval policies, audit logging, segregation of duties (SoD), and general ledger integration.

```mermaid
graph TB
subgraph "AP Module"
A["Models<br/>ap_bill_model.py<br/>ap_vendor_model.py<br/>ap_withholding_model.py"]
B["Repositories<br/>ap_bill_repository.py"]
C["Services<br/>ap_bill_service.py<br/>ap_bill_approval_service.py<br/>ap_bill_posting_service.py"]
D["Schemas<br/>ap_bill_schemas.py"]
E["API Routes<br/>ap_bill_routes.py"]
end
subgraph "Core"
F["Approval Policy<br/>approval_policy_model.py"]
G["Audit Log<br/>audit_log_model.py"]
H["SoD Validator<br/>sod_validator.py"]
end
subgraph "General Ledger"
I["Journal Entry Models<br/>journal_entry_model.py"]
J["Journal Entry Service<br/>journal_entry_service.py"]
end
A --> B
B --> C
C --> D
D --> E
C --> F
C --> G
C --> H
C --> I
C --> J
```

**Diagram sources**
- [ap_bill_model.py](file://app/modules/ap/models/ap_bill_model.py#L20-L102)
- [ap_vendor_model.py](file://app/modules/ap/models/ap_vendor_model.py#L8-L40)
- [ap_withholding_model.py](file://app/modules/ap/models/ap_withholding_model.py#L9-L32)
- [ap_bill_repository.py](file://app/modules/ap/repositories/ap_bill_repository.py#L11-L38)
- [ap_bill_service.py](file://app/modules/ap/services/ap_bill_service.py#L15-L111)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L26-L229)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L16-L127)
- [ap_bill_schemas.py](file://app/modules/ap/schemas/ap_bill_schemas.py#L10-L114)
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py#L1-L262)
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py#L18-L36)
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)
- [sod_validator.py](file://app/modules/core/services/sod_validator.py#L55-L63)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L128)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L40-L635)

**Section sources**
- [ap_bill_model.py](file://app/modules/ap/models/ap_bill_model.py#L1-L102)
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py#L1-L262)

## Core Components
- AP Bill model defines lifecycle states, financial totals, approval and posting metadata, and relationships to vendor, lines, allocations, and journal entry.
- AP Vendor model captures vendor master data and banking details.
- AP Withholding Profile model supports optional tax-withholding configurations.
- AP Bill Service handles creation, line addition, listing, and retrieval.
- AP Bill Approval Service enforces state transitions, approval policy checks, SoD validation, and audit logging.
- AP Bill Posting Service posts bills to the general ledger, generating journal entries and updating bill status.
- API Routes expose endpoints for bill creation, listing, retrieval, approval actions, and posting with idempotency and row-version checks.
- Schemas define request/response contracts for all operations.
- Repositories encapsulate persistence queries.
- Approval Policy and Audit Log models support policy-driven approvals and compliance tracking.
- Journal Entry models and service manage ledger posting, balancing, and reversals.

**Section sources**
- [ap_bill_model.py](file://app/modules/ap/models/ap_bill_model.py#L10-L102)
- [ap_vendor_model.py](file://app/modules/ap/models/ap_vendor_model.py#L8-L40)
- [ap_withholding_model.py](file://app/modules/ap/models/ap_withholding_model.py#L9-L32)
- [ap_bill_service.py](file://app/modules/ap/services/ap_bill_service.py#L15-L111)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L26-L229)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L16-L127)
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py#L31-L262)
- [ap_bill_schemas.py](file://app/modules/ap/schemas/ap_bill_schemas.py#L21-L114)
- [ap_bill_repository.py](file://app/modules/ap/repositories/ap_bill_repository.py#L11-L38)
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py#L18-L36)
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L128)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L40-L635)

## Architecture Overview
The AP workflow follows a layered architecture:
- API routes accept requests and orchestrate operations.
- Services encapsulate business logic for bill lifecycle, approvals, and posting.
- Repositories handle data access.
- Models define domain entities and relationships.
- General Ledger integrates for journal entry creation and posting.
- Core modules enforce approvals, SoD, and audit trails.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "AP Routes"
participant BillSvc as "APBillService"
participant ApproveSvc as "APBillApprovalService"
participant PostSvc as "APBillPostingService"
participant GLSvc as "JournalEntryService"
Client->>API : "POST /books/{book_id}/ap/bills"
API->>BillSvc : "create_bill(...) + add_line(...)"
BillSvc-->>API : "Created bill with lines"
Client->>API : "POST /ap/bills/{bill_id}/submit-approval"
API->>ApproveSvc : "submit_for_approval(...)"
ApproveSvc-->>API : "Updated bill status"
Client->>API : "POST /ap/bills/{bill_id}/approve"
API->>ApproveSvc : "approve(...)"
ApproveSvc-->>API : "Approved bill"
Client->>API : "POST /ap/bills/{bill_id}/post"
API->>PostSvc : "post_bill(...)"
PostSvc->>GLSvc : "create_draft_entry(...)"
GLSvc-->>PostSvc : "Draft entry"
PostSvc->>GLSvc : "add_line(... x2)"
GLSvc-->>PostSvc : "Lines added"
PostSvc->>GLSvc : "post_entry(..., source_key)"
GLSvc-->>PostSvc : "Posted entry"
PostSvc-->>API : "Updated bill with journal_entry_id"
API-->>Client : "Bill response"
```

**Diagram sources**
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py#L31-L262)
- [ap_bill_service.py](file://app/modules/ap/services/ap_bill_service.py#L23-L111)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L34-L204)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L27-L127)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L53-L242)

## Detailed Component Analysis

### AP Bill Lifecycle and State Machine
The AP Bill progresses through a strict state machine:
- DRAFT → PENDING_APPROVAL → APPROVED → POSTED
- DRAFT → REJECTED
- DRAFT → CANCELLED (implicit via rejection or cancellation flows)

```mermaid
stateDiagram-v2
[*] --> DRAFT
DRAFT --> PENDING_APPROVAL : "submit_for_approval()"
PENDING_APPROVAL --> APPROVED : "approve()"
PENDING_APPROVAL --> REJECTED : "reject()"
APPROVED --> POSTED : "post_bill()"
DRAFT --> CANCELLED : "manual or policy"
```

**Diagram sources**
- [ap_bill_model.py](file://app/modules/ap/models/ap_bill_model.py#L10-L18)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L34-L204)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L27-L127)

**Section sources**
- [ap_bill_model.py](file://app/modules/ap/models/ap_bill_model.py#L10-L18)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L34-L204)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L27-L127)

### Approval Workflows and Policy Enforcement
- Approval policy per legal entity and object type controls whether approval is required for AP bills.
- SoD validation stubs are present for future enforcement.
- Audit logs record all approval actions with actor, role, reason, and override reason.

```mermaid
flowchart TD
Start(["Submit for Approval"]) --> CheckPolicy["Check Approval Policy"]
CheckPolicy --> Required{"Approval Required?"}
Required --> |No| AutoApprove["Set APPROVED<br/>approved_by/approved_at"]
Required --> |Yes| Pending["Set PENDING_APPROVAL<br/>submitted_by/submitted_at"]
AutoApprove --> End(["Done"])
Pending --> End
```

**Diagram sources**
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L34-L94)
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py#L18-L36)
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)

**Section sources**
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L34-L204)
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py#L9-L36)
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)
- [sod_validator.py](file://app/modules/core/services/sod_validator.py#L55-L63)

### Authorization Patterns and Idempotency
- Row-version optimistic locking is enforced on approval and posting operations.
- Idempotency keys prevent duplicate postings; the system checks idempotency and source_key uniqueness.
- Endpoint keys and replay protection are integrated at the API layer.

```mermaid
sequenceDiagram
participant API as "AP Routes"
participant PostSvc as "APBillPostingService"
participant GLSvc as "JournalEntryService"
API->>API : "require_idempotency_key()"
API->>PostSvc : "post_bill(bill_id, posted_by, row_version)"
PostSvc->>PostSvc : "check_row_version(row_version)"
PostSvc->>GLSvc : "create_draft_entry(...)"
GLSvc-->>PostSvc : "Draft entry"
PostSvc->>GLSvc : "post_entry(..., source_key)"
GLSvc-->>PostSvc : "Posted entry"
PostSvc-->>API : "Return updated bill"
```

**Diagram sources**
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py#L196-L262)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L27-L127)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L171-L242)

**Section sources**
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py#L196-L262)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L27-L127)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L171-L242)

### Posting Workflows to General Ledger
- Posting creates a draft journal entry with source metadata.
- Two lines are added: debit to expense and credit to liability using mapped accounts.
- Posting validates period status, balances, and uniqueness via source_key.
- On success, bill status updates to POSTED and journal_entry_id is recorded.

```mermaid
flowchart TD
Start(["post_bill()"]) --> Validate["Validate bill status APPROVED"]
Validate --> Lines["Load bill lines"]
Lines --> CreateJE["create_draft_entry(book_id, bill_date, description)"]
CreateJE --> Debit["add_line(debit EXP_AP)"]
Debit --> Credit["add_line(credit LIAB_AP)"]
Credit --> Post["post_entry(source_key)"]
Post --> UpdateBill["Update bill: status=POSTED,<br/>posted_by/posted_at,<br/>journal_entry_id"]
UpdateBill --> End(["Done"])
```

**Diagram sources**
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L27-L127)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L53-L242)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)

**Section sources**
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L27-L127)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L53-L242)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)

### Exception Handling, Rollback Mechanisms, and Error Recovery
- Validation errors are raised for invalid states (e.g., posting non-approved bills).
- Period locks prevent posting to closed periods.
- Duplicate posting prevention uses idempotency keys and source_key uniqueness.
- Reversal capability exists for posted journal entries to support error recovery.
- Audit logs capture reasons and override reasons for decisions.

```mermaid
flowchart TD
Start(["Operation"]) --> TryOp["Execute operation"]
TryOp --> Ok{"Success?"}
Ok --> |Yes| Commit["Commit transaction"]
Ok --> |No| HandleErr["Raise appropriate error"]
HandleErr --> Recover{"Recoverable?"}
Recover --> |Yes| Rollback["Rollback transaction"]
Recover --> |No| Report["Report to caller"]
Rollback --> Report
Commit --> End(["Done"])
```

**Diagram sources**
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L21-L23)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L13-L13)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L171-L242)

**Section sources**
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L21-L23)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L13-L13)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L171-L242)

### Compliance Requirements and Audit Trail Generation
- Audit log records actor, role, action, object, timestamps, reason, and correlation identifiers.
- Approval actions are audited with decision reasons and override reasons.
- Journal entries include source metadata and source_key to prevent duplicates.

```mermaid
classDiagram
class AuditLog {
+UUID id
+UUID actor_user_id
+String actor_role
+String action
+String object_type
+UUID object_id
+Text reason
+String correlation_id
+DateTime created_at
}
class APBillApprovalService {
+submit_for_approval(...)
+approve(...)
+reject(...)
-_log_audit(...)
}
APBillApprovalService --> AuditLog : "creates"
```

**Diagram sources**
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L206-L229)

**Section sources**
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L206-L229)

### Multi-Level Approvals and Policy Configurations
- Approval policy is configured per legal entity and object type.
- The current implementation supports a binary requirement flag; multi-level approvals can be extended by adding policy tiers and routing logic.

```mermaid
classDiagram
class ApprovalPolicy {
+UUID legal_entity_id
+ApprovalObjectType object_type
+Boolean approval_required
}
class APBillApprovalService {
+submit_for_approval(...)
}
APBillApprovalService --> ApprovalPolicy : "checks"
```

**Diagram sources**
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py#L18-L36)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L62-L78)

**Section sources**
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py#L18-L36)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L62-L78)

### Workflow Customization Examples
- Disable approvals per legal entity by setting approval_required=false for AP_BILL.
- Override SoD checks via override_reason when permitted by policy.
- Customize posting behavior by adjusting account mappings and dimension requirements.

**Section sources**
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py#L18-L36)
- [sod_validator.py](file://app/modules/core/services/sod_validator.py#L55-L63)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L344-L381)

## Dependency Analysis
The AP module depends on core modules for approvals and auditing, and on general ledger for posting. The dependency graph highlights tight cohesion within AP services and clear boundaries to GL.

```mermaid
graph LR
APBillRoutes["ap_bill_routes.py"] --> APBillService["ap_bill_service.py"]
APBillRoutes --> APBillApprovalService["ap_bill_approval_service.py"]
APBillRoutes --> APBillPostingService["ap_bill_posting_service.py"]
APBillService --> APBillRepository["ap_bill_repository.py"]
APBillApprovalService --> ApprovalPolicyModel["approval_policy_model.py"]
APBillApprovalService --> AuditLogModel["audit_log_model.py"]
APBillApprovalService --> SoDValidator["sod_validator.py"]
APBillPostingService --> JournalEntryService["journal_entry_service.py"]
APBillPostingService --> JournalEntryModel["journal_entry_model.py"]
```

**Diagram sources**
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py#L1-L262)
- [ap_bill_service.py](file://app/modules/ap/services/ap_bill_service.py#L15-L111)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L26-L229)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L16-L127)
- [ap_bill_repository.py](file://app/modules/ap/repositories/ap_bill_repository.py#L11-L38)
- [approval_policy_model.py](file://app/modules/core/models/approval_policy_model.py#L18-L36)
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)
- [sod_validator.py](file://app/modules/core/services/sod_validator.py#L55-L63)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L40-L635)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L128)

**Section sources**
- [ap_bill_routes.py](file://app/modules/ap/api/routes/ap_bill_routes.py#L1-L262)
- [ap_bill_service.py](file://app/modules/ap/services/ap_bill_service.py#L15-L111)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L26-L229)
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L16-L127)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L40-L635)

## Performance Considerations
- Use pagination and filtering in bill listing to avoid large result sets.
- Batch operations for line additions can reduce round-trips.
- Journal entry posting validates balances and dimensions; ensure minimal line count per entry to improve performance.
- Indexes on frequently queried fields (status, dates, vendor) improve query performance.

## Troubleshooting Guide
Common issues and resolutions:
- Posting fails with validation errors: Ensure bill is APPROVED and has at least one line.
- Period locked error: Verify accounting period status before posting.
- Duplicate posting prevented: Use unique idempotency keys and source_key values.
- Approval errors: Confirm policy requires approval and SoD rules are satisfied.
- Audit trail gaps: Verify audit log configuration and that actions trigger logging.

**Section sources**
- [ap_bill_posting_service.py](file://app/modules/ap/services/ap_bill_posting_service.py#L13-L13)
- [journal_entry_service.py](file://app/modules/general_ledger/services/journal_entry_service.py#L171-L242)
- [ap_bill_approval_service.py](file://app/modules/ap/services/ap_bill_approval_service.py#L21-L23)
- [audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)

## Conclusion
The AP module implements a robust, policy-driven workflow with strong compliance and audit capabilities. It integrates tightly with general ledger for accurate posting and supports idempotency and SoD controls. Extensibility points exist for multi-level approvals and enhanced policy configurations.

## Appendices

### Data Model Overview
```mermaid
erDiagram
AP_BILL {
uuid id PK
uuid legal_entity_id FK
uuid book_id FK
uuid ap_vendor_id FK
string bill_number
date bill_date
date due_date
numeric total_amount
string currency
enum status
numeric paid_amount
numeric outstanding_amount
uuid journal_entry_id FK
}
AP_VENDOR {
uuid id PK
uuid legal_entity_id FK
string vendor_code
string vendor_name
string vendor_type
string contact_email
string contact_phone
string tax_id
string payment_terms
string default_currency
string bank_name
string bank_account_number
string iban
string swift_code
text address
string country
boolean is_active
}
JOURNAL_ENTRY {
uuid id PK
uuid legal_entity_id FK
uuid book_id FK
uuid period_id FK
string entry_number
date entry_date
text description
string reference_number
enum status
string source_service
string source_type
uuid source_id
string idempotency_key
string source_key
}
AP_BILL }o--|| AP_VENDOR : "vendor"
AP_BILL }o--o| JOURNAL_ENTRY : "journal_entry"
```

**Diagram sources**
- [ap_bill_model.py](file://app/modules/ap/models/ap_bill_model.py#L20-L66)
- [ap_vendor_model.py](file://app/modules/ap/models/ap_vendor_model.py#L8-L32)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)

**Section sources**
- [ap_bill_model.py](file://app/modules/ap/models/ap_bill_model.py#L20-L66)
- [ap_vendor_model.py](file://app/modules/ap/models/ap_vendor_model.py#L8-L32)
- [journal_entry_model.py](file://app/modules/general_ledger/models/journal_entry_model.py#L17-L57)
- [fm_schema.sql](file://database/fm_schema.sql#L1-L200)