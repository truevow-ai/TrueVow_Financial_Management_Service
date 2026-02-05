# Context Management Strategy

**Purpose:** Efficient token usage and context preservation across implementation requests

---

## Strategy Overview

### 1. **Checkpoint-Based Development**
- After each milestone/significant progress, create a checkpoint document
- Checkpoints summarize: what was built, key decisions, file structure
- Future requests reference checkpoints instead of reading all files

### 2. **Focused File Operations**
- Only read files needed for current task
- Use `grep` and `codebase_search` for targeted queries
- Avoid reading entire large files unless necessary

### 3. **Progress Tracking**
- `IMPLEMENTATION_PROGRESS.md` - Single source of truth for status
- Updated after each significant change
- Contains current context summary

### 4. **Architecture Decision Records (ADRs)**
- Document key architectural decisions
- Reference ADRs instead of explaining decisions repeatedly
- Located in `docs/01-main/ADRs/`

### 5. **Milestone Checkpoints**
- Each milestone has a checkpoint document
- Contains: files created, decisions made, next steps
- Example: `MILESTONE_0_CHECKPOINT.md`

---

## How to Use This Strategy

### For Each New Request:

1. **Check Progress Tracker First**
   - Read `IMPLEMENTATION_PROGRESS.md` to understand current state
   - Check latest milestone checkpoint

2. **Reference Checkpoints**
   - Instead of reading all files, reference checkpoint summaries
   - Only read specific files when needed for current task

3. **Update Progress After Changes**
   - Update `IMPLEMENTATION_PROGRESS.md` with new status
   - Create/update checkpoint if significant progress made

4. **Document Decisions**
   - Create ADR for architectural decisions
   - Reference ADR in code comments when relevant

---

## Current Context (Milestone 0)

**Status:** 🚧 In Progress  
**Checkpoint:** `MILESTONE_0_CHECKPOINT.md`  
**Key Files:**
- Core structure: `app/core/`
- API structure: `app/api/v1/`
- Shared utilities: `app/shared/`
- Docker setup: `docker-compose.yml`, `Dockerfile`

**Next:** Complete Milestone 0 tasks (migrations, seed loader, auth middleware)

---

## Token Efficiency Tips

1. **Use Summaries:** Reference checkpoint docs instead of full code
2. **Targeted Reads:** Only read files you're actively modifying
3. **Grep First:** Use grep to find specific patterns before reading files
4. **Batch Operations:** Group related file operations together
5. **Update Progress:** Keep progress tracker current to avoid re-reading

---

**Last Updated:** December 21, 2025
