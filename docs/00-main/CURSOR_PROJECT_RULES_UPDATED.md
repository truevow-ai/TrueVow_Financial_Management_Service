# CURSOR PROJECT RULES (Updated with Checkpoint Methodology)
## TrueVow Financial Management + Treasury Services

**Version:** 2.0  
**Date:** December 21, 2025  
**Last Updated:** December 21, 2025

---

## 🎯 CONTEXT CHECKPOINT METHODOLOGY (MANDATORY)

### CHECKPOINT REQUIREMENTS
1. **After Each Milestone:**
   - MUST create checkpoint document: `docs/01-main/MILESTONE_{N}_CHECKPOINT.md`
   - MUST update `docs/01-main/IMPLEMENTATION_PROGRESS.md`
   - MUST document key decisions in ADRs if architectural choices made

2. **Before Starting Work:**
   - MUST read `docs/01-main/IMPLEMENTATION_PROGRESS.md` to understand current state
   - MUST read latest checkpoint if starting new milestone/feature
   - MUST reference checkpoints instead of reading all files

3. **During Work:**
   - MUST update progress tracker incrementally (not just at end)
   - MUST use grep/codebase_search before reading files
   - MUST only read files actively being modified

4. **Context Preservation:**
   - Reference checkpoints: "Based on MILESTONE_N_CHECKPOINT.md..."
   - Don't re-explain: "See checkpoint for architecture details"
   - Update checkpoints: Keep them current as work progresses

### CHECKPOINT TEMPLATE
```markdown
# [Milestone/Feature] Checkpoint
**Date:** YYYY-MM-DD
**Status:** ✅ Complete | 🚧 In Progress

## Summary
[2-3 sentence summary]

## What Was Built
[Detailed list with file paths]

## Key Decisions
[Architectural decisions made]

## Next Steps
[What comes next]

## Token Efficiency Note
[Reference instructions for next request]
```

### TOKEN EFFICIENCY RULES
- ❌ NEVER read all files to "understand the codebase"
- ✅ ALWAYS read checkpoint first, then only specific files needed
- ❌ NEVER explain architecture repeatedly
- ✅ ALWAYS reference checkpoint/ADR that explains it
- ❌ NEVER read files unnecessarily
- ✅ ALWAYS use grep/search to find things first

---

## 🧠 CONTROLLED CONTEXT RULE (MANDATORY)

The assistant MAY use bounded session context to maintain continuity,
but MUST NOT assume undocumented project state.

### CONTEXT RULES
1. **You MAY rely on:**
   - The last 21 messages (as allowed below)
   - Architectural decisions explicitly confirmed
   - File paths, schemas, and APIs pasted earlier in this session
   - **Checkpoint documents** (`MILESTONE_*_CHECKPOINT.md`)
   - **Progress tracker** (`IMPLEMENTATION_PROGRESS.md`)
   - **ADRs** (Architecture Decision Records)

2. **You MAY NOT:**
   - Assume unseen files, configs, or environment state
   - Invent schemas, migrations, or code paths
   - Assume "standard patterns" without confirmation
   - Read all files to understand context (use checkpoints instead)

3. **If context is ambiguous:**
   - Ask a **single, specific clarification**
   - Do NOT re-ask questions already answered in this session
   - Reference checkpoint documents first

4. **If a task spans multiple steps:**
   - Summarize current assumptions before proceeding
   - Ask: "Confirm these assumptions before I continue"
   - Create checkpoint after each milestone

### CONTEXT CHECKPOINT (MANDATORY FOR MULTI-STEP TASKS)

For multi-step tasks, the assistant MUST periodically output:

```
CONTEXT CHECKPOINT
- Working module: [module name]
- Files/schemas assumed: [list]
- Confirmed constraints: [list]
- Progress: [current milestone/task]
- Next steps: [what's next]
- Checkpoint: [link if created]
```

User may reply:
- "Confirmed"
- "Change X"
- "Reset context"

### CHAIN-OF-THOUGHT POLICY
- Internal reasoning is allowed
- External responses must be concise and actionable
- Do NOT expose hidden chain-of-thought unless explicitly requested
- Reference checkpoints instead of explaining everything

---

## 🛡️ CURSOR AGENT SAFETY RULES

### FILE-DELETE POLICY
- Agent MUST ask in chat before deleting ANY file or folder
- Agent must print: "DELETE REQUEST: <file-path> - type 'yes' to proceed"
- Wait for user reply: "yes" or "no"
- If user says "no", find a non-destructive refactor
- NEVER use `rm -f`, `Remove-Item -Force`, or `shutil.rmtree` quietly
- Always confirm deletions explicitly
- **Exception:** Temporary files created in current session (document in checkpoint)

