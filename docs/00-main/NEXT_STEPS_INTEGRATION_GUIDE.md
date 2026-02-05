# Next Steps Integration Guide

**Date:** January 25, 2026  
**Status:** Implementation Guide

This document outlines the remaining integration steps for the approval workflow and UI enhancements.

---

## Completed Components

### Backend Services ✅
1. **Reconciliation Matching Service** (`app/modules/general_ledger/services/reconciliation_matching_service.py`)
   - Intelligent matching with confidence scoring
   - Supports amount, date, description, and reference matching
   - Returns top N suggestions per transaction

2. **Period Close Checklist Service** (`app/modules/general_ledger/services/period_close_checklist_service.py`)
   - Automated checklist computation
   - Validates: bank recs, RevRec, payroll, royalty, AR/AP aging
   - Supports manual override

### Frontend Utilities ✅
1. **Excel Paste Handler** (`frontend/utils/excelPasteHandler.ts`)
   - Parses tab/comma-separated data
   - Maps to grid columns
   - Shows toast notifications

2. **Undo/Redo Hook** (`frontend/hooks/useUndoRedo.ts`)
   - History stack management
   - Keyboard shortcuts (Ctrl+Z, Ctrl+Y)
   - Supports bulk operations

---

## Remaining Integration Tasks

### 1. Database Migrations

**Action:** Create Alembic migration for approval workflow fields

**Files to migrate:**
- `accounting_period`: Add `submitted_by`, `submitted_at`, `approved_by`, `approved_at`, `decision_reason`, `row_version`
- `payroll_run`: Add `submitted_by`, `submitted_at`, `rejected_by`, `rejected_at`, `decision_reason`, `row_version`
- `reconciliation_adjustment_batch`: Already has approval fields (verify)
- `royalty_calculation`: Already has approval fields (verify)
- `period_close_checklist`: New table

**Command:**
```bash
alembic revision --autogenerate -m "Add approval workflow fields"
alembic upgrade head
```

### 2. GlobalToolbar Integration

#### Journal Entry Page
**File:** `frontend/components/pages/journal-entries/JournalEntryCreatePage.tsx`

**Changes needed:**
1. Import GlobalToolbar and ApprovalStatusBanner
2. Add approval workflow hooks (useSubmitPayrollRunForApproval pattern)
3. Add toolbar above form/grid
4. Handle status-based read-only mode
5. Wire up submit/approve/reject/post handlers

**Example pattern** (from RoyaltyRunPage):
```tsx
<GlobalToolbar
  entityId={entityId}
  entityName={entityName}
  periodId={periodId}
  periodName={periodName}
  status={status}
  isPosted={status === 'POSTED'}
  canSubmit={status === 'DRAFT'}
  canApprove={status === 'PENDING_APPROVAL'}
  onSubmitApproval={handleSubmit}
  onApprove={handleApprove}
  onReject={handleReject}
  onPost={handlePost}
/>
```

#### AP Bill Page
**File:** Find AP Bill page component (may be in `frontend/components/pages/ap/` or `bills/`)

**Same pattern as Journal Entry**

### 3. Excel Paste Integration

**File:** `frontend/components/common/JournalEntryGrid.tsx`

**Changes needed:**
1. Import `excelPasteHandler` utilities
2. Add `onPaste` handler to grid container
3. Parse pasted data
4. Map to current column order
5. Update grid state via `onLinesChange`
6. Show toast notification

**Example:**
```tsx
const handlePaste = useCallback((event: ClipboardEvent) => {
  const parsed = handlePasteEvent(event, columnOrder, currentRow, currentCol)
  if (parsed) {
    const updates = mapPastedDataToGrid(parsed, columnOrder, currentRow, currentCol)
    // Apply updates to lines
    showPasteNotification(parsed.rowCount, parsed.columnCount, showToast)
  }
}, [columnOrder, currentRow, currentCol])
```

### 4. Undo/Redo Integration

**File:** `frontend/components/common/JournalEntryGrid.tsx`

**Changes needed:**
1. Import `useUndoRedo` hook
2. Initialize with current lines state
3. Call `updateCell`/`updateCells` on edits
4. Add undo/redo buttons to toolbar
5. Wire up keyboard shortcuts

**Example:**
```tsx
const { state, canUndo, canRedo, undo, redo, updateCell, updateCells } = useUndoRedo(initialLines)

// On cell edit:
updateCell(cellKey, newValue)

// On paste:
updateCells(bulkUpdates)
```

### 5. API Endpoint Path Fixes

**File:** `frontend/hooks/useApprovalWorkflows.ts`

**Issue:** Some endpoints have `{book_id}` placeholder instead of actual book_id

**Fix:** Replace `{book_id}` with actual book_id from context or props

**Example:**
```tsx
// Before:
fetch(`/api/v1/fm/books/{book_id}/payroll/runs/${runId}/submit-approval`)

// After:
fetch(`/api/v1/fm/books/${bookId}/payroll/runs/${runId}/submit-approval`)
```

---

## Testing Checklist

- [ ] Approval workflows work for all object types (payroll, reconciliation, period, royalty)
- [ ] GlobalToolbar shows correct buttons based on status and role
- [ ] Excel paste works with multi-row, multi-column data
- [ ] Undo/Redo works for cell edits and paste operations
- [ ] Period close checklist validates correctly
- [ ] Reconciliation matching suggests relevant journal entries
- [ ] All API endpoints use correct book_id values

---

## Notes

- RoyaltyRunPage already has GlobalToolbar integrated - use as reference
- PayrollRunDetailPage may need GlobalToolbar integration too
- Consider creating a shared `useApprovalWorkflow` hook that combines all approval actions
- Excel paste should respect column types (currency, date, etc.)
- Undo/Redo should clear history when loading new data

---

**END OF INTEGRATION GUIDE**
