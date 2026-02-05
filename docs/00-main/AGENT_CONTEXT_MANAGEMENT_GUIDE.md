# Agent Context Management Guide
## Checkpoint-Based Development Methodology

**Purpose:** This guide provides instructions for AI coding agents and developers to efficiently manage context, preserve progress, and minimize token usage through checkpoint-based development.

**Version:** 1.0  
**Date:** December 21, 2025

---

## 🎯 Overview

### The Problem
- Large codebases require reading many files, consuming tokens
- Context can be lost between requests
- Repeated explanations waste tokens
- Difficult to track progress across sessions

### The Solution
**Checkpoint-Based Development:**
- Create summary checkpoints after significant work
- Reference checkpoints instead of reading all files
- Maintain a single progress tracker
- Document decisions in ADRs

---

## 📋 Core Principles

### 1. **Incremental Development**
- Work on one milestone/task at a time
- Complete and checkpoint before moving to next
- Don't start new work until current is documented

### 2. **Focused File Operations**
- Only read files needed for current task
- Use `grep` and `codebase_search` for targeted queries
- Avoid reading entire large files unless necessary

### 3. **Checkpoint After Milestones**
- Create checkpoint document after each milestone
- Update progress tracker immediately
- Document key decisions in ADRs

### 4. **Reference, Don't Reread**
- Reference checkpoint summaries in future requests
- Only read specific files when actively modifying
- Use progress tracker to understand current state

---

## 📝 Checkpoint Creation Guidelines

### When to Create a Checkpoint

Create a checkpoint document when:
- ✅ A milestone is completed
- ✅ Significant feature is implemented
- ✅ Major architectural decision is made
- ✅ Before switching to a different module/feature
- ✅ At end of each coding session

**Do NOT create checkpoints:**
- ❌ For every small change
- ❌ Before work is complete
- ❌ For exploratory/research work

### Checkpoint Document Structure

Create checkpoint files with this naming: `MILESTONE_{N}_CHECKPOINT.md` or `{FEATURE}_CHECKPOINT.md`

**Required Sections:**

```markdown
# [Milestone/Feature Name] Checkpoint

**Date:** YYYY-MM-DD
**Status:** ✅ Complete | 🚧 In Progress | ⏳ Pending

---

## Summary
Brief 2-3 sentence summary of what was accomplished.

---

## What Was Built

### Category 1 ✅
- **Component Name** (`path/to/file.py`)
  - Brief description
  - Key features

### Category 2 ✅
- **Component Name** (`path/to/file.py`)
  - Brief description

---

## File Structure Created

```
app/
├── new_module/
│   ├── file1.py
│   └── file2.py
```

---

## Key Decisions (ADRs to Create)

1. **Decision Name**
   - Context: Why this decision was needed
   - Decision: What was chosen
   - Reason: Why this approach

---

## Dependencies Added

- `package==version` - Purpose

---

## Next Steps

1. Next task 1
2. Next task 2

---

## Testing Status

- ✅ Linter checks passed
- ⏳ Unit tests (to be created)
- ⏳ Integration tests (to be created)

---

## Token Efficiency Note

This checkpoint serves as context for [next milestone/feature]. 
Reference this document instead of reading all files when continuing.

**Key Context for Next Request:**
- What's complete
- What's ready to use
- What needs to be done next

---

**Last Updated:** YYYY-MM-DD
```

---

## 🔄 Progress Tracker Maintenance

### Progress Tracker Structure

Maintain a single `IMPLEMENTATION_PROGRESS.md` file with:

```markdown
## Milestone Status

### Milestone N — [Name] (Timeframe)
**Status:** ✅ Complete | 🚧 In Progress | ⏳ Pending
**Started:** YYYY-MM-DD
**Completed:** YYYY-MM-DD (if complete)

**Tasks:**
- [x] Completed task
- [ ] Pending task

**Key Files Created:**
- Category: `path/to/files`

**Decisions Made:**
- Decision 1
- Decision 2

**Checkpoint:** `MILESTONE_N_CHECKPOINT.md`
```

### When to Update

