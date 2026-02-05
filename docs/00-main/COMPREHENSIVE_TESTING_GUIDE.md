# Comprehensive Testing Guide

**Date:** January 25, 2026  
**Purpose:** Manual testing checklist for all integrated features

---

## 🧪 Testing Overview

This guide provides a systematic approach to testing all the integrated features. Test in the order listed to ensure dependencies are met.

---

## 📋 Pre-Testing Checklist

### Environment Setup
- [ ] Database migration applied (`alembic upgrade head`)
- [ ] Backend server running
- [ ] Frontend server running
- [ ] Database connection verified
- [ ] Test user accounts created (with different roles: FINANCE_USER, FINANCE_MANAGER, FINANCE_ADMIN)

### Test Data Setup
- [ ] At least one Entity created
- [ ] At least one Book created (ACCRUAL and CASH)
- [ ] At least one Accounting Period created
- [ ] GL Accounts created
- [ ] Test bank account created (for reconciliation testing)

---

## 1. Excel Paste Functionality

### Test Location
- **Page:** Journal Entry Create/Edit Page
- **Component:** JournalEntryGrid

### Test Cases

#### Test 1.1: Basic Paste from Excel
1. Open Journal Entry page
2. Create a new entry with at least 2 lines
3. Copy data from Excel (2-3 rows with: Account, Description, Debit, Credit)
4. Click on first empty row in grid
5. Paste (Ctrl+V)
6. **Expected:** Data is parsed and populated into grid columns
7. **Verify:** All columns are correctly mapped

#### Test 1.2: Paste with Tab Separators
1. Copy data with tab separators
2. Paste into grid
3. **Expected:** Data is correctly parsed

#### Test 1.3: Paste with Comma Separators
1. Copy CSV data
2. Paste into grid
3. **Expected:** Data is correctly parsed

#### Test 1.4: Paste Notification
1. Paste data
2. **Expected:** Toast notification appears confirming paste operation
3. **Verify:** Notification shows correct number of rows pasted

#### Test 1.5: Paste Validation
1. Paste invalid data (e.g., text in amount column)
2. **Expected:** Validation errors appear
3. **Verify:** Grid shows error indicators

---

## 2. Undo/Redo Functionality

### Test Location
- **Page:** Journal Entry Create/Edit Page
- **Component:** JournalEntryGrid

### Test Cases

#### Test 2.1: Basic Undo (Ctrl+Z)
1. Make a change to grid (e.g., edit a cell)
2. Press Ctrl+Z
3. **Expected:** Change is reverted
4. **Verify:** Grid state returns to previous state

#### Test 2.2: Basic Redo (Ctrl+Y)
1. After undoing, press Ctrl+Y
2. **Expected:** Change is reapplied
3. **Verify:** Grid state returns to modified state

#### Test 2.3: Multiple Undo Operations
1. Make 3-4 sequential changes
2. Press Ctrl+Z multiple times
3. **Expected:** Each undo reverts one change
4. **Verify:** History stack works correctly

#### Test 2.4: Undo After Paste
1. Paste data from Excel
2. Press Ctrl+Z
3. **Expected:** Pasted data is removed
4. **Verify:** Grid returns to state before paste

#### Test 2.5: Undo History Limit
1. Make many changes (>50)
2. Undo repeatedly
3. **Expected:** System handles large history gracefully
4. **Verify:** No performance degradation

---

## 3. GlobalToolbar Component

### Test Location
- **Page:** Journal Entry Create/Edit Page (when entryId exists)

### Test Cases

#### Test 3.1: Toolbar Visibility
1. Create a new journal entry
2. **Expected:** GlobalToolbar appears after entry is saved (entryId exists)
3. **Verify:** Toolbar shows entity/book/period selectors

#### Test 3.2: Entity/Book/Period Selection
1. Click on Entity selector
2. **Expected:** Dropdown shows available entities
3. Select different entity
4. **Expected:** Book selector updates
5. Select different book
6. **Expected:** Period selector updates

