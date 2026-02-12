---
description: 
globs: 
alwaysApply: true
---
# Agent Instructions: Architectural Decision Process

**For:** All AI Agents working on TrueVow projects  
**Purpose:** Prevent architectural mistakes by checking authoritative sources first  
**Status:** ✅ **MANDATORY PROCESS**

---

## 🚨 **CRITICAL RULE: ALWAYS CHECK PRD FIRST**

Before making ANY architectural decision, you MUST search these authoritative documents:

1. **TrueVow PRD** - Expected Path:
`C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md`
2. **System Documentation** - Expected Path:
`C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TRUEVOW_COMPLETE_SYSTEM_DOCUMENTATION.txt`
3. **Technical Documentation** - Expected Path:
`C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\[TrueVow-Complete-System-Technical-Documentation-for-Developers.md](mdc:http:/truevow-complete-system-technical-documentation-for-developers.md)`

**⚠️ These are the SINGLE SOURCE OF TRUTH. Failure to check = architectural mistake.**

---

## ✅ **EFFICIENT CHECKING METHOD**

### **❌ WRONG: Reading Entire Documents**
```python
# DON'T DO THIS - Wastes ~80,000 tokens
read_file("C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md")  # 12,000+ lines
```

### **✅ RIGHT: Search First, Read Only Relevant Sections**
```python
# Step 1: Search for your topic
grep -i "customer portal" C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md

# Step 2: If found at line 9364, read only that section
read_file("C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md", offset=9360, limit=20)
```

**Token Savings: 99.25% (600 tokens vs 80,000 tokens)**

---

## 📋 **MANDATORY WORKFLOW**

### **Before ANY Architectural Decision:**

1. **Search PRD** ✅
   ```bash
   grep -i "your-topic" docs/project-rules/TrueVow_PRD.md
   # OR use semantic search:
   codebase_search(
       query="Where should [service] be located?",
       target_directories=['C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md']
   )
   ```

2. **Read Only Relevant Section** ✅
   ```python
   # If grep found line N, read context around it
   read_file("C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md", offset=N-10, limit=30)
   ```

3. **Search System Documentation** ✅
   ```bash
   grep -i "your-topic" docs/project-rules/TRUEVOW_COMPLETE_SYSTEM_DOCUMENTATION.txt
   ```

4. **Read Only Relevant Section** ✅
   ```python
   read_file("C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md", offset=N-10, limit=30)
   ```

5. **Search Technical Documentation** ✅
   ```bash
   grep -i "your-topic" TrueVow-Complete System-Technical-Documentation-for-Developers.md
   ```

6. **Read Only Relevant Section** ✅
   ```python
   read_file("TrueVow-Complete-System-Technical-Documentation-for-Developers.md", offset=N-10, limit=30)
   ```

7. **Make Decision Based on Findings** ✅
   - Reference the PRD sections found
   - Align decision with authoritative sources
   - Document decision in ADR

---

## 🎯 **COMMON SEARCH PATTERNS**

### **Service Location Decisions:**
```bash
# Search for: "[Service Name]" + "repository" or "location"
grep -i "customer portal.*repository\|customer portal.*location" C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md
grep -i "draft.*repository\|draft.*location" C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md
grep -i "settle.*repository\|settle.*location" C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md
```

### **Architecture Pattern Decisions:**
```bash
# Search for: "[Service]" + "hub" or "spoke" or "separate"
grep -i "customer portal.*hub\|customer portal.*spoke\|customer portal.*separate" C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md
```

### **Database Strategy Decisions:**
```bash
# Search for: "[Service]" + "database" or "per-tenant" or "centralized"
grep -i "customer portal.*database\|customer portal.*per-tenant\|customer portal.*centralized" C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md
```

---

## ✅ **VALIDATION CHECKLIST**

Before implementing any architectural decision, verify:

- [ ] Searched PRD for relevant sections
- [ ] Searched system documentation for relevant sections
- [ ] Searched technical documentation for relevant sections
- [ ] Read only relevant sections (not entire documents)
- [ ] Decision aligns with PRD findings
- [ ] Decision aligns with system documentation
- [ ] Decision follows Hub-and-Spoke pattern (if applicable)
- [ ] Decision maintains microservices isolation
- [ ] Decision maintains security boundaries
- [ ] Created ADR documenting decision
- [ ] Referenced PRD sections in ADR

---

## 🚨 **RED FLAGS - STOP AND ASK USER**

If you encounter any of these, **STOP** and ask the user:

1. **Conflicting Information:**
   - PRD says one thing, but codebase shows another
   - Multiple architecture docs conflict
   - **Action:** Ask user which is correct

2. **Missing Information:**
   - Search returns no results
   - PRD doesn't mention the service
   - **Action:** Ask user for clarification