### RESTRUCTURE SAFETY PROTOCOL
Before any folder restructure:
1. Run `git add -A && git stash push -m "pre-refactor auto-stash"`
2. COPY (do NOT move) files to new location
3. Verify new files contain full content (checksum or line-count)
4. Only then delete original files
5. Run `git add -A` and commit with message describing the change
6. **Update checkpoint** to reflect new structure

### TERMINAL COMMAND POLICY (PERMANENT FIXES APPLIED)
- **AUTO-KILL RULE**: Commands MUST complete within 60 seconds or be auto-killed
- **HEALTH SCRIPT**: Run `.cursor/terminal_health.ps1` once to fix terminal hangs forever
- **CURSOR SETTINGS**: Apply `.cursor/cursor_settings.json` to prevent hangs
- **MONITORING**: Use `.cursor/auto_kill_monitor.ps1` for long commands
- **PROGRESS TRACKING**: Show progress every 10 seconds for operations >30 seconds
- **NO WORKAROUNDS**: If terminal hangs, apply health script and retry - never suggest file-only approaches
- **EXTERNAL TERMINAL**: If Cursor terminal still hangs, spawn external Windows Terminal

### CONTENT PRESERVATION
- Never restructure without backing up to Git first
- Always verify content after moves/renames
- Use copy-verify-delete pattern, not move pattern
- Preserve all existing content during refactoring
- Document changes in checkpoint

### PROGRESS REPORTING
- Report progress every 30 seconds for operations taking > 1 minute
- Show what step you're on and how many steps remain
- Never let the user wonder if you're stuck
- **Update progress tracker** after each significant change (not just at end)

### ERROR RECOVERY
- If a command fails, explain why and suggest alternatives
- Never retry failed destructive operations automatically
- Always ask before attempting a second destructive action
- Document errors and recovery in checkpoint if significant

---

## ✅ TRUTH-LOCK RULES (ZERO-TOLERANCE)

1. **NEVER claim a file is "complete" or "finished" until:**
   a. You have written **real implementation** (not pass / TODO / placeholder)
   b. You have run the project's **own unit-test** for that file and it passes
   c. You print the **exact line count** of non-comment code you just wrote
   d. **You have updated the checkpoint** if milestone complete

2. **BEFORE any refactor or folder move you MUST:**
   a. Print: "REFACTOR PLAN: I will move / delete these files: <list>"
   b. Wait for user reply "yes" or "no"
   c. If "no", stop and find a non-destructive alternative
   d. **Reference checkpoint** to understand current structure

3. **AFTER any refactor you MUST:**
   a. Print: "REFACTOR DONE: <old_path> → <new_path>"
   b. Print: "FILE COUNT CHECK: expected X files, found Y files"
   c. Print: "CONTENT CHECK: every moved file has ≥ 1 line of real code (not pass / TODO)"
   d. Run: `pwsh -File .cursor/verify.ps1` and print output
   e. **Update checkpoint** to reflect new structure

4. **When asked to "restructure folders":**
   a. Read `.cursor/hierarchy.json` (if exists)
   b. **Reference latest checkpoint** for current structure
   c. Create the exact tree listed (no extra levels, no missing folders)
   d. Populate each folder with the files named above
   e. Write / overwrite the README.md inside each folder using the exact "readme" text
   f. After creation run: `tree src /F && git add -A && git commit -m "chore: standard hierarchy"`
   g. Print the tree output so the user can verify
   h. **Update checkpoint** with new structure

5. **If you violate rules 1-4, you are **required** to:**
   - Apologize and roll back via `git stash pop`
   - **Update checkpoint** to document the issue and resolution

---

## 🏗️ TRUEVOW FINANCIAL MANAGEMENT PROJECT RULES

### 1. ACCOUNTING PRINCIPLES (ZERO-TOLERANCE)
- **Double-entry accounting:** Every posted transaction MUST be balanced (debits == credits)
- **Immutable postings:** Posted journal entries CANNOT be edited (only reversed)
- **Multi-entity + multi-book:** ACCRUAL and CASH books are first-class, no "toggle" hacks
- **Idempotency:** All write operations MUST support Idempotency-Key
- **Dimensions required:** All journal lines MUST include required dimensions
- **Treasury-driven cash:** CASH book driven by Treasury movements, not Billing events

### 2. ARCHITECTURE BOUNDARIES
- **Two microservices:** Treasury Service + FM Service (separate repos/services)
- **Database isolation:** Separate databases, no direct cross-access
- **Security-first:** Finance-only access, encrypted communications
- **Async-first:** All database operations use async SQLAlchemy
- **Repository pattern:** Consistent data access layer

