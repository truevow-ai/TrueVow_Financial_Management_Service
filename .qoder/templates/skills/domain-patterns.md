# {Domain} Patterns
**Updated:** {DATE}

---

## Architecture Overview

{PROJECT_NAME} is {brief_description_of_what_the_system_does}.

### System Role
- {role_1}
- {role_2}
- {role_3}

---

## Module Relationships

```
{module_a} ← {relationship_description}
      ↑
  {module_b}
      ↓
  {module_c}
```

---

## Core Data Patterns

### {Primary_Isolation_Pattern}
Every record belongs to a {tenant_concept}. Enforced at:
- **Application level:** all queries scoped by `{tenant_id_field}`
- **Database level:** {isolation_mechanism} on every table

```sql
-- Every table follows this pattern
CREATE TABLE {table_name} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    {tenant_id_field} UUID NOT NULL REFERENCES {tenant_table}(id),
    ...
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
-- Add isolation policy
{isolation_policy_sql}
```

### {Secondary_Core_Pattern}
{description_of_pattern}

---

## External Integration Patterns

### Adapter Pattern
External services are always wrapped in an adapter:
```
{module}/integrations/
├── {service}_adapter.py        # Abstract base (interface)
├── http_{service}_adapter.py   # Real HTTP implementation
└── mock_{service}_adapter.py   # Test mock
```

Benefits:
- Swap real service with mock in tests
- Change underlying HTTP client without touching business logic
- Clear contract for what the service must provide

### Usage-Based Billing / Third-Party APIs
When integrating usage-based external APIs:
1. Accrual at period end (estimate from prior actuals)
2. True-up on invoice receipt
3. Idempotency key on every inbound event

---

## API Patterns

### Standard Response
```json
{
  "data": { ... },
  "meta": { "total": 100, "page": 1 }
}
```

### Error Response
```json
{
  "detail": "Human-readable message",
  "code": "MACHINE_READABLE_CODE"
}
```

### Pagination
- `?page=1&page_size=50`
- Default: 50 | Max: 200

---

## Security Patterns

### Auth Flow
1. Login → {token_type} issued
2. Token in `Authorization: Bearer {token}` header
3. `{auth_dependency}` validates token on every request
4. {tenant_context} extracted from token or request path

### Forbidden Patterns
- Never bypass auth globally
- Never expose raw DB errors to API consumers
- Never skip {isolation_mechanism} on new tables
- Never log PII in plain text

---

## Testing Patterns

### Backend
```
tests/
├── unit/           # Isolated service/repo tests
├── integration/    # Real DB session tests
└── conftest.py     # Shared fixtures
```

### Frontend
```
{frontend_tests_path}/
├── components/     # Component tests
├── hooks/          # Hook tests
└── pages/          # Page integration
```

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Missing {isolation} context | Empty results, no error | Set {isolation_variable} before query |
| {domain_pitfall_1} | {symptom_1} | {fix_1} |
| {domain_pitfall_2} | {symptom_2} | {fix_2} |
| Package manager mix | Install errors | Use {package_manager} only |
| Missing {isolation} on new table | All rows blocked | Add {isolation_policy} on migration |

---

## Debugging Checklist

- [ ] Check {isolation} context is set
- [ ] Verify {core_invariant} holds
- [ ] Confirm external adapters are injected correctly (not hardcoded)
- [ ] Run `{primary_truth_command}` to reproduce
- [ ] Check logs: `logs/{relevant_log}.log`

---

**Version:** 1.0 | **Updated:** {DATE}