#### Test 3.3: Save Button
1. Make changes to entry
2. Click Save button in toolbar
3. **Expected:** Entry is saved
4. **Verify:** Success notification appears

#### Test 3.4: Status Display
1. View entry in different statuses (DRAFT, PENDING_APPROVAL, APPROVED, POSTED)
2. **Expected:** Status badge displays correctly
3. **Verify:** Status color matches expected state

---

## 4. ApprovalStatusBanner Component

### Test Location
- **Page:** Journal Entry Create/Edit Page

### Test Cases

#### Test 4.1: Banner Visibility
1. Create entry and submit for approval
2. **Expected:** ApprovalStatusBanner appears
3. **Verify:** Banner shows submission details

#### Test 4.2: Submission Information
1. Submit entry for approval
2. **Expected:** Banner shows:
   - Submitted by (user name)
   - Submitted at (timestamp)
   - Status badge
3. **Verify:** All information is accurate

#### Test 4.3: Approval Information
1. Approve an entry
2. **Expected:** Banner shows:
   - Approved by (user name)
   - Approved at (timestamp)
   - Decision reason (if provided)
3. **Verify:** All information is accurate

#### Test 4.4: Rejection Information
1. Reject an entry
2. **Expected:** Banner shows:
   - Rejected by (user name)
   - Rejected at (timestamp)
   - Decision reason
3. **Verify:** All information is accurate

#### Test 4.5: Posted Information
1. Post an entry
2. **Expected:** Banner shows:
   - Posted by (user name)
   - Posted at (timestamp)
3. **Verify:** All information is accurate

#### Test 4.6: Status-Specific Styling
1. View entries in different statuses
2. **Expected:** Banner styling changes based on status:
   - PENDING_APPROVAL: Yellow/amber
   - APPROVED: Green
   - REJECTED: Red
   - POSTED: Blue
3. **Verify:** Colors match expected states

---

## 5. Approval Workflows

### Test Location
- **Pages:** Journal Entry, Payroll Run, Reconciliation Adjustment, Period Close, Royalty Run

### Test Cases for Each Workflow Type

#### Test 5.1: Journal Entry Approval Workflow

##### 5.1.1: Submit for Approval
1. Create a journal entry (DRAFT status)
2. Click "Submit for Approval" in GlobalToolbar
3. **Expected:**
   - Status changes to PENDING_APPROVAL
   - ApprovalStatusBanner appears
   - Entry becomes read-only
4. **Verify:** Entry cannot be edited

##### 5.1.2: Approve Entry
1. As FINANCE_MANAGER, view pending entry
2. Click "Approve" button
3. Enter approval reason (optional)
4. **Expected:**
   - Status changes to APPROVED
   - Banner updates with approval info
   - Entry remains read-only
5. **Verify:** Approval audit log created

##### 5.1.3: Reject Entry
1. As FINANCE_MANAGER, view pending entry
2. Click "Reject" button
3. Enter rejection reason (required)
4. **Expected:**
   - Status changes to REJECTED
   - Banner updates with rejection info
   - Entry becomes editable again
5. **Verify:** Rejection audit log created

##### 5.1.4: Post Entry
1. With APPROVED entry, click "Post" button
2. **Expected:**
   - Status changes to POSTED
   - Banner updates with post info
   - Entry becomes permanently read-only
3. **Verify:** Journal lines are posted to GL

##### 5.1.5: Separation of Duties (SoD)
1. As FINANCE_USER, create and submit entry
2. Try to approve as same user
3. **Expected:** Error message (SoD violation)
4. **Verify:** Only FINANCE_MANAGER can approve

##### 5.1.6: FINANCE_ADMIN Override
1. As FINANCE_ADMIN, approve entry created by same user
2. Enter override reason
3. **Expected:** Approval succeeds with override
4. **Verify:** Override reason logged

#### Test 5.2: Payroll Run Approval Workflow
- Follow same pattern as Journal Entry (5.1.1 - 5.1.6)
- **Endpoints to test:**
  - POST `/books/{book_id}/payroll/runs/{run_id}/submit-approval`
  - POST `/books/{book_id}/payroll/runs/{run_id}/approve`
  - POST `/books/{book_id}/payroll/runs/{run_id}/reject`
  - POST `/books/{book_id}/payroll/runs/{run_id}/post`

