# Authentication & Authorization

<cite>
**Referenced Files in This Document**
- [app/auth/__init__.py](file://app/auth/__init__.py)
- [app/auth/middleware.py](file://app/auth/middleware.py)
- [app/auth/permissions.py](file://app/auth/permissions.py)
- [app/auth/roles.py](file://app/auth/roles.py)
- [app/core/config.py](file://app/core/config.py)
- [app/core/logging.py](file://app/core/logging.py)
- [app/core/middleware.py](file://app/core/middleware.py)
- [app/main.py](file://app/main.py)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py)
- [frontend/hooks/useClerkToken.ts](file://frontend/hooks/useClerkToken.ts)
- [MIGRATION_PLAN.md](file://MIGRATION_PLAN.md)
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
This document describes the authentication and authorization system for the Financial Management Service. It explains how JWT tokens are validated, how service access is enforced, and how role-based access control (RBAC) governs permissions across modules. It also covers permission validation, role hierarchies, dynamic access control, and integration with external authentication providers. Finally, it outlines security best practices, token lifecycle management, and audit trail requirements for compliance.

## Project Structure
The authentication and authorization logic is primarily implemented in the backend under app/auth, with supporting configuration and logging in app/core. The frontend integrates with Clerk for token acquisition and storage. The audit log model supports compliance and traceability.

```mermaid
graph TB
subgraph "Backend"
A["app/auth/middleware.py"]
B["app/auth/permissions.py"]
C["app/auth/roles.py"]
D["app/auth/__init__.py"]
E["app/core/config.py"]
F["app/core/logging.py"]
G["app/core/middleware.py"]
H["app/main.py"]
I["app/modules/core/models/audit_log_model.py"]
end
subgraph "Frontend"
J["frontend/hooks/useClerkToken.ts"]
end
H --> G
H --> A
D --> A
A --> E
A --> F
B --> C
I -. "compliance logging" .- A
J --> H
```

**Diagram sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L1-L140)
- [app/auth/permissions.py](file://app/auth/permissions.py#L1-L127)
- [app/auth/roles.py](file://app/auth/roles.py#L1-L119)
- [app/auth/__init__.py](file://app/auth/__init__.py#L1-L14)
- [app/core/config.py](file://app/core/config.py#L1-L74)
- [app/core/logging.py](file://app/core/logging.py#L1-L34)
- [app/core/middleware.py](file://app/core/middleware.py#L1-L35)
- [app/main.py](file://app/main.py#L1-L53)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)
- [frontend/hooks/useClerkToken.ts](file://frontend/hooks/useClerkToken.ts#L1-L23)

**Section sources**
- [app/auth/__init__.py](file://app/auth/__init__.py#L1-L14)
- [app/auth/middleware.py](file://app/auth/middleware.py#L1-L140)
- [app/auth/permissions.py](file://app/auth/permissions.py#L1-L127)
- [app/auth/roles.py](file://app/auth/roles.py#L1-L119)
- [app/core/config.py](file://app/core/config.py#L1-L74)
- [app/core/logging.py](file://app/core/logging.py#L1-L34)
- [app/core/middleware.py](file://app/core/middleware.py#L1-L35)
- [app/main.py](file://app/main.py#L1-L53)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)
- [frontend/hooks/useClerkToken.ts](file://frontend/hooks/useClerkToken.ts#L1-L23)
- [MIGRATION_PLAN.md](file://MIGRATION_PLAN.md#L1-L23)

## Core Components
- JWT validation and service access enforcement: Centralized validation against an external auth service with local fallback, plus service gating for financial_management.
- RBAC definitions: Roles and permission matrices for modules and actions, plus permission helpers for approvals and postings.
- Permission checking: Utility to evaluate whether a user’s roles and permissions satisfy a required permission.
- Configuration and logging: JWT secret handling, algorithm, expiration, and structured logging for observability.
- Audit logging: Structured audit log model capturing actor, action, object, and metadata for compliance.

**Section sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L17-L86)
- [app/auth/permissions.py](file://app/auth/permissions.py#L7-L127)
- [app/auth/roles.py](file://app/auth/roles.py#L6-L119)
- [app/core/config.py](file://app/core/config.py#L37-L51)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)

## Architecture Overview
The system enforces authentication and authorization at the API gateway via middleware. Requests must carry a valid JWT; the backend validates it either via an external auth service or locally using a configured secret. After successful validation, service access is checked, and the current user context (including roles and permissions) is extracted. Permission checks are performed per-request using RBAC matrices and helpers.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "FastAPI App"
participant AuthMW as "Auth Middleware"
participant Config as "Settings"
participant Logger as "Logger"
Client->>API : "HTTP request with Authorization : Bearer <token>"
API->>AuthMW : "verify_fm_access(credentials)"
AuthMW->>AuthMW : "validate_token(token)"
AuthMW->>Config : "read jwt_secret_key, jwt_algorithm"
AuthMW->>Logger : "log errors/warnings"
AuthMW-->>API : "validated payload or raises HTTPException"
API->>AuthMW : "get_current_user(token_payload)"
AuthMW-->>API : "user {user_id, email, roles, permissions}"
API->>AuthMW : "check_fm_permission(user, required_permission)"
AuthMW-->>API : "bool"
API-->>Client : "response or 403/401"
```

**Diagram sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L17-L138)
- [app/core/config.py](file://app/core/config.py#L37-L51)
- [app/core/logging.py](file://app/core/logging.py#L1-L34)
- [app/main.py](file://app/main.py#L1-L53)

## Detailed Component Analysis

### JWT Validation and Service Access
- Centralized validation: Attempts external auth service validation first; falls back to local decoding using a configured secret and algorithm.
- Service gating: Ensures the token payload includes financial_management among accessible services before allowing access.
- Error handling: Distinguishes auth service availability vs. token validity errors, logging appropriately.

```mermaid
flowchart TD
Start(["validate_token(token)"]) --> TryRemote["POST to external auth service validate"]
TryRemote --> RemoteOK{"Remote OK?"}
RemoteOK --> |Yes| ReturnRemote["Return decoded payload"]
RemoteOK --> |No| LocalCheck["jwt_secret_key present?"]
LocalCheck --> |Yes| LocalDecode["jwt.decode(token, secret, algorithm)"]
LocalCheck --> |No| Raise401["Raise 401 Token validation failed"]
LocalDecode --> ReturnLocal["Return decoded payload"]
ReturnRemote --> End(["Done"])
ReturnLocal --> End
Raise401 --> End
```

**Diagram sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L17-L56)
- [app/core/config.py](file://app/core/config.py#L37-L51)

**Section sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L17-L86)
- [app/core/config.py](file://app/core/config.py#L37-L51)
- [app/core/logging.py](file://app/core/logging.py#L1-L34)

### RBAC Role Definitions and Hierarchies
- Roles: A comprehensive set of roles scoped to financial_management and mapped to services and permissions.
- Hierarchies: Certain legacy role names map to canonical roles (e.g., finance_head to FINANCE_ADMIN).
- Permissions: Roles define baseline permissions (read, write, admin), with module-specific overrides.

```mermaid
classDiagram
class Roles {
+dict ROLES
+dict PERMISSIONS
+get_role_services(role) list
+get_role_permissions(role) list
+can_access_service(role, service) bool
+has_permission(role, permission) bool
}
class Permissions {
+dict PERMISSION_MATRIX
+has_permission(role, module, action) bool
+can_approve(role, object_type) bool
+can_post(role, object_type) bool
}
Roles <.. Permissions : "role mapping and helpers"
```

**Diagram sources**
- [app/auth/roles.py](file://app/auth/roles.py#L6-L119)
- [app/auth/permissions.py](file://app/auth/permissions.py#L7-L127)

**Section sources**
- [app/auth/roles.py](file://app/auth/roles.py#L6-L119)
- [app/auth/permissions.py](file://app/auth/permissions.py#L7-L127)

### Permission Validation and Dynamic Access Control
- Dynamic checks: At runtime, the system evaluates whether a user’s roles and permissions satisfy a required permission.
- Admin escalation: Roles or permissions containing admin grant broad privileges.
- Module-action granularity: Permission matrices define allowed actions per module, enabling fine-grained controls.

```mermaid
flowchart TD
Start(["check_fm_permission(user, required_permission)"]) --> Extract["Extract user roles and permissions"]
Extract --> AdminRole{"admin or finance_head in roles?"}
AdminRole --> |Yes| Allow["Allow"]
AdminRole --> |No| CheckPerm{"required_permission in permissions?"}
CheckPerm --> |Yes| Allow
CheckPerm --> |No| AdminPerm{"admin in permissions?"}
AdminPerm --> |Yes| Allow
AdminPerm --> |No| Deny["Deny"]
Allow --> End(["Done"])
Deny --> End
```

**Diagram sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L109-L138)

**Section sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L109-L138)

### Audit Trail and Compliance Logging
- Audit log model: Captures actor identifiers, roles, actions, object types/IDs, correlation IDs, timestamps, and optional reasons and technical metadata.
- Compliance intent: Supports financial transaction auditing, user action tracking, and regulatory requirements.

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
timestamp created_at
}
```

**Diagram sources**
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)

**Section sources**
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)

### Frontend Integration with Clerk
- Token acquisition: The frontend hook obtains a token from Clerk and stores it in localStorage for API clients.
- Migration note: The project migration targets replacing custom JWT auth with Clerk.

```mermaid
sequenceDiagram
participant FE as "Frontend"
participant Clerk as "Clerk SDK"
participant LocalStorage as "localStorage"
FE->>Clerk : "getToken()"
Clerk-->>FE : "token"
FE->>LocalStorage : "setItem('clerk_token', token)"
FE->>FE : "use token in API requests"
```

**Diagram sources**
- [frontend/hooks/useClerkToken.ts](file://frontend/hooks/useClerkToken.ts#L6-L20)
- [MIGRATION_PLAN.md](file://MIGRATION_PLAN.md#L16-L21)

**Section sources**
- [frontend/hooks/useClerkToken.ts](file://frontend/hooks/useClerkToken.ts#L1-L23)
- [MIGRATION_PLAN.md](file://MIGRATION_PLAN.md#L1-L23)

## Dependency Analysis
- External dependencies: FastAPI security (HTTPBearer), HTTP client (httpx), JWT library (jose), and logging (loguru/stdlib).
- Internal dependencies: Auth middleware depends on configuration and logging; permissions depend on roles; audit logging is decoupled and reusable.

```mermaid
graph LR
MW["auth/middleware.py"] --> CFG["core/config.py"]
MW --> LOG["core/logging.py"]
PERM["auth/permissions.py"] --> ROLE["auth/roles.py"]
AUD["modules/core/models/audit_log_model.py"] -. "compliance" .- MW
FE["frontend/hooks/useClerkToken.ts"] --> MW
```

**Diagram sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L1-L140)
- [app/auth/permissions.py](file://app/auth/permissions.py#L1-L127)
- [app/auth/roles.py](file://app/auth/roles.py#L1-L119)
- [app/core/config.py](file://app/core/config.py#L1-L74)
- [app/core/logging.py](file://app/core/logging.py#L1-L34)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)
- [frontend/hooks/useClerkToken.ts](file://frontend/hooks/useClerkToken.ts#L1-L23)

**Section sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L1-L140)
- [app/auth/permissions.py](file://app/auth/permissions.py#L1-L127)
- [app/auth/roles.py](file://app/auth/roles.py#L1-L119)
- [app/core/config.py](file://app/core/config.py#L1-L74)
- [app/core/logging.py](file://app/core/logging.py#L1-L34)
- [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L1-L43)
- [frontend/hooks/useClerkToken.ts](file://frontend/hooks/useClerkToken.ts#L1-L23)

## Performance Considerations
- Token validation latency: External auth service validation introduces network latency; consider caching validated tokens at the edge or short-lived local validation for internal routes.
- Algorithm and secret configuration: Ensure HS256 and a strong secret are used; avoid weak development defaults in production.
- Logging overhead: Structured logging is efficient; avoid excessive log volume in high-throughput scenarios.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- 401 Unauthorized: Indicates token validation failure. Check JWT secret configuration and algorithm; verify the token issuer and audience.
- 403 Forbidden: Indicates lack of financial_management service access. Confirm the token payload includes financial_management in services.
- 503 Service Unavailable: Indicates external auth service unavailability. Retry with exponential backoff and degrade gracefully if appropriate.
- Logging: Use correlation IDs to trace requests across services; inspect logs for validation errors and warnings.

**Section sources**
- [app/auth/middleware.py](file://app/auth/middleware.py#L30-L56)
- [app/auth/middleware.py](file://app/auth/middleware.py#L74-L86)
- [app/core/middleware.py](file://app/core/middleware.py#L11-L34)
- [app/core/logging.py](file://app/core/logging.py#L1-L34)

## Conclusion
The system implements a robust, layered authentication and authorization strategy: centralized JWT validation with local fallback, strict service gating, and comprehensive RBAC with hierarchical roles and dynamic permission checks. The audit log model supports compliance needs, while the frontend integration with Clerk aligns with modern SSO practices. Adopt the best practices below to maintain security and reliability.

## Appendices

### Practical Examples

- Implementing custom permissions
  - Extend the permission matrix with new module-action pairs and map them to roles.
  - Add a helper function to encapsulate domain-specific checks (e.g., can_approve, can_post).
  - Reference: [app/auth/permissions.py](file://app/auth/permissions.py#L7-L127)

- Extending role definitions
  - Add a new role to the roles registry with services and permissions.
  - Map legacy role names to canonical roles if needed.
  - Reference: [app/auth/roles.py](file://app/auth/roles.py#L6-L79)

- Integrating with external authentication providers
  - Ensure the external auth service returns a payload with services and claims.
  - Configure JWT secret and algorithm for local fallback during development.
  - Reference: [app/auth/middleware.py](file://app/auth/middleware.py#L17-L56), [app/core/config.py](file://app/core/config.py#L37-L51)

- Security best practices
  - Enforce HTTPS and secure cookies for token transport.
  - Rotate secrets regularly and restrict JWT expiration.
  - Sanitize logs to avoid exposing tokens or PII.
  - Reference: [app/core/config.py](file://app/core/config.py#L37-L51), [app/core/logging.py](file://app/core/logging.py#L1-L34)

- Token lifecycle management
  - Short-lived access tokens with refresh tokens via the external provider.
  - Invalidate tokens on logout and enforce re-authentication after sensitive actions.
  - Reference: [app/auth/middleware.py](file://app/auth/middleware.py#L17-L56)

- Audit trail requirements for compliance
  - Capture actor, role, action, object, correlation ID, timestamps, and reasons for sensitive operations.
  - Maintain retention policies aligned with SOX/GDPR requirements.
  - Reference: [app/modules/core/models/audit_log_model.py](file://app/modules/core/models/audit_log_model.py#L9-L43)