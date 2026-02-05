# Quick Start Guide for AI Agents
## Context Checkpoint Methodology

**TL;DR:** Create checkpoints after milestones, reference them instead of reading all files, update progress tracker, save tokens.

---

## 🚀 5-Minute Setup

### 1. Understand the Pattern
- **Checkpoints** = Summary documents created after significant work
- **Progress Tracker** = Single file tracking all milestone status
- **ADRs** = Architecture decision records

### 2. Before Starting Work
```
1. Read: docs/01-main/IMPLEMENTATION_PROGRESS.md
2. Read: Latest checkpoint (MILESTONE_N_CHECKPOINT.md)
3. Understand: What's done, what's next
```

### 3. During Work
```
- Only read files you're actively modifying
- Use grep/codebase_search to find things
- Update progress tracker as you go
```

### 4. After Completing Milestone
```
1. Create: MILESTONE_N_CHECKPOINT.md
2. Update: IMPLEMENTATION_PROGRESS.md
3. Create: ADRs for key decisions
```

---

## 📝 Checkpoint Template (Copy-Paste)

```markdown
# [Milestone/Feature] Checkpoint

**Date:** YYYY-MM-DD
**Status:** ✅ Complete

---

## Summary
[2-3 sentence summary]

---

## What Was Built

### Category ✅
- **Component** (`path/to/file.py`)
  - Description

---

## File Structure

```
app/
└── new_structure/
```

---

## Key Decisions

1. **Decision:** [What]
   - **Reason:** [Why]

---

## Next Steps

1. Next task
2. Next task

---

## Token Efficiency Note

Reference this checkpoint instead of reading all files.

**Last Updated:** YYYY-MM-DD
```

---

## ✅ Do's and Don'ts

### ✅ DO
- Create checkpoints after milestones
- Reference checkpoints in future requests
- Update progress tracker incrementally
- Use grep/search before reading files
- Document decisions in ADRs

### ❌ DON'T
- Read all files to understand context
- Skip checkpoint creation
- Explain architecture repeatedly
- Read files unnecessarily
- Wait until end to update progress

---

## 🎯 Example Workflow

**User:** "Continue with Milestone 1"

**Agent Should:**
1. Read `IMPLEMENTATION_PROGRESS.md` → See Milestone 0 complete, Milestone 1 next
2. Read `MILESTONE_0_CHECKPOINT.md` → Understand infrastructure
3. Start work on Milestone 1 (only read needed files)
4. Update progress as work progresses
5. Create checkpoint when complete

**NOT:**
- Read all 50 files to "understand the codebase"
- Ask user to explain what's been done
- Start from scratch

---

## 📊 Token Savings

**Without Checkpoints:**
- Every request reads 50 files = 50K tokens
- 10 requests = 500K tokens

**With Checkpoints:**
- First request: 50 files + checkpoint = 55K tokens
- Next 9 requests: checkpoint + 5 files = 9K each = 81K tokens
- Total = 136K tokens (73% savings!)

---

## 🔗 Key Files

- Progress: `docs/01-main/IMPLEMENTATION_PROGRESS.md`
- Checkpoints: `docs/01-main/MILESTONE_*_CHECKPOINT.md`
- Full Guide: `docs/01-main/AGENT_CONTEXT_MANAGEMENT_GUIDE.md`

---

**Remember:** Checkpoints are your friend. Use them!