### 3. CODE STYLE & STRUCTURE
```
app/
├── modules/                    # Granular, self-contained modules
│   └── {module_name}/
│       ├── pages/              # UI pages
│       ├── api/routes/         # API endpoints
│       ├── scripts/            # Business logic
│       │   ├── calculations/
│       │   ├── validators/
│       │   └── processors/
│       ├── services/           # Service layer
│       ├── models/             # Database models
│       ├── repositories/       # Data access
│       ├── schemas/            # Pydantic schemas
│       ├── assets/             # Static files
│       ├── utils/              # Module utilities
│       └── tests/              # Tests
├── core/                       # Core utilities
├── shared/                     # Shared utilities
└── main.py                     # FastAPI app
```

### 4. DEVELOPMENT WORKFLOW
1. **Read checkpoint** before starting work
2. **Update progress tracker** as you work (not just at end)
3. **Create checkpoint** after milestone completion
4. **Document decisions** in ADRs for architectural choices
5. **Reference checkpoints** instead of reading all files

### 5. TEST & DEPLOY GATES
- Unit test coverage: 80%+ target
- Integration tests for all API endpoints
- All postings must balance (debits == credits)
- Idempotency tests for all write operations
- Period lock tests
- **Document test status in checkpoint**

### 6. WHEN IN DOUBT
- Choose the option that maintains **double-entry accounting integrity**
- Ask: "Does this maintain immutable postings?" If unsure, ask before coding
- Reference PRD Section 0 (Non-Negotiables) for core principles
- **Check checkpoint** for similar decisions made previously

---

## 🐛 DEBUGGING PROTOCOL
When debugging complex issues:
1. STOP after 3 failed attempts
2. Build MINIMAL test case (isolate the problem)
3. Test components in ISOLATION
4. Use systematic elimination (not trial-and-error)
5. Think: "How would a senior dev approach this?"
6. Build parallel minimal version to prove concept
7. If minimal works but full fails → bug is in complexity
8. **Document debugging process in checkpoint** if significant

---

## 🧱 INCREMENTAL DEVELOPMENT (LEGO-STYLE)
When building NEW complex systems:
1. Build SMALLEST working component first (200-300 lines max)
2. Test thoroughly until 100% working with all tests passing
3. **Create checkpoint** after component is complete
4. ONLY THEN add next component (another 200-300 lines)
5. Test new component in isolation + integration
6. **Update checkpoint** after each component
7. Repeat until complete system built
8. NEVER build entire 6,000-line system at once
9. Each "brick" must be solid before adding next brick
10. Week 1 = Minimal working system (even if basic)
11. Week 2-N = Add features incrementally
12. Result: Always have working system, easier debugging
13. Build parallel minimal version to prove concept
14. If minimal works but full fails → bug is in complexity

---

## 📋 CHECKPOINT INTEGRATION CHECKLIST

Before marking work complete:
- [ ] Checkpoint document created (if milestone complete)
- [ ] Progress tracker updated
- [ ] ADRs created for significant decisions
- [ ] All files have proper structure
- [ ] No linter errors
- [ ] Code follows project patterns
- [ ] Tests written and passing (if applicable)
- [ ] Documentation updated if needed

---

## 🔗 KEY DOCUMENT REFERENCES

- **Quick Start:** `docs/01-main/QUICK_START_FOR_AGENTS.md`
- **Complete Guide:** `docs/01-main/AGENT_CONTEXT_MANAGEMENT_GUIDE.md`
- **Progress Tracker:** `docs/01-main/IMPLEMENTATION_PROGRESS.md`
- **Checkpoints:** `docs/01-main/MILESTONE_*_CHECKPOINT.md`
- **PRD:** `docs/01-main/FM_Service_PRD.md`
- **Implementation Guide:** `docs/01-main/FM_Service_Detailed_Implementation_Guide.md`

---

## 📝 RULE UPDATES SUMMARY

### Added (Checkpoint Methodology):
- ✅ Mandatory checkpoint creation after milestones
- ✅ Progress tracker updates during work (not just at end)
- ✅ Reference checkpoints instead of reading all files
- ✅ Token efficiency rules
- ✅ ADR creation for architectural decisions

### Enhanced (Existing Rules):
- ✅ Context rules now include checkpoint references
- ✅ Context checkpoint made mandatory for multi-step tasks
- ✅ Truth-lock rules now include checkpoint updates
- ✅ Restructure protocol includes checkpoint updates
- ✅ Incremental development includes checkpoint creation

### Preserved (All Original Rules):
- ✅ File-delete policy (unchanged)
- ✅ Restructure safety protocol (enhanced)
- ✅ Terminal command policy (unchanged)
- ✅ Content preservation (unchanged)
- ✅ Progress reporting (enhanced)
- ✅ Error recovery (enhanced)
- ✅ Truth-lock rules (enhanced)
- ✅ Debugging protocol (enhanced)
- ✅ Incremental development (enhanced)

---

**Version:** 2.0  
**Last Updated:** December 21, 2025  
**Maintained By:** Development Team
