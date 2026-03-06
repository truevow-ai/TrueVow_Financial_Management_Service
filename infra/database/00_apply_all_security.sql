-- =====================================================
-- TrueVow Financial Management - Master Deployment Script
-- =====================================================
-- Purpose: Apply all security and integrity constraints
-- Date: 2026-03-02
-- =====================================================
--
-- DEPLOYMENT ORDER (IMPORTANT - run in this order):
-- 1. rls_policies.sql          - P0: Row-Level Security
-- 2. immutability_constraints.sql - P1: Immutability Triggers
-- 3. business_constraints.sql   - P2: Business Constraints
--
-- =====================================================

\echo '====================================================='
\echo 'TrueVow FM - Security & Integrity Deployment'
\echo '====================================================='
\echo ''

-- Run RLS Policies (P0 - CRITICAL)
\echo 'Step 1/3: Applying RLS Policies (P0 - CRITICAL)...'
\i rls_policies.sql
\echo 'RLS Policies applied successfully.'
\echo ''

-- Run Immutability Constraints (P1 - URGENT)
\echo 'Step 2/3: Applying Immutability Constraints (P1 - URGENT)...'
\i immutability_constraints.sql
\echo 'Immutability Constraints applied successfully.'
\echo ''

-- Run Business Constraints (P2 - HIGH)
\echo 'Step 3/3: Applying Business Constraints (P2 - HIGH)...'
\i business_constraints.sql
\echo 'Business Constraints applied successfully.'
\echo ''

\echo '====================================================='
\echo 'DEPLOYMENT COMPLETE'
\echo '====================================================='
\echo ''
\echo 'Verification queries:'
\echo '  SELECT COUNT(*) FROM pg_tables WHERE schemaname = '\''public'\'' AND rowsecurity = true;'
\echo '  SELECT COUNT(*) FROM pg_policies WHERE schemaname = '\''public'\'';'
\echo '  SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '\''%immutability%'\'' OR tgname LIKE '\''%validation%'\'';'
\echo ''

-- =====================================================
-- END OF MASTER DEPLOYMENT SCRIPT
-- =====================================================
