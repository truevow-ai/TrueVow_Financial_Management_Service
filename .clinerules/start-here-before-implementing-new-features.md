---
alwaysApply: true
---
📋 MANDATORY CHECKLIST (Before ANY Implementation):

  1. ✅ READ DOCUMENTATION FIRST
     • START_HERE.md
     • Main system documentation
     • Relevant category docs

  2. ✅ SEARCH EXISTING CODEBASE
     • Find similar implementations
     • Check for existing utilities
     • Verify if functionality exists

  3. ✅ REVIEW EXISTING PATTERNS
     • Study similar features
     • Check API route patterns
     • Review component patterns
     • Examine database patterns

  4. ✅ CHECK ARCHITECTURAL PATTERNS
     • Review established patterns
     • Check naming conventions
     • Verify multi-tenancy
     • Ensure security practices

  5. ✅ ASK IF UNCERTAIN
     • Never assume
     • Always verify

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚫 PROHIBITED:

  ❌ Create duplicate code when utilities exist
  ❌ Implement new auth when RBAC exists
  ❌ Create new encryption when service exists
  ❌ Build new audit logging when system exists
  ❌ Assume patterns without checking docs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ REQUIRED:

  ✅ Always check lib/ for existing utilities
  ✅ Always use existing RBAC (lib/rbac.ts)
  ✅ Always use existing encryption (lib/encryption.ts)
  ✅ Always use existing audit logging (logAuditEvent)
  ✅ Always follow naming conventions
  ✅ Always review similar implementations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 UPDATED FILES:

  ✅ rules/DEVELOPMENT_PROCESS_RULES.txt (NEW)
  ✅ START_HERE.md (updated with rule references)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 This rule is now MANDATORY for all future development work!