3. **Unclear Architecture:**
   - PRD mentions service but location unclear
   - Multiple possible interpretations
   - **Action:** Ask user to clarify

4. **Breaking Changes:**
   - Decision would change existing architecture
   - Decision conflicts with deployed system
   - **Action:** Ask user for approval

---

## 📊 **ARCHITECTURE PRINCIPLES (NON-NEGOTIABLE)**

### **1. Hub-and-Spoke Pattern:**
- **SaaS Admin = HUB** (orchestrates all services)
- **All other services = SPOKES** (managed by hub)
- **Customer Portal = SPOKE** (separate repository, API-only)

### **2. Microservices Isolation:**
- Each service has separate database
- Services communicate via APIs only
- No direct database cross-access

### **3. Security Boundaries:**
- **Customer Portal = API-only** (no direct database access)
- **SaaS Admin = Internal staff only**
- **Tenant App = Backend API only**

### **4. Service Locations (From PRD):**
- **Customer Portal:** `Truevow-Customer-Portal/` (separate repo)
- **SaaS Admin:** `2025-TrueVow-SaaS-Administration/` (separate repo)
- **Tenant App:** `2025-TrueVow-Tenant-Application/` (separate repo)
- **SETTLE:** Separate service (centralized DB)
- **CONNECT:** Separate service (centralized DB)
- **VERIFY:** Separate service (centralized DB)

---

## 📚 **QUICK REFERENCE**

### **Service Location Check:**
```bash
# 1. Search PRD
grep -i "[service-name]" C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md

# 2. Read relevant section (if found at line N)
read_file("docs/project-rules/TrueVow_PRD.md", offset=N-10, limit=30)

# 3. Make decision based on section
```

### **Architecture Pattern Check:**
```bash
# 1. Semantic search
codebase_search(
    query="What is the architecture pattern for [service]?",
    target_directories=['C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\']
)

# 2. Read relevant sections from results
# 3. Make decision
```

---

## 🎯 **EXAMPLE: Customer Portal Decision**

### **Correct Process:**

1. **Search PRD:**
   ```bash
   grep -i "customer portal" docs/project-rules/TrueVow_PRD.md
   # Result: Line 9364: "Customer Portal (`Truevow-Customer-Portal/`)"
   ```

2. **Read Relevant Section:**
   ```python
   read_file("C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation\TrueVow_PRD.md", offset=9360, limit=20)
   # Result: Shows Customer Portal is separate repository
   ```

3. **Make Decision:**
   - Customer Portal = Separate repository (`Truevow-Customer-Portal/`)
   - NOT integrated into Tenant App
   - API-only (no direct database access)

4. **Document Decision:**
   - Create ADR referencing PRD line 9364
   - Align with Hub-and-Spoke pattern
   - Maintain security boundaries

### **Wrong Process (What NOT to Do):**

1. ❌ Read entire PRD (12,000+ lines)
2. ❌ Make decision without checking PRD
3. ❌ Create `app/portal/` in Tenant App
4. ❌ Document incorrect architecture

---

## 📋 **WHEN TO READ ENTIRE DOCUMENTS**

**Only read entire documents when:**
- ❌ **Never for routine checks**
- ✅ Only if you need comprehensive understanding (rare)
- ✅ Only if search returns too many results (then refine search)
- ✅ Only if you're creating a new architecture document

**For routine architectural decisions:**
- ✅ **Search → Read relevant section → Make decision**
- ❌ **Never read entire documents**

---

## 🔄 **IF YOU FIND CONFLICTS**

If PRD and codebase conflict:

1. **Document the conflict:**
   - What PRD says
   - What codebase shows
   - Where the conflict is

2. **Ask the user:**
   - "I found a conflict between PRD (line X) and codebase (file Y). Which is correct?"

3. **Update accordingly:**
   - If PRD is correct: Fix codebase
   - If codebase is correct: Update PRD (with user approval)

---

## ✅ **SUCCESS CRITERIA**

You've followed the process correctly if:

- ✅ You searched PRD before making decision
- ✅ You read only relevant sections (not entire documents)
- ✅ Your decision aligns with PRD findings
- ✅ You referenced PRD sections in your documentation
- ✅ You maintained token efficiency (<1000 tokens for check)
- ✅ You followed architecture principles
- ✅ You created ADR documenting decision

---

## 📞 **QUESTIONS?**

If you're unsure about:
- Where a service should be located
- What architecture pattern to use
- Whether a decision aligns with PRD
- How to search efficiently

**Ask the user for clarification before proceeding.**

---

**Created By:** AI Assistant  
**Date:** January 19, 2025  
**Status:** ✅ **MANDATORY FOR ALL AGENTS**

---

*Always check PRD first, but use search tools efficiently. Never read entire documents for routine checks.*
