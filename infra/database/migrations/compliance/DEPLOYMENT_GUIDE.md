# DATABASE COMPLIANCE DEPLOYMENT GUIDE
## TrueVow Financial Management Service

**Audience**: DevOps, Database Administrators  
**Prerequisites**: Supabase Dashboard access, SQL Editor permissions

---

## DEPLOYMENT SEQUENCE

### ⚠️ CRITICAL: Execute in this exact order

```
Phase 1: RLS Policies          → 001_rls_policies.sql
Phase 2: Immutability          → 002_immutability_constraints.sql  
Phase 3: Business Constraints  → 003_business_constraints.sql
Phase 4: Verification          → Run integration tests
```

**DO NOT skip phases or execute out of order.**

---

## PHASE 1: RLS POLICY DEPLOYMENT (P0 - CRITICAL)

### Estimated Time: 10-15 minutes

### Steps:

1. **Open Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard/project/ififhzrbhadmtedyvzhb
   - Login with admin credentials

2. **Navigate to SQL Editor**
   - Left sidebar → "SQL Editor"
   - Click "New query"

3. **Load Phase 1 SQL**
   - Copy contents of: `database/migrations/compliance/001_rls_policies.sql`
   - Paste into SQL Editor

4. **Execute Phase 1**
   - Review SQL (ensure no destructive operations)
   - Click "Run" button
   - **Expected**: ~459 lines executed, 23 tables with RLS enabled

5. **Verify Phase 1**
   - Run verification query at bottom of script:
   ```sql
   SELECT tablename, rowsecurity 
   FROM pg_tables
   WHERE schemaname = 'public'
   AND tablename IN ('legal_entity', 'book', 'journal_entry')
   ORDER BY tablename;
   ```
   - **Expected**: All tables show `rowsecurity = true`

6. **Verify Policies Created**
   ```sql
   SELECT tablename, policyname 
   FROM pg_policies
   WHERE schemaname = 'public'
   ORDER BY tablename;
   ```
   - **Expected**: ~23 policies listed

### ✅ Phase 1 Success Criteria:
- [ ] SQL executed without errors
- [ ] All 23 tables have `rowsecurity = true`
- [ ] Policy count matches expected (23 policies)
- [ ] Verification queries return expected results

### ❌ Rollback Phase 1 (if needed):
```sql
-- Disable RLS on all tables
DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOR tbl IN 
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public' AND rowsecurity = true
  LOOP
    EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', tbl);
  END LOOP;
END $$;

-- Drop all policies
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN 
    SELECT schemaname, tablename, policyname 
    FROM pg_policies 
    WHERE schemaname = 'public'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', 
      pol.policyname, pol.schemaname, pol.tablename);
  END LOOP;
END $$;
```

---

## PHASE 2: IMMUTABILITY CONSTRAINTS (P1 - URGENT)

### Estimated Time: 10-15 minutes

### Steps:

1. **Verify Phase 1 Complete**
   - Confirm RLS policies are active
   - Do NOT proceed if Phase 1 failed

2. **Load Phase 2 SQL**
   - Open new SQL Editor tab
   - Copy contents of: `database/migrations/compliance/002_immutability_constraints.sql`
   - Paste into SQL Editor

3. **Execute Phase 2**
   - Review SQL (creates triggers and functions)
   - Click "Run"
   - **Expected**: ~403 lines executed, 6 triggers created

4. **Verify Phase 2**
   - Run verification query:
   ```sql
   SELECT event_object_table, trigger_name, event_manipulation
   FROM information_schema.triggers
   WHERE trigger_schema = 'public'
   AND trigger_name LIKE '%immutability%'
   ORDER BY event_object_table;
   ```
   - **Expected**: 6 triggers listed

5. **Verify Balance Constraint**
   ```sql
   SELECT constraint_name, check_clause
   FROM information_schema.check_constraints
   WHERE constraint_name = 'journal_entry_must_balance';
   ```
   - **Expected**: Constraint exists

### ✅ Phase 2 Success Criteria:
- [ ] SQL executed without errors
- [ ] 6 immutability triggers created
- [ ] Balance check constraint active on journal_entry
- [ ] Status transition functions created
- [ ] Verification queries return expected results

### ❌ Rollback Phase 2 (if needed):
```sql
-- Drop all immutability triggers
DROP TRIGGER IF EXISTS journal_entry_immutability ON journal_entry;
DROP TRIGGER IF EXISTS journal_line_immutability ON journal_line;
DROP TRIGGER IF EXISTS accounting_period_immutability ON accounting_period;
DROP TRIGGER IF EXISTS payroll_run_immutability ON payroll_run;
DROP TRIGGER IF EXISTS ar_payment_allocation_immutability ON ar_payment_allocation;
DROP TRIGGER IF EXISTS ap_payment_allocation_immutability ON ap_payment_allocation;

-- Drop trigger functions
DROP FUNCTION IF EXISTS prevent_posted_journal_modification();
DROP FUNCTION IF EXISTS prevent_closed_period_modification();
DROP FUNCTION IF EXISTS prevent_posted_payroll_modification();
DROP FUNCTION IF EXISTS prevent_payment_allocation_modification();
DROP FUNCTION IF EXISTS prevent_posted_journal_line_modification();

-- Remove balance constraint
ALTER TABLE journal_entry DROP CONSTRAINT IF EXISTS journal_entry_must_balance;
```

---

## PHASE 3: BUSINESS CONSTRAINTS (P2 - HIGH)

### Estimated Time: 15-20 minutes

### Steps:

