---
trigger: always_on
---

# {PROJECT_NAME} RULES
**Repo Type:** {REPO_TYPE}  (e.g. Python/FastAPI | Next.js | Monorepo)
**Date:** {DATE}

---

## 1. STATUS WORDS (ONLY THESE THREE)

| Status | Meaning |
|--------|---------|
| **DONE** | Truth commands executed, outputs captured |
| **UNVERIFIED** | Code written but not verified |
| **BLOCKED** | Specific prerequisite prevents execution (must name it) |

---

## 2. TRUTH COMMANDS FOR THIS REPO

### {TECH_STACK_BACKEND} Commands
```bash
# Migrations
{migration_command}

# Tests
{test_command}
```

### {TECH_STACK_FRONTEND} Commands
```bash
# Install
{install_command}

# Lint
{lint_command}

# Build
{build_command}
```

**Package manager rule:** {package_manager} ONLY — never mix.

---

## 3. DIRECTORY STRUCTURE

### Backend — New Code Goes Here
```
{backend_module_path}/
├── {layer_1}/     # {layer_1_description}
├── {layer_2}/     # {layer_2_description}
├── {layer_3}/     # {layer_3_description}
├── {layer_4}/     # {layer_4_description}
└── {layer_5}/     # {layer_5_description}
```

### Frontend — New Code Goes Here
```
{frontend_components_path}/   # UI components
{frontend_hooks_path}/        # Custom hooks
{frontend_lib_path}/          # API clients
{frontend_types_path}/        # TypeScript types
```

**DO NOT** create modules outside these paths.
**DO NOT** invent top-level folders.

---

## 4. SAFETY RULES

- NEVER delete files without asking: "DELETE REQUEST: {path} — type yes to proceed"
- NEVER push to git without explicit user permission
- NEVER bypass authentication globally
- NEVER skip migrations
- Always `git stash` before restructuring

---

## 5. NON-NEGOTIABLES (DOMAIN SPECIFIC)

### Security
- {security_rule_1}
- {security_rule_2}

### {DOMAIN} Invariants
- {invariant_1}
- {invariant_2}
- {invariant_3}

---

## 6. AGENT REGISTRY

| Agent | When to Use |
|-------|-------------|
| orchestrator | Start of every session |
| search-agent | Before touching any file |
| code-agent | Writing or modifying code |
| {app-agent-1} | {when_to_use} |
| {app-agent-2} | {when_to_use} |

---

## 7. DOCUMENTATION LOCATIONS

- Progress: `{progress_file_path}`
- Session cache: `{working_cache_path}`
- Checkpoints: `{checkpoints_path}`
- ADRs: `{adr_path}`

---

**End of Rules**