#### Test 5.3: Reconciliation Adjustment Approval Workflow
- Follow same pattern as Journal Entry (5.1.1 - 5.1.6)
- **Endpoints to test:**
  - POST `/reconciliations/{rec_id}/adjustments/submit-approval`
  - POST `/reconciliations/{rec_id}/adjustments/approve`
  - POST `/reconciliations/{rec_id}/adjustments/reject`

#### Test 5.4: Period Close Approval Workflow
- Follow same pattern as Journal Entry (5.1.1 - 5.1.6)
- **Additional:** Test checklist validation
- **Endpoints to test:**
  - POST `/books/{book_id}/periods/{period_id}/submit-close`
  - POST `/books/{book_id}/periods/{period_id}/approve-close`

#### Test 5.5: Royalty Run Approval Workflow
- Follow same pattern as Journal Entry (5.1.1 - 5.1.6)
- **Endpoints to test:**
  - POST `/intercompany/royalties/runs/{run_id}/submit-approval`
  - POST `/intercompany/royalties/runs/{run_id}/approve`
  - POST `/intercompany/royalties/runs/{run_id}/reject`

---

## 6. Period Close Checklist

### Test Location
- **API Endpoints:** Period Close Checklist endpoints

### Test Cases

#### Test 6.1: Get Checklist
1. Call GET `/books/{book_id}/periods/{period_id}/checklist`
2. **Expected:** Returns list of checklist items
3. **Verify:** All 6 item codes present (BANK_REC_DONE, REVREC_DONE, PAYROLL_POSTED, ROYALTY_POSTED, AR_AGING_READY, AP_AGING_READY)

#### Test 6.2: Compute Checklist
1. Call POST `/books/{book_id}/periods/{period_id}/checklist/compute`
2. **Expected:** Checklist items are computed based on period state
3. **Verify:** Statuses are accurate (PENDING, COMPLETE, SKIPPED)

#### Test 6.3: Mark Item Complete
1. Call POST `/books/{book_id}/periods/{period_id}/checklist/{item_code}/complete`
2. Provide notes (optional)
3. **Expected:** Item status changes to COMPLETE
4. **Verify:** Notes are saved, computed_by and computed_at are set

#### Test 6.4: Checklist Validation on Period Close
1. Create period with incomplete checklist
2. Try to submit for close
3. **Expected:** Validation error (checklist not complete)
4. **Verify:** Error message is clear

#### Test 6.5: Checklist Auto-Computation
1. Complete all prerequisites (bank rec, payroll, etc.)
2. Compute checklist
3. **Expected:** All items show COMPLETE
4. **Verify:** Period can be submitted for close

---

## 7. Reconciliation Matching

### Test Location
- **API Endpoint:** Reconciliation Matching Suggestions

### Test Cases

#### Test 7.1: Get Matching Suggestions
1. Create reconciliation session
2. Import bank transactions
3. Call GET `/reconciliations/{session_id}/transactions/{transaction_id}/suggestions`
4. **Expected:** Returns list of suggested journal entries
5. **Verify:** Suggestions are sorted by confidence score

#### Test 7.2: Matching Criteria
1. Create journal entry with specific amount and date
2. Create bank transaction with matching amount and date
3. Get suggestions
4. **Expected:** Journal entry appears in suggestions with high confidence
5. **Verify:** Match reasons are accurate (amount match, date match, etc.)

#### Test 7.3: Multiple Suggestions
1. Create multiple journal entries with similar amounts
2. Get suggestions for a transaction
3. **Expected:** Multiple suggestions returned (up to top_n limit)
4. **Verify:** Suggestions are ranked by confidence

#### Test 7.4: No Matches
1. Create transaction with unique amount/date
2. Get suggestions
3. **Expected:** Empty list or low-confidence suggestions only
4. **Verify:** System handles gracefully