- ✅ After completing a task (mark as done)
- ✅ After creating checkpoint (link to it)
- ✅ When starting new milestone (update status)
- ✅ When blocked (add blocker note)

---

## 🏗️ Architecture Decision Records (ADRs)

### When to Create ADR

Create an ADR when:
- Making architectural choices
- Choosing between technologies
- Defining patterns/standards
- Resolving design conflicts

### ADR Format

```markdown
# ADR-001: [Decision Title]

**Status:** Proposed | Accepted | Deprecated | Superseded  
**Date:** YYYY-MM-DD  
**Deciders:** [Who made the decision]

---

## Context

The issue motivating this decision or change.

## Decision

The change that we're proposing or have agreed to implement.

## Consequences

What becomes easier or more difficult to do and any risks introduced by this change.

## Alternatives Considered

- Alternative 1: [description]
- Alternative 2: [description]
```

---

## 💡 Token Efficiency Best Practices

### 1. **Use Checkpoints First**
```
❌ BAD: Read all 50 files to understand current state
✅ GOOD: Read checkpoint document, then only specific files needed
```

### 2. **Targeted File Reads**
```
❌ BAD: read_file("app/") - reads everything
✅ GOOD: read_file("app/core/config.py") - specific file
```

### 3. **Use Search Tools**
```
❌ BAD: Read multiple files to find a function
✅ GOOD: grep("function_name") to find it, then read that file
```

### 4. **Batch Operations**
```
❌ BAD: Create file, read file, create file, read file
✅ GOOD: Create multiple related files, then verify together
```

### 5. **Update Progress Incrementally**
```
❌ BAD: Wait until end to update progress
✅ GOOD: Update progress tracker after each significant change
```

### 6. **Reference, Don't Repeat**
```
❌ BAD: Explain architecture in every request
✅ GOOD: "See MILESTONE_0_CHECKPOINT.md for architecture"
```

---

## 📚 Workflow Example

### Starting a New Milestone

1. **Read Progress Tracker**
   ```
   Read: IMPLEMENTATION_PROGRESS.md
   Understand: Current state, what's done, what's next
   ```

2. **Read Latest Checkpoint**
   ```
   Read: MILESTONE_N_CHECKPOINT.md
   Understand: What was built, decisions made, next steps
   ```

3. **Read Relevant ADRs** (if any)
   ```
   Read: docs/01-main/ADRs/ADR-XXX.md
   Understand: Architectural decisions affecting current work
   ```

4. **Start Work**
   ```
   Focus on: Only files needed for current task
   Create: New files as needed
   Update: Progress tracker as you go
   ```

5. **Create Checkpoint When Done**
   ```
   Create: MILESTONE_N+1_CHECKPOINT.md
   Update: IMPLEMENTATION_PROGRESS.md
   Document: Key decisions in ADRs if needed
   ```

### Continuing Work

1. **Reference Checkpoint**
   ```
   "Based on MILESTONE_N_CHECKPOINT.md, I need to..."
   ```

2. **Read Only What's Needed**
   ```
   Only read files you're actively modifying
   Use grep/search for finding things
   ```

3. **Update Progress**
   ```
   Update progress tracker after significant changes
   ```

---

## 🎯 Context Preservation Strategy

### For Each Request

**Before Starting:**
1. Check `IMPLEMENTATION_PROGRESS.md` for current state
2. Read latest checkpoint if starting new work
3. Check ADRs for relevant decisions

**During Work:**
1. Read only files needed for current task
2. Use search tools (grep, codebase_search) for discovery
3. Update progress tracker incrementally

**After Completing:**
1. Create/update checkpoint if milestone complete
2. Update progress tracker
3. Create ADRs for significant decisions
4. Note what's ready for next request

### Context Summary Template

At end of each request, provide:

```markdown
## Context Summary

**What Was Done:**
- Task 1: [description]
- Task 2: [description]

**Files Created/Modified:**
- `path/to/file1.py` - [purpose]
- `path/to/file2.py` - [purpose]

**Key Decisions:**
- Decision 1: [brief]
- Decision 2: [brief]

**Next Steps:**
- Next task 1
- Next task 2

**Checkpoint:** [link if created]
```

---