1. **Verify Phases 1 & 2 Complete**
   - Confirm RLS active
   - Confirm immutability triggers active

2. **Load Phase 3 SQL**
   - Open new SQL Editor tab
   - Copy contents of: `database/migrations/compliance/003_business_constraints.sql`
   - Paste into SQL Editor

3. **Execute Phase 3**
   - Review SQL (adds unique constraints, indexes, validation)
   - Click "Run"
   - **Expected**: ~540 lines executed

4. **Verify Phase 3**
   - Check unique constraints:
   ```sql
   SELECT table_name, constraint_name
   FROM information_schema.table_constraints
   WHERE constraint_type = 'UNIQUE'
   AND table_schema = 'public'
   ORDER BY table_name;
   ```
   - **Expected**: ~15 unique constraints

5. **Verify Indexes Created**
   ```sql
   SELECT tablename, indexname
   FROM pg_indexes
   WHERE schemaname = 'public'
   AND indexname LIKE 'idx_%'
   ORDER BY tablename;
   ```
   - **Expected**: ~10 performance indexes

### ✅ Phase 3 Success Criteria:
- [ ] SQL executed without errors
- [ ] All unique constraints active
- [ ] Period overlap validation trigger active
- [ ] Currency validation active
- [ ] Performance indexes created
- [ ] Validation functions available

---

## PHASE 4: INTEGRATION TESTING

### Estimated Time: 10 minutes

### Steps:

1. **Install Test Dependencies** (if not already installed)
   ```bash
   pip install pytest pytest-asyncio asyncpg
   ```

2. **Run Compliance Tests**
   ```bash
   pytest tests/compliance/test_rls_compliance.py -v -s
   ```

3. **Review Test Results**
   - All tests should PASS
   - Review coverage reports printed to console

4. **Generate Full Compliance Report**
   ```bash
   pytest tests/compliance/test_rls_compliance.py::TestComplianceReport -v -s
   ```

### ✅ Phase 4 Success Criteria:
- [ ] All RLS policy tests pass
- [ ] All constraint tests pass
- [ ] Coverage reports show 100% compliance
- [ ] No missing policies or constraints

---

## POST-DEPLOYMENT VERIFICATION

### Application-Level Verification:

1. **Update Application Connection**
   - Ensure `DATABASE_URL` uses RLS-enforced credentials
   - Do NOT use service role for user operations

2. **Set Tenant Context in Application**
   - Before each query, set:
   ```python
   await conn.execute(
       "SET app.current_legal_entity_id = $1",
       str(tenant_id)
   )
   ```

3. **Test Tenant Isolation**
   - Create test users for 2 different tenants
   - Verify User A cannot see User B's data
   - Verify cross-tenant queries return 0 rows

4. **Test Immutability**
   - Create and POST a journal entry
   - Attempt to modify it (should fail with exception)
   - Verify only POSTED → REVERSED transition allowed

5. **Test Business Constraints**
   - Attempt to create duplicate entry numbers (should fail)
   - Attempt to create unbalanced journal entry (should fail)
   - Verify all unique constraints enforced

---

## ROLLBACK STRATEGY

### Complete Rollback (Emergency Only):

**WARNING**: This removes ALL compliance constraints. Only use in emergency.

```sql
-- 1. Drop all triggers
DO $$
DECLARE
  trig RECORD;
BEGIN
  FOR trig IN 
    SELECT trigger_name, event_object_table
    FROM information_schema.triggers
    WHERE trigger_schema = 'public'
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I CASCADE', 
      trig.trigger_name, trig.event_object_table);
  END LOOP;
END $$;

-- 2. Disable all RLS
DO $$
DECLARE
  tbl TEXT;
BEGIN
  FOR tbl IN 
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public' AND rowsecurity = true
  LOOP
    EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', tbl);
  END LOOP;
END $$;

-- 3. Drop all policies
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN 
    SELECT tablename, policyname 
    FROM pg_policies 
    WHERE schemaname = 'public'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I', 
      pol.policyname, pol.tablename);
  END LOOP;
END $$;
```

---

## TROUBLESHOOTING

### Issue: "Permission denied for table X"
**Solution**: User lacks SELECT/INSERT/UPDATE/DELETE on table. Grant permissions or use service role temporarily.

### Issue: "Policy violation" errors
**Solution**: Ensure `app.current_legal_entity_id` is set before queries. Check RLS policy logic.

### Issue: Trigger prevents valid operations
**Solution**: Review trigger logic. May need to refine status transition rules.

### Issue: Performance degradation
**Solution**: RLS policies add query overhead. Ensure indexes are created (Phase 3). Consider query optimization.

---

## SUPPORT

For deployment issues, contact:
- **Database Team**: DBA team via Slack #database-ops
- **Backend Team**: Financial service team via #fm-service

For compliance questions:
- **Compliance Officer**: compliance@truevow.ai
- **Platform Architect**: architecture@truevow.ai

---

## COMPLIANCE SIGN-OFF

After successful deployment, complete this checklist:

- [ ] Phase 1 deployed and verified
- [ ] Phase 2 deployed and verified
- [ ] Phase 3 deployed and verified
- [ ] Integration tests pass (100%)
- [ ] Application tenant isolation tested
- [ ] Immutability constraints tested
- [ ] Business constraints tested
- [ ] Performance acceptable (< 50ms overhead)
- [ ] Documentation updated
- [ ] Team trained on new constraints

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Verified By**: _____________  
**Sign-off**: _____________

---

## END OF DEPLOYMENT GUIDE