#### Test 7.5: Exclude Already Matched
1. Match a transaction to a journal entry
2. Get suggestions for another transaction
3. **Expected:** Already matched entry does not appear
4. **Verify:** No duplicate matches

---

## 8. Read-Only Mode

### Test Location
- **Page:** Journal Entry Create/Edit Page

### Test Cases

#### Test 8.1: POSTED Entry Read-Only
1. View a POSTED journal entry
2. **Expected:**
   - All form fields are disabled
   - Grid is read-only
   - Save button is disabled
   - Edit button is hidden
3. **Verify:** No modifications possible

#### Test 8.2: PENDING_APPROVAL Entry Read-Only
1. View a PENDING_APPROVAL entry
2. **Expected:**
   - All form fields are disabled
   - Grid is read-only
   - Only Approve/Reject buttons available
3. **Verify:** No modifications possible until approved/rejected

#### Test 8.3: DRAFT Entry Editable
1. View a DRAFT entry
2. **Expected:**
   - All form fields are enabled
   - Grid is editable
   - Save button is enabled
3. **Verify:** Full editing capability

---

## 9. Integration Testing

### Test Cases

#### Test 9.1: End-to-End Journal Entry Workflow
1. Create journal entry (DRAFT)
2. Add lines via Excel paste
3. Use Undo/Redo to adjust
4. Save entry
5. Submit for approval
6. Approve as manager
7. Post entry
8. **Expected:** Complete workflow succeeds
9. **Verify:** All steps work seamlessly

#### Test 9.2: Period Close with Checklist
1. Create accounting period
2. Complete all checklist items (bank rec, payroll, etc.)
3. Compute checklist
4. Submit period for close
5. Approve period close
6. **Expected:** Period closes successfully
7. **Verify:** All validations pass

#### Test 9.3: Reconciliation with Matching
1. Create reconciliation session
2. Import bank transactions
3. Get matching suggestions
4. Match transactions to journal entries
5. Create adjustment batch
6. Submit adjustment for approval
7. Approve and post
8. **Expected:** Complete reconciliation workflow
9. **Verify:** All steps work correctly

---

## 10. Error Handling

### Test Cases

#### Test 10.1: Network Errors
1. Disconnect network
2. Try to save/submit/approve
3. **Expected:** Error message displayed
4. **Verify:** User can retry after reconnection

#### Test 10.2: Validation Errors
1. Submit invalid data (e.g., unbalanced journal entry)
2. **Expected:** Validation errors displayed
3. **Verify:** Errors are clear and actionable

#### Test 10.3: Permission Errors
1. Try to approve as non-manager
2. **Expected:** Permission denied error
3. **Verify:** Error message is clear

#### Test 10.4: Concurrent Modification
1. Open same entry in two tabs
2. Edit in first tab and save
3. Edit in second tab and save
4. **Expected:** Row version conflict error
5. **Verify:** User can refresh and retry

---

## 📊 Test Results Template

Use this template to track test results:

```
Feature: [Feature Name]
Test Case: [Test ID]
Status: [PASS / FAIL / BLOCKED]
Notes: [Any issues or observations]
Screenshots: [If applicable]
```

---

## 🐛 Bug Reporting

When reporting bugs, include:
1. **Feature:** Which feature failed
2. **Test Case:** Which test case failed
3. **Steps to Reproduce:** Detailed steps
4. **Expected Behavior:** What should happen
5. **Actual Behavior:** What actually happened
6. **Screenshots/Logs:** Visual evidence
7. **Environment:** Browser, OS, user role

---

## ✅ Completion Checklist

After completing all tests:

- [ ] All Excel paste tests passed
- [ ] All Undo/Redo tests passed
- [ ] All GlobalToolbar tests passed
- [ ] All ApprovalStatusBanner tests passed
- [ ] All approval workflow tests passed (all 5 types)
- [ ] All period close checklist tests passed
- [ ] All reconciliation matching tests passed
- [ ] All read-only mode tests passed
- [ ] All integration tests passed
- [ ] All error handling tests passed
- [ ] All bugs documented and reported
- [ ] Test results documented

---

**END OF TESTING GUIDE**
