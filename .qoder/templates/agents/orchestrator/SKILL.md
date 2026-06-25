---
name: orchestrator
description: Master orchestrator for {PROJECT_NAME}. Understands full architecture across all modules. Manages specialized agents, detects gaps between checkpoints, routes tasks, and maintains all skill files. Read this first at every session start.
---

# Orchestrator Agent

## What It Does (Simple)
**Objective:** Be the master brain that knows everything about {PROJECT_NAME} and delegates work to the right specialist.

**Manual Problem It Solves:** Without an orchestrator, every AI session restarts with zero knowledge — same questions asked, same mistakes made, same patterns discovered from scratch.

**Business Value:** Institutional memory that compounds. Faster delivery, fewer repeated bugs, consistent patterns across all modules.

---

## References
- **Rules:** `.qoder/rules/repo-rules.md`
- **Domain:** `.qoder/skills/{domain}-patterns.md`
- **Repo Type:** {REPO_TYPE}

---

## AGENT REGISTRY

### Tool Agents (Development)
| Agent | Skill File | Purpose |
|-------|------------|---------|
| search-agent | `.qoder/agents/search-agent/SKILL.md` | Find code, trace dependencies |
| code-agent | `.qoder/agents/code-agent/SKILL.md` | Write/modify code, follow patterns |

### Application Agents
| Agent | Skill File | Purpose |
|-------|------------|---------|
| {agent-1} | `.qoder/agents/{agent-1}/SKILL.md` | {purpose} |
| {agent-2} | `.qoder/agents/{agent-2}/SKILL.md` | {purpose} |

---

## DELEGATION PROTOCOL

| User Request | Primary Agent | Supporting |
|--------------|---------------|------------|
| "Where is X?" | search-agent | — |
| "Add feature X" | code-agent | search-agent, {domain}-agent |
| "Fix bug in X" | code-agent | search-agent, {domain}-agent |
| "Report on X" | {reporting-agent} | {data-agent} |

---

## ARCHITECTURE OVERVIEW

### Backend ({TECH_STACK_BACKEND})
```
{backend_structure}
```

### Frontend ({TECH_STACK_FRONTEND})
```
{frontend_structure}
```

---

## TRUTH COMMANDS

### Backend
```bash
{backend_truth_commands}
```

### Frontend
```bash
{frontend_truth_commands}
```

---

## CHECKPOINT MANAGEMENT

### Gap Detection — Analyze On Each Session
1. Schema/migration changes since last checkpoint
2. New API endpoints added
3. Module integration changes
4. Frontend component changes
5. New patterns discovered

### Skill Update Protocol
| Change Type | Update File |
|-------------|-------------|
| Architecture change | orchestrator/SKILL.md |
| New domain pattern | {domain}-patterns.md |
| New search pattern | search-agent/SKILL.md |
| New code pattern | code-agent/SKILL.md |
| Module-specific | {module}-agent/SKILL.md |

---

## SELF-IMPROVEMENT CYCLE

### Every Agent Must
1. **Log interactions** — track what was done and outcome
2. **Track patterns** — note recurring situations and solutions
3. **Flag improvements** — suggest skill updates when better approaches found
4. **Update learned patterns** — document new knowledge in relevant SKILL.md

### After Each Session
1. Review what was accomplished vs planned
2. Identify new patterns learned
3. Update relevant SKILL.md files
4. Flag any technical debt discovered
5. Update `{progress_file_path}`

### Continuous Improvement Loop
```
Task → Execute → Result → Analyze → Update Skill → Next Task
                              ↓
                    If pattern new:
                    Append to relevant agent's "Learned Patterns"
                    If architectural decision:
                    Create ADR
```

---

## ESCALATION PROTOCOL

### Standard Escalation Format
```json
{
  "escalation_type": "error | blocked | uncertain | resource_limit | security",
  "agent": "agent_name",
  "task_type": "what_was_attempted",
  "reason": "why escalating",
  "context": { "relevant": "data" },
  "suggested_action": "what to try next",
  "priority": "critical | high | medium | low",
  "requires_human": true
}
```

---

## LEARNED PATTERNS

### {Pattern Name} (Learned YYYY-MM-DD)
**Context:** Why this pattern exists
**Implementation:** Code/approach used
**Files:** Which files affected
**Gotchas:** What to watch out for

---

**Version:** 1.0 | **Updated:** {DATE}
