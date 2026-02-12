# Payroll Module

<cite>
**Referenced Files in This Document**
- [employee_model.py](file://app/modules/payroll/models/employee_model.py)
- [payroll_run_model.py](file://app/modules/payroll/models/payroll_run_model.py)
- [payment_batch_model.py](file://app/modules/payroll/models/payment_batch_model.py)
- [pay_component_model.py](file://app/modules/payroll/models/pay_component_model.py)
- [pay_group_model.py](file://app/modules/payroll/models/pay_group_model.py)
- [bonus_model.py](file://app/modules/payroll/models/bonus_model.py)
- [commission_model.py](file://app/modules/payroll/models/commission_model.py)
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py)
- [payment_batch_service.py](file://app/modules/payroll/services/payment_batch_service.py)
- [payroll_approval_service.py](file://app/modules/payroll/services/payroll_approval_service.py)
- [payroll_run_routes.py](file://app/modules/payroll/api/routes/payroll_run_routes.py)
- [payment_batch_routes.py](file://app/modules/payroll/api/routes/payment_batch_routes.py)
- [wps_export.py](file://app/modules/payroll/plugins/wps_export.py)
- [employee_repository.py](file://app/modules/payroll/repositories/employee_repository.py)
- [payroll_run_repository.py](file://app/modules/payroll/repositories/payroll_run_repository.py)
- [payment_batch_repository.py](file://app/modules/payroll/repositories/payment_batch_repository.py)
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
This document describes the Payroll module, covering employee management, compensation calculation, payroll run processing, and tax deduction management. It explains the payroll calculation service, payroll run service, payment batch service, and payroll approval service implementations. It also documents the employee, payroll run, payment batch, pay component, and pay group models, along with payroll run and payment batch routes. Practical examples illustrate payroll processing workflows, tax calculations, payment distribution, approval workflows, and regulatory compliance.

## Project Structure
The Payroll module follows a layered architecture:
- Models define domain entities and relationships
- Services encapsulate business logic and workflows
- Repositories handle data access
- Plugins provide export capabilities
- API routes expose endpoints for payroll operations

```mermaid
graph TB
subgraph "Models"
EM["HREmployee<br/>Employee Bank Details"]
PR["PayrollRun<br/>PayrollRunItem<br/>PayrollRunComponentLine"]
PB["PayrollPaymentBatch"]
PC["PayComponentDefinition<br/>PayComponentAssignment"]
PG["PayGroup"]
B["BonusPlan<br/>BonusResult"]
C["CommissionPlan<br/>CommissionRule<br/>CommissionLedger"]
end
subgraph "Services"
PCS["PayrollCalculationService"]
PRS["PayrollRunService"]
PBS["PaymentBatchService"]
PAS["PayrollApprovalService"]
end
subgraph "Repositories"
ER["HREmployeeRepository"]
PRR["PayrollRunRepository<br/>PayrollRunItemRepository<br/>PayrollRunComponentLineRepository"]
PBR["PayrollPaymentBatchRepository"]
end
subgraph "Plugins"
WPS["UAEWPSExporter"]
end
subgraph "API Routes"
PRRoutes["Payroll Run Routes"]
PBRoutes["Payment Batch Routes"]
end
EM --> ER
PR --> PRR
PB --> PBR
PC --> PRR
PG --> ER
B --> PRR
C --> PRR
PCS --> ER
PCS --> PC
PRS --> PCS
PRS --> PRR
PRS --> PRR
PRS --> WPS
PBS --> PRR
PBS --> ER
PBS --> PBR
PBS --> WPS
PAS --> PRR
PRRoutes --> PRS
PRRoutes --> PAS
PBRoutes --> PBS
```

**Diagram sources**
- [employee_model.py](file://app/modules/payroll/models/employee_model.py#L16-L75)
- [payroll_run_model.py](file://app/modules/payroll/models/payroll_run_model.py#L23-L117)
- [payment_batch_model.py](file://app/modules/payroll/models/payment_batch_model.py#L18-L42)
- [pay_component_model.py](file://app/modules/payroll/models/pay_component_model.py#L38-L88)
- [pay_group_model.py](file://app/modules/payroll/models/pay_group_model.py#L24-L48)
- [bonus_model.py](file://app/modules/payroll/models/bonus_model.py#L16-L63)
- [commission_model.py](file://app/modules/payroll/models/commission_model.py#L17-L101)
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py#L22-L138)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L25-L416)
- [payment_batch_service.py](file://app/modules/payroll/services/payment_batch_service.py#L16-L133)
- [payroll_approval_service.py](file://app/modules/payroll/services/payroll_approval_service.py#L26-L253)
- [wps_export.py](file://app/modules/payroll/plugins/wps_export.py#L9-L88)
- [employee_repository.py](file://app/modules/payroll/repositories/employee_repository.py#L10-L53)
- [payroll_run_repository.py](file://app/modules/payroll/repositories/payroll_run_repository.py#L16-L107)
- [payment_batch_repository.py](file://app/modules/payroll/repositories/payment_batch_repository.py#L10-L38)
- [payroll_run_routes.py](file://app/modules/payroll/api/routes/payroll_run_routes.py#L25-L302)
- [payment_batch_routes.py](file://app/modules/payroll/api/routes/payment_batch_routes.py#L10-L59)

**Section sources**
- [payroll_run_routes.py](file://app/modules/payroll/api/routes/payroll_run_routes.py#L25-L302)
- [payment_batch_routes.py](file://app/modules/payroll/api/routes/payment_batch_routes.py#L10-L59)

## Core Components
- Employee Management: HREmployee and related bank details, with pay group associations and component assignments
- Compensation Calculation: PayrollCalculationService computes earnings, deductions, and employer contributions per employee
- Payroll Run Processing: PayrollRunService orchestrates run creation, calculation, approval, posting, and reversal
- Payment Batch Management: PaymentBatchService generates WPS export batches and manages batch lifecycle
- Approval Workflow: PayrollApprovalService enforces state transitions and segregation of duties
- Pay Components and Groups: PayComponentDefinition and PayGroup define standardized pay components and grouping rules
- Bonus and Commission: BonusResult and CommissionLedger integrate variable pay into payroll runs

**Section sources**
- [employee_model.py](file://app/modules/payroll/models/employee_model.py#L16-L75)
- [pay_component_model.py](file://app/modules/payroll/models/pay_component_model.py#L38-L88)
- [pay_group_model.py](file://app/modules/payroll/models/pay_group_model.py#L24-L48)
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py#L22-L138)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L25-L416)
- [payment_batch_service.py](file://app/modules/payroll/services/payment_batch_service.py#L16-L133)
- [payroll_approval_service.py](file://app/modules/payroll/services/payroll_approval_service.py#L26-L253)
- [bonus_model.py](file://app/modules/payroll/models/bonus_model.py#L16-L63)
- [commission_model.py](file://app/modules/payroll/models/commission_model.py#L17-L101)

## Architecture Overview
The Payroll module implements a clean separation of concerns:
- Models represent domain entities with relationships and constraints
- Services encapsulate workflows and enforce business rules
- Repositories abstract persistence
- Plugins encapsulate export-specific logic
- Routes bind services to HTTP endpoints

```mermaid
sequenceDiagram
participant Client as "Client"
participant Routes as "Payroll Run Routes"
participant Service as "PayrollRunService"
participant Calc as "PayrollCalculationService"
participant Repo as "PayrollRunRepository"
participant ItemRepo as "PayrollRunItemRepository"
Client->>Routes : POST /books/{book_id}/payroll/runs/{run_id}/calculate
Routes->>Service : calculate_run(run_id)
Service->>Repo : get_by_id(run_id)
Service->>Service : list_by_pay_group(pay_group_id, active_only=true)
loop For each employee
Service->>Calc : calculate_employee_pay(employee_id, pay_period_start, pay_period_end)
Calc-->>Service : {gross, deductions, net, employer_contrib, component_lines}
Service->>ItemRepo : create(run_item)
Service->>Service : create_component_line(...) for each component
end
Service->>Repo : update(totals, status=CALCULATED)
Service-->>Routes : PayrollRun
Routes-->>Client : 200 OK
```

**Diagram sources**
- [payroll_run_routes.py](file://app/modules/payroll/api/routes/payroll_run_routes.py#L52-L66)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L75-L148)
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py#L33-L124)
- [payroll_run_repository.py](file://app/modules/payroll/repositories/payroll_run_repository.py#L16-L62)
- [payroll_run_repository.py](file://app/modules/payroll/repositories/payroll_run_repository.py#L64-L92)

## Detailed Component Analysis

### Employee Management
- HREmployee stores personal and employment details, including pay group and WPS fields
- HREmployeeBank holds bank details with a unique primary account per employee
- Relationships connect employees to pay groups, component assignments, run items, and commission ledger

```mermaid
classDiagram
class HREmployee {
+UUID id
+UUID legal_entity_id
+String employee_code
+String employee_name
+EmployeeType employee_type
+String country
+String location
+UUID pay_group_id
+String currency
+Date hire_date
+Date termination_date
+Boolean is_active
+Boolean wps_enabled
+String labour_id
+String mol_id
+String iban
}
class HREmployeeBank {
+UUID id
+UUID hr_employee_id
+String bank_name
+String account_number
+String iban
+String swift_code
+Boolean is_primary
}
HREmployeeBank --> HREmployee : "belongsTo"
```

**Diagram sources**
- [employee_model.py](file://app/modules/payroll/models/employee_model.py#L16-L75)

**Section sources**
- [employee_model.py](file://app/modules/payroll/models/employee_model.py#L16-L75)
- [employee_repository.py](file://app/modules/payroll/repositories/employee_repository.py#L10-L53)

### Payroll Run Models
- PayrollRun tracks run metadata, totals, and approval/posting state
- PayrollRunItem captures per-employee pay details and links to component lines
- PayrollRunComponentLine records detailed component amounts and notes

```mermaid
classDiagram
class PayrollRun {
+UUID id
+UUID legal_entity_id
+UUID book_id
+UUID pay_group_id
+String run_number
+Date pay_period_start
+Date pay_period_end
+Date pay_date
+PayrollRunStatus status
+Decimal total_gross
+Decimal total_deductions
+Decimal total_net
+Decimal total_employer_contrib
+String currency
+Integer row_version
+UUID submitted_by
+DateTime submitted_at
+UUID approved_by
+DateTime approved_at
+UUID rejected_by
+DateTime rejected_at
+Text decision_reason
+UUID posted_by
+DateTime posted_at
+UUID journal_entry_id
+Text notes
}
class PayrollRunItem {
+UUID id
+UUID payroll_run_id
+UUID hr_employee_id
+Decimal gross_pay
+Decimal total_deductions
+Decimal net_pay
+Decimal employer_contributions
+String currency
}
class PayrollRunComponentLine {
+UUID id
+UUID payroll_run_item_id
+UUID pay_component_id
+Decimal amount
+String currency
+Text calculation_note
}
PayrollRunItem --> PayrollRun : "belongsTo"
PayrollRunComponentLine --> PayrollRunItem : "belongsTo"
```

**Diagram sources**
- [payroll_run_model.py](file://app/modules/payroll/models/payroll_run_model.py#L23-L117)

**Section sources**
- [payroll_run_model.py](file://app/modules/payroll/models/payroll_run_model.py#L23-L117)
- [payroll_run_repository.py](file://app/modules/payroll/repositories/payroll_run_repository.py#L16-L107)

### Payment Batch Models
- PayrollPaymentBatch represents export batches (e.g., WPS SIF), tracking status, file metadata, and export details

```mermaid
classDiagram
class PayrollPaymentBatch {
+UUID id
+UUID payroll_run_id
+String batch_number
+String export_type
+BatchStatus status
+String file_path
+String file_hash
+Integer file_size
+DateTime exported_at
+UUID exported_by
+Text batch_metadata
}
PayrollPaymentBatch --> PayrollRun : "belongsTo"
```

**Diagram sources**
- [payment_batch_model.py](file://app/modules/payroll/models/payment_batch_model.py#L18-L42)

**Section sources**
- [payment_batch_model.py](file://app/modules/payroll/models/payment_batch_model.py#L18-L42)
- [payment_batch_repository.py](file://app/modules/payroll/repositories/payment_batch_repository.py#L10-L38)

### Pay Component Models
- PayComponentDefinition defines standardized components (earnings, deductions, employer contributions) with taxability and WPS flags
- PayComponentAssignment links components to employees with amounts/rates and effective dates

```mermaid
classDiagram
class PayComponentDefinition {
+UUID id
+UUID legal_entity_id
+String component_code
+String component_name
+ComponentType component_type
+Boolean is_taxable
+Boolean affects_wps_net
+String gl_map_key
+Boolean is_active
}
class PayComponentAssignment {
+UUID id
+UUID hr_employee_id
+UUID pay_component_id
+Decimal amount
+Decimal rate
+Boolean is_active
+Date effective_from
+Date effective_to
}
PayComponentAssignment --> HREmployee : "belongsTo"
PayComponentAssignment --> PayComponentDefinition : "belongsTo"
```

**Diagram sources**
- [pay_component_model.py](file://app/modules/payroll/models/pay_component_model.py#L38-L88)

**Section sources**
- [pay_component_model.py](file://app/modules/payroll/models/pay_component_model.py#L38-L88)

### Pay Group Models
- PayGroup defines pay frequency, pay day rules, currency, and WPS enablement per legal entity

```mermaid
classDiagram
class PayGroup {
+UUID id
+UUID legal_entity_id
+String group_code
+String group_name
+PayFrequency frequency
+String payroll_currency
+PayDayRule pay_day_rule
+Boolean wps_enabled
+Boolean is_active
}
PayGroup --> HREmployee : "hasMany"
PayGroup --> PayrollRun : "hasMany"
```

**Diagram sources**
- [pay_group_model.py](file://app/modules/payroll/models/pay_group_model.py#L24-L48)

**Section sources**
- [pay_group_model.py](file://app/modules/payroll/models/pay_group_model.py#L24-L48)

### Bonus and Commission Models
- BonusPlan and BonusResult manage one-time and periodic bonuses
- CommissionPlan, CommissionRule, and CommissionLedger track accruals and payouts

```mermaid
classDiagram
class BonusPlan {
+UUID id
+UUID legal_entity_id
+String plan_code
+String plan_name
+BonusType bonus_type
+Boolean is_active
}
class BonusResult {
+UUID id
+UUID bonus_plan_id
+UUID hr_employee_id
+Date bonus_date
+Decimal bonus_amount
+String currency
+Text description
+Boolean is_paid
+Date paid_at
+UUID payroll_run_id
}
class CommissionPlan {
+UUID id
+UUID legal_entity_id
+String plan_code
+String plan_name
+CommissionBasis basis
+String payout_mode
+Decimal default_recognized_rate
+Decimal default_collected_rate
+Boolean is_active
}
class CommissionRule {
+UUID id
+UUID commission_plan_id
+String applies_to
+String role
+UUID employee_id
+Text sku_filter
+Decimal tier_from
+Decimal tier_to
+Decimal recognized_rate
+Decimal collected_rate
+Boolean is_active
}
class CommissionLedger {
+UUID id
+UUID legal_entity_id
+UUID commission_plan_id
+UUID hr_employee_id
+Date period_start
+Date period_end
+Decimal recognized_revenue_base
+Decimal collected_revenue_base
+Decimal recognized_commission
+Decimal collected_commission
+Decimal total_commission
+String currency
+Boolean is_paid
+Date paid_at
+UUID payroll_run_id
}
BonusResult --> HREmployee : "belongsTo"
BonusResult --> PayrollRun : "belongsTo"
CommissionRule --> CommissionPlan : "belongsTo"
CommissionLedger --> HREmployee : "belongsTo"
CommissionLedger --> PayrollRun : "belongsTo"
```

**Diagram sources**
- [bonus_model.py](file://app/modules/payroll/models/bonus_model.py#L16-L63)
- [commission_model.py](file://app/modules/payroll/models/commission_model.py#L17-L101)

**Section sources**
- [bonus_model.py](file://app/modules/payroll/models/bonus_model.py#L16-L63)
- [commission_model.py](file://app/modules/payroll/models/commission_model.py#L17-L101)

### Payroll Calculation Service
Responsibilities:
- Validates employee eligibility
- Aggregates component assignments (fixed amount or rate-based)
- Includes unpaid commissions and bonuses within the pay period
- Produces component lines and totals

```mermaid
flowchart TD
Start(["calculate_employee_pay"]) --> LoadEmp["Load employee and validate active"]
LoadEmp --> GetAssignments["List active assignments effective on pay period end"]
GetAssignments --> InitAmts["Initialize earnings/deductions/employer_contrib=0"]
InitAmts --> LoopAssign["For each assignment"]
LoopAssign --> FetchComp["Fetch component definition"]
FetchComp --> IsInactive{"Component active?"}
IsInactive --> |No| NextAssign["Skip assignment"]
IsInactive --> |Yes| CalcAmount["Compute amount (amount or rate*base)"]
CalcAmount --> AppendLine["Append component line"]
AppendLine --> TypeCheck{"Type EARNING/Deduction/Contrib?"}
TypeCheck --> |EARNING| IncEarn["Add to earnings"]
TypeCheck --> |DEDUCTION| IncDed["Add to deductions"]
TypeCheck --> |EMPLOYER_CONTRIBUTION| IncEmp["Add to employer contrib"]
IncEarn --> NextAssign
IncDed --> NextAssign
IncEmp --> NextAssign
NextAssign --> LoopAssign
LoopAssign --> Commissions["Add unpaid commissions in period"]
Commissions --> Bonuses["Add unpaid bonuses in period"]
Bonuses --> NetPay["net_pay = earnings - deductions"]
NetPay --> ReturnRes["Return totals and component lines"]
```

**Diagram sources**
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py#L33-L124)

**Section sources**
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py#L22-L138)

### Payroll Run Service
Responsibilities:
- Create runs with generated run numbers
- Calculate runs by invoking the calculation service and persisting items and component lines
- Manage approval workflow transitions
- Post runs to the general ledger with proper mappings and idempotency
- Reverse posted runs with period-aware reversal and audit trail

```mermaid
sequenceDiagram
participant Client as "Client"
participant Routes as "Payroll Run Routes"
participant Service as "PayrollRunService"
participant Calc as "PayrollCalculationService"
participant GL as "JournalEntryService"
participant Map as "GLAccountMappingRepository"
Client->>Routes : POST /books/{book_id}/payroll/runs
Routes->>Service : create_run(...)
Service-->>Routes : PayrollRun(DRAFT)
Client->>Routes : POST /books/{book_id}/payroll/runs/{run_id}/calculate
Routes->>Service : calculate_run(run_id)
Service->>Calc : calculate_employee_pay(...)
Service-->>Routes : PayrollRun(CALCULATED)
Client->>Routes : POST /books/{book_id}/payroll/runs/{run_id}/post
Routes->>Service : post_run(run_id, posted_by, row_version)
Service->>Map : get mapping(EXP_PAYROLL, LIAB_PAYROLL, EXP_EMPLOYER_CONTRIB)
Service->>GL : create_draft_entry(...)
Service->>GL : add_line(...), add_line(...)
Service->>GL : post_entry(source_key)
Service-->>Routes : journal_entry_id
```

**Diagram sources**
- [payroll_run_routes.py](file://app/modules/payroll/api/routes/payroll_run_routes.py#L28-L199)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L38-L314)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L405-L416)

**Section sources**
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L25-L416)

### Payment Batch Service
Responsibilities:
- Generate WPS SIF batches for posted runs
- Validate employee data against WPS requirements
- Compute file hash and metadata
- Provide batch file download capability

```mermaid
flowchart TD
Start(["generate_wps_batch"]) --> LoadRun["Load payroll run and validate status=POSTED"]
LoadRun --> GetItems["List run items"]
GetItems --> FilterEmp["Filter employees with wps_enabled"]
FilterEmp --> Validate["Validate employee data via UAEWPSExporter"]
Validate --> BuildList["Build employee list with IBAN, net_pay, reference"]
BuildList --> GenSIF["Generate SIF content"]
GenSIF --> Hash["Compute SHA-256 hash"]
Hash --> CreateBatch["Persist PayrollPaymentBatch (GENERATED)"]
CreateBatch --> Commit["Commit transaction"]
Commit --> Return["Return batch info"]
```

**Diagram sources**
- [payment_batch_service.py](file://app/modules/payroll/services/payment_batch_service.py#L27-L96)
- [wps_export.py](file://app/modules/payroll/plugins/wps_export.py#L41-L88)

**Section sources**
- [payment_batch_service.py](file://app/modules/payroll/services/payment_batch_service.py#L16-L133)
- [wps_export.py](file://app/modules/payroll/plugins/wps_export.py#L9-L88)

### Payroll Approval Service
Responsibilities:
- Enforce state transitions: CALCULATED → PENDING_APPROVAL → APPROVED or REJECTED
- Integrate with approval policy repository to determine if approval is required
- Enforce segregation of duties (SoD) checks
- Log audit actions with before/after status and reasons

```mermaid
stateDiagram-v2
[*] --> Calculated
Calculated --> PendingApproval : "submit_for_approval()"
PendingApproval --> Approved : "approve()"
PendingApproval --> Rejected : "reject()"
Approved --> Posted : "post_run()"
Posted --> Reversed : "reverse_run()"
```

**Diagram sources**
- [payroll_approval_service.py](file://app/modules/payroll/services/payroll_approval_service.py#L26-L253)
- [payroll_run_model.py](file://app/modules/payroll/models/payroll_run_model.py#L10-L21)

**Section sources**
- [payroll_approval_service.py](file://app/modules/payroll/services/payroll_approval_service.py#L26-L253)

### Payroll Run Routes
Endpoints:
- Create payroll run
- Calculate payroll run
- Submit for approval
- Approve payroll run
- Reject payroll run
- Post payroll run (with idempotency)
- Reverse payroll run (restricted)
- List and retrieve payroll runs

```mermaid
sequenceDiagram
participant Client as "Client"
participant Routes as "Payroll Run Routes"
participant Service as "PayrollRunService"
participant Approval as "PayrollApprovalService"
Client->>Routes : POST /runs
Routes->>Service : create_run(...)
Routes-->>Client : 201 PayrollRun
Client->>Routes : POST /runs/{run_id}/calculate
Routes->>Service : calculate_run(run_id)
Routes-->>Client : 200 PayrollRun
Client->>Routes : POST /runs/{run_id}/submit-approval
Routes->>Approval : submit_for_approval(...)
Routes-->>Client : 200 PayrollRun
Client->>Routes : POST /runs/{run_id}/approve
Routes->>Approval : approve(...)
Routes-->>Client : 200 PayrollRun
Client->>Routes : POST /runs/{run_id}/post
Routes->>Service : post_run(...)
Routes-->>Client : {payroll_run_id, journal_entry_id, status}
Client->>Routes : POST /runs/{run_id}/reverse
Routes->>Service : reverse_run(...)
Routes-->>Client : 200 PayrollRun
```

**Diagram sources**
- [payroll_run_routes.py](file://app/modules/payroll/api/routes/payroll_run_routes.py#L28-L302)

**Section sources**
- [payroll_run_routes.py](file://app/modules/payroll/api/routes/payroll_run_routes.py#L25-L302)

### Payment Batch Routes
Endpoints:
- Generate WPS batch for a run
- Download batch file

```mermaid
sequenceDiagram
participant Client as "Client"
participant Routes as "Payment Batch Routes"
participant Service as "PaymentBatchService"
Client->>Routes : POST /runs/{run_id}/wps-batch
Routes->>Service : generate_wps_batch(run_id, exported_by)
Routes-->>Client : {batch_id, batch_number, export_type, status, file_size}
Client->>Routes : GET /batches/{batch_id}/download
Routes->>Service : get_batch_file(batch_id)
Routes-->>Client : SIF file attachment
```

**Diagram sources**
- [payment_batch_routes.py](file://app/modules/payroll/api/routes/payment_batch_routes.py#L13-L59)

**Section sources**
- [payment_batch_routes.py](file://app/modules/payroll/api/routes/payment_batch_routes.py#L10-L59)

## Dependency Analysis
- Services depend on repositories for data access and on other services for cross-cutting logic
- Models define relationships that repositories leverage for queries
- Routes depend on services and enforce authorization and idempotency
- Plugins encapsulate export-specific logic, minimizing coupling

```mermaid
graph LR
PCS["PayrollCalculationService"] --> ER["HREmployeeRepository"]
PCS --> PCR["PayComponentDefinitionRepository"]
PCS --> PAR["PayComponentAssignmentRepository"]
PCS --> CLR["CommissionLedgerRepository"]
PCS --> BR["BonusResultRepository"]
PRS["PayrollRunService"] --> PCS
PRS --> PRR["PayrollRunRepository"]
PRS --> PRI["PayrollRunItemRepository"]
PRS --> PRC["PayrollRunComponentLineRepository"]
PRS --> GL["JournalEntryService"]
PRS --> MAP["GLAccountMappingRepository"]
PBS["PaymentBatchService"] --> PRR
PBS --> PRI
PBS --> ER
PBS --> PBR["PayrollPaymentBatchRepository"]
PBS --> WPS["UAEWPSExporter"]
PAS["PayrollApprovalService"] --> PRR
PAS --> POL["ApprovalPolicyRepository"]
```

**Diagram sources**
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py#L7-L31)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L7-L36)
- [payment_batch_service.py](file://app/modules/payroll/services/payment_batch_service.py#L7-L25)
- [payroll_approval_service.py](file://app/modules/payroll/services/payroll_approval_service.py#L13-L32)

**Section sources**
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py#L22-L138)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L25-L416)
- [payment_batch_service.py](file://app/modules/payroll/services/payment_batch_service.py#L16-L133)
- [payroll_approval_service.py](file://app/modules/payroll/services/payroll_approval_service.py#L26-L253)

## Performance Considerations
- Use repository methods with filtering and ordering to minimize result sets
- Batch operations for run item creation and component line creation
- Optimize queries with indexed columns (run number, employee code, pay group)
- Employ idempotency keys for safe reprocessing of posting and reversal operations
- Cache GL account mappings when feasible to reduce repeated lookups

## Troubleshooting Guide
Common issues and resolutions:
- Employee not found or inactive: Ensure employee exists and is active before calculation
- Invalid run status: Verify run is in the expected state (e.g., CALCULATED before approval, POSTED before reversal)
- Missing approval policy: If approval is required but policy not configured, submission may fail
- SoD violations: Review segregation of duties constraints and adjust roles or override reasons accordingly
- WPS validation failures: Confirm employee data meets IBAN format and mandatory fields requirements
- Idempotency errors: Reuse the same idempotency key for retries; avoid changing request body unintentionally

**Section sources**
- [payroll_calculation_service.py](file://app/modules/payroll/services/payroll_calculation_service.py#L40-L46)
- [payroll_run_service.py](file://app/modules/payroll/services/payroll_run_service.py#L172-L189)
- [payroll_approval_service.py](file://app/modules/payroll/services/payroll_approval_service.py#L62-L79)
- [wps_export.py](file://app/modules/payroll/plugins/wps_export.py#L67-L88)

## Conclusion
The Payroll module provides a robust framework for managing employee data, calculating compensation, processing payroll runs, generating payment batches, and enforcing approvals and compliance. Its modular design supports extensibility (e.g., additional export formats) while maintaining strong data integrity and auditability.