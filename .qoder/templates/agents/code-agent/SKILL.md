---
name: code-agent
description: Code writing and modification specialist for {PROJECT_NAME}. Implements features, fixes bugs, adds migrations, and updates frontend components following established repo patterns. Always uses search-agent first to confirm targets before editing.
---

# Code Agent

## What It Does (Simple)
**Objective:** Write or modify code that is correct on the first attempt by following proven repo patterns.

**Manual Problem It Solves:** AI agents that modify code without knowing established patterns create inconsistencies, break tests, and introduce bugs.

**Business Value:** Consistent code quality across all modules. Fewer review cycles. Fewer production bugs.

---

## Tasks & Objectives

| Task | Objective | Expected Result |
|------|-----------|-----------------|
| `add_endpoint` | Add new API route | Route + schema + service method |
| `add_model` | Add ORM model | Model + migration |
| `add_migration` | Create migration | Versioned migration file |
| `fix_bug` | Fix first-failure only | Passing truth command |
| `add_component` | Add frontend component | Typed component + hook |
| `add_integration` | Add external service adapter | Interface + implementation |

---

## Backend Patterns

### Module Structure (Actual — Directory Based)
```
{module}/
├── api/
│   └── routes/
│       └── {resource}_routes.py    # FastAPI router
├── models/
│   └── {resource}_model.py         # ORM model
├── repositories/
│   └── {resource}_repository.py    # DB queries
├── schemas/
│   └── {resource}_schemas.py       # Pydantic schemas
├── services/
│   └── {resource}_service.py       # Business logic
└── integrations/                   # External adapters (if applicable)
    ├── {service}_adapter.py        # Interface/base
    └── http_{service}_adapter.py   # HTTP implementation
```

### Endpoint Pattern
```python
# api/routes/{resource}_routes.py
@router.post("/{entity_id}/resource", response_model=ResourceOut)
async def create_resource(
    entity_id: uuid.UUID,
    payload: ResourceIn,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await resource_service.create(db, entity_id, payload, current_user)
```

### Service Pattern
```python
# services/{resource}_service.py
async def create(db: AsyncSession, entity_id: uuid.UUID, data: ResourceIn):
    return await resource_repository.create(db, entity_id, data.model_dump())
```

### Repository Pattern
```python
# repositories/{resource}_repository.py
async def create(db: AsyncSession, entity_id: uuid.UUID, data: dict):
    obj = ResourceModel(legal_entity_id=entity_id, **data)
    db.add(obj)
    await db.flush()
    return obj
```

### Integration Adapter Pattern
```python
# integrations/{service}_adapter.py
class {Service}Adapter(ABC):
    @abstractmethod
    async def get_{resource}(self, tenant_id: str) -> dict: ...

# integrations/http_{service}_adapter.py
class HTTP{Service}Adapter({Service}Adapter):
    async def get_{resource}(self, tenant_id: str) -> dict:
        response = await self._client.get(f"{self._base_url}/...")
        return response.json()
```

### Migration Pattern
```python
# Always include tenant isolation + RLS
op.create_table(
    "new_table",
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("legal_entity_id", sa.UUID(), nullable=False),
    ...
)
op.execute("ALTER TABLE new_table ENABLE ROW LEVEL SECURITY")
op.execute("""
    CREATE POLICY new_table_tenant_isolation ON new_table
    USING (legal_entity_id::text = current_setting('app.current_tenant', true))
""")
```

---

## Frontend Patterns

### Hook Pattern
```typescript
// hooks/use{Resource}.ts
export function use{Resource}(entityId: string) {
  const [data, setData] = useState<{Resource}[]>([]);
  const [loading, setLoading] = useState(true);
  // ...
}
```

### Component Pattern
```typescript
// components/{domain}/{Resource}List.tsx
export default function {Resource}List({ entityId }: { entityId: string }) {
  const { data, loading } = use{Resource}(entityId);
  // ...
}
```

---

## Safety Rules

1. **Search first** — never modify without confirming target via search-agent
2. **One file at a time** — sequential edits, never parallel
3. **First failure only** — fix one error per truth command run
4. **No hide-failures** — no `ignoreBuildErrors`, no skipped tests
5. **RLS on every table** — every new table needs `legal_entity_id` + RLS policy
6. **No bulk deletes** — always ask before any delete operation

---

## Documentation Updates

### After Each Feature Added
1. Confirm truth commands pass
2. Note any new patterns discovered
3. Update relevant agent SKILL.md if pattern is reusable

---

## Escalation Protocol

| Condition | Action | Priority |
|-----------|--------|----------|
| Test failure after 2 fix attempts | Escalate with full error | High |
| Migration conflict | Escalate — schema decision needed | High |
| Breaking change to shared module | Escalate — cross-module impact | High |
| External integration fails | Confirm adapter config | Medium |

---

## Learned Patterns

### Integration Adapter Pattern Separates Interface from Implementation (Learned {DATE})
**Context:** External service integrations use abstract base + HTTP implementation to enable mocking in tests
**Implementation:** Create `{service}_adapter.py` (ABC) + `http_{service}_adapter.py` (real) + `mock_{service}_adapter.py` (tests)
**Files:** `{module}/integrations/`
**Gotchas:** If you add methods to the HTTP adapter without adding to the ABC, tests using mock adapter will fail silently

---

**Version:** 1.0 | **Updated:** {DATE}
