-- Drop all existing tables to start fresh
-- Run this FIRST before running base schema SQL

DROP TABLE IF EXISTS idempotency_keys CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS accounting_period CASCADE;
DROP TABLE IF EXISTS gl_account CASCADE;
DROP TABLE IF EXISTS dimension_value CASCADE;
DROP TABLE IF EXISTS dimension CASCADE;
DROP TABLE IF EXISTS book CASCADE;
DROP TABLE IF EXISTS legal_entity CASCADE;

-- Drop all enums
DROP TYPE IF EXISTS booktype CASCADE;
DROP TYPE IF EXISTS periodstatus CASCADE;
DROP TYPE IF EXISTS accounttype CASCADE;
DROP TYPE IF EXISTS journalentrystatus CASCADE;
DROP TYPE IF EXISTS invoicestatus CASCADE;
DROP TYPE IF EXISTS paymentstatus CASCADE;
DROP TYPE IF EXISTS schedulestatus CASCADE;
DROP TYPE IF EXISTS transactiontype CASCADE;
DROP TYPE IF EXISTS transfertype CASCADE;
DROP TYPE IF EXISTS reconciliationstatus CASCADE;
DROP TYPE IF EXISTS payrollrunstatus CASCADE;
DROP TYPE IF EXISTS componenttype CASCADE;
DROP TYPE IF EXISTS payfrequency CASCADE;
DROP TYPE IF EXISTS paydayrule CASCADE;
DROP TYPE IF EXISTS employeetype CASCADE;