## ✅ Quality Checklist

Before marking work complete, ensure:

- [ ] Checkpoint document created (if milestone complete)
- [ ] Progress tracker updated
- [ ] ADRs created for significant decisions
- [ ] All files have proper structure
- [ ] No linter errors
- [ ] Code follows project patterns
- [ ] Documentation updated if needed

---

## 📖 Example: Starting Milestone 1

### Step 1: Read Context
```
1. Read IMPLEMENTATION_PROGRESS.md
   → See Milestone 0 is complete
   → See Milestone 1 is next

2. Read MILESTONE_0_CHECKPOINT.md
   → Understand what infrastructure exists
   → See what's ready to use
   → Understand next steps
```

### Step 2: Plan Work
```
Based on checkpoint:
- Core infrastructure exists ✅
- Database setup ready ✅
- Need to create: Models, CoA, Periods, Journal Entries
```

### Step 3: Start Implementation
```
1. Create models (only read base_model.py for reference)
2. Create repositories (use base_repository.py as template)
3. Create services
4. Update progress as you go
```

### Step 4: Create Checkpoint
```
When Milestone 1 complete:
1. Create MILESTONE_1_CHECKPOINT.md
2. Update IMPLEMENTATION_PROGRESS.md
3. Document decisions in ADRs
```

---

## 🚫 Common Mistakes to Avoid

### ❌ Mistake 1: Reading Everything
```
BAD: "Let me read all files to understand the codebase"
GOOD: "Let me read the checkpoint to understand current state"
```

### ❌ Mistake 2: Not Creating Checkpoints
```
BAD: Work on multiple milestones without checkpoints
GOOD: Create checkpoint after each milestone
```

### ❌ Mistake 3: Not Updating Progress
```
BAD: Work for hours, then update progress at end
GOOD: Update progress tracker after each significant change
```

### ❌ Mistake 4: Repeating Explanations
```
BAD: Explain architecture in every request
GOOD: Reference checkpoint/ADR that explains it
```

### ❌ Mistake 5: Reading Files Unnecessarily
```
BAD: Read 20 files to find one function
GOOD: Use grep to find it, then read that file
```

---

## 📊 Token Usage Comparison

### Without Checkpoints
```
Request 1: Read 50 files (50,000 tokens)
Request 2: Read 50 files again (50,000 tokens)
Request 3: Read 50 files again (50,000 tokens)
Total: 150,000 tokens
```

### With Checkpoints
```
Request 1: Read 50 files, create checkpoint (55,000 tokens)
Request 2: Read checkpoint + 5 files (8,000 tokens)
Request 3: Read checkpoint + 5 files (8,000 tokens)
Total: 71,000 tokens (53% reduction)
```

---

## 🎓 Training Checklist

For new agents/developers, ensure they:

- [ ] Understand checkpoint structure
- [ ] Know when to create checkpoints
- [ ] Can use progress tracker effectively
- [ ] Know how to create ADRs
- [ ] Understand token efficiency principles
- [ ] Can reference checkpoints instead of reading files

---

## 📞 Quick Reference

### File Locations
- **Progress Tracker:** `docs/01-main/IMPLEMENTATION_PROGRESS.md`
- **Checkpoints:** `docs/01-main/MILESTONE_{N}_CHECKPOINT.md`
- **ADRs:** `docs/01-main/ADRs/ADR-{NNN}.md`
- **This Guide:** `docs/01-main/AGENT_CONTEXT_MANAGEMENT_GUIDE.md`

### Key Commands
- **Find function:** `grep("function_name")`
- **Search codebase:** `codebase_search("query", target_directories)`
- **Read file:** `read_file("path/to/file.py")`
- **List directory:** `list_dir("path/to/dir")`

### Status Indicators
- ✅ = Complete
- 🚧 = In Progress
- ⏳ = Pending
- ❌ = Blocked

---

## 🔄 Maintenance

This guide should be:
- Updated when methodology changes
- Referenced at start of each major work session
- Shared with all agents/developers working on project
- Used as onboarding material for new team members

---

**Last Updated:** December 21, 2025  
**Maintained By:** Development Team  
**Version:** 1.0
