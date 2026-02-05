# AP Bill Pages Integration Guide

**Date:** January 25, 2026  
**Purpose:** Guide for integrating GlobalToolbar and approval workflows into AP Bill pages when they are created

---

## 📋 Overview

When the AP (Accounts Payable) module is implemented, the AP Bill pages should follow the same integration pattern established for the Journal Entry page. This guide provides the exact steps and code patterns to use.

---

## 🎯 Integration Checklist

When creating AP Bill pages, integrate the following:

- [ ] GlobalToolbar component
- [ ] ApprovalStatusBanner component
- [ ] Approval workflow hooks
- [ ] Read-only mode logic
- [ ] EntityBook context integration
- [ ] Excel paste handler (if using grid)
- [ ] Undo/Redo functionality (if using grid)

---

## 📝 Step-by-Step Integration

### Step 1: Import Required Components

```typescript
import { GlobalToolbar } from '@/components/common/GlobalToolbar'
import { ApprovalStatusBanner } from '@/components/common/ApprovalStatusBanner'
import { useEntityBook } from '@/contexts/EntityBookContext'
import {
  useAPBillSubmitApproval,
  useAPBillApprove,
  useAPBillReject,
  useAPBillPost
} from '@/hooks/useApprovalWorkflows'
```

### Step 2: Set Up Approval Hooks

```typescript
export function APBillCreatePage() {
  const { selectedBookId } = useEntityBook()
  const { data: bill } = useAPBill(billId) // Your existing hook
  
  // Approval workflow hooks
  const submitApproval = useAPBillSubmitApproval()
  const approve = useAPBillApprove()
  const reject = useAPBillReject()
  const post = useAPBillPost()
  
  // ... rest of component
}
```

### Step 3: Determine Read-Only State

```typescript
const entryStatus = bill?.status?.toUpperCase() || 'DRAFT'
const isReadOnly = entryStatus === 'POSTED' || entryStatus === 'PENDING_APPROVAL'
const isLocked = entryStatus === 'POSTED' // Permanent lock for posted
```

### Step 4: Add GlobalToolbar

```typescript
{billId && (
  <GlobalToolbar
    entityId={bill?.entity_id}
    bookId={selectedBookId}
    periodId={bill?.period_id}
    status={entryStatus}
    isPosted={isLocked}
    lastSavedAt={bill?.updated_at}
    onSubmitApproval={handleSubmitApproval}
    onApprove={handleApprove}
    onReject={handleReject}
    onPost={handlePost}
    onSave={handleSave}
  />
)}
```

### Step 5: Add ApprovalStatusBanner

```typescript
{entryStatus !== 'DRAFT' && (
  <ApprovalStatusBanner
    status={entryStatus}
    submittedBy={bill?.submitted_by}
    submittedAt={bill?.submitted_at}
    approvedBy={bill?.approved_by}
    approvedAt={bill?.approved_at}
    rejectedBy={bill?.rejected_by}
    rejectedAt={bill?.rejected_at}
    decisionReason={bill?.decision_reason}
    postedBy={bill?.posted_by}
    postedAt={bill?.posted_at}
  />
)}
```

### Step 6: Implement Approval Handlers

```typescript
const handleSubmitApproval = async (reason?: string) => {
  if (!billId || !selectedBookId) return
  
  try {
    await submitApproval.mutateAsync({
      billId,
      bookId: selectedBookId,
      reason
    })
    toast.success('Bill submitted for approval')
    // Invalidate queries to refresh data
  } catch (error) {
    toast.error('Failed to submit for approval')
  }
}

const handleApprove = async (reason?: string, overrideReason?: string) => {
  if (!billId || !selectedBookId) return
  
  try {
    await approve.mutateAsync({
      billId,
      bookId: selectedBookId,
      reason,
      overrideReason
    })
    toast.success('Bill approved')
  } catch (error) {
    toast.error('Failed to approve bill')
  }
}

const handleReject = async (reason: string) => {
  if (!billId || !selectedBookId) return
  
  try {
    await reject.mutateAsync({
      billId,
      bookId: selectedBookId,
      reason
    })
    toast.success('Bill rejected')
  } catch (error) {
    toast.error('Failed to reject bill')
  }
}

const handlePost = async () => {
  if (!billId || !selectedBookId) return
  
  try {
    await post.mutateAsync({
      billId,
      bookId: selectedBookId
    })
    toast.success('Bill posted')
  } catch (error) {
    toast.error('Failed to post bill')
  }
}
```

### Step 7: Apply Read-Only Mode to Form Fields

```typescript
<input
  type="text"
  value={bill?.vendor_name}
  disabled={isReadOnly}
  className={isReadOnly ? 'opacity-50 cursor-not-allowed' : ''}
/>

// For all form fields, add:
disabled={isReadOnly}
```

### Step 8: Apply Read-Only Mode to Grid (if applicable)

```typescript
{bill?.lines && (
  <APBillLineGrid
    lines={bill.lines}
    readOnly={isReadOnly}
    // ... other props
  />
)}
```

---

## 🔌 Backend Requirements

### API Endpoints Needed

The backend should provide these endpoints (following the same pattern as journal entries):

```
POST /books/{book_id}/ap/bills/{bill_id}/submit-approval
POST /books/{book_id}/ap/bills/{bill_id}/approve
POST /books/{book_id}/ap/bills/{bill_id}/reject
POST /books/{book_id}/ap/bills/{bill_id}/post
```

### Response Schema

The AP Bill response should include approval fields:

```typescript
interface APBillResponse {
  id: string
  // ... other fields
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'POSTED'
  submitted_by?: string
  submitted_at?: string
  approved_by?: string
  approved_at?: string
  rejected_by?: string
  rejected_at?: string
  decision_reason?: string
  posted_by?: string
  posted_at?: string
  row_version: number
  // ... other fields
}
```

---

## 📋 Frontend Hooks Needed

Add these hooks to `frontend/hooks/useApprovalWorkflows.ts`:

```typescript
// AP Bill Approval Hooks
export function useAPBillSubmitApproval() {
  const { selectedBookId } = useEntityBook()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ billId, reason }: { billId: string; reason?: string }) => {
      const response = await fetch(
        `/api/v1/books/${selectedBookId}/ap/bills/${billId}/submit-approval`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason })
        }
      )
      if (!response.ok) throw new Error('Failed to submit')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['ap-bills'])
    }
  })
}

// Similar hooks for approve, reject, post
```

---

## 🎨 UI Layout Pattern

Follow this layout structure:

```typescript
<div className="space-y-6">
  {/* GlobalToolbar - appears when billId exists */}
  {billId && <GlobalToolbar {...toolbarProps} />}
  
  {/* ApprovalStatusBanner - appears for non-DRAFT statuses */}
  {entryStatus !== 'DRAFT' && <ApprovalStatusBanner {...bannerProps} />}
  
  {/* Main Form */}
  <div className="card">
    <form>
      {/* Form fields with read-only logic */}
    </form>
  </div>
  
  {/* Grid (if applicable) */}
  {bill?.lines && (
    <APBillLineGrid
      lines={bill.lines}
      readOnly={isReadOnly}
    />
  )}
</div>
```

---

## ✅ Testing Checklist

When AP Bill pages are created, test:

- [ ] GlobalToolbar appears when bill is saved
- [ ] ApprovalStatusBanner appears for non-DRAFT statuses
- [ ] Submit for approval works
- [ ] Approve works (with SoD validation)
- [ ] Reject works
- [ ] Post works
- [ ] Read-only mode works for POSTED bills
- [ ] Read-only mode works for PENDING_APPROVAL bills
- [ ] Entity/Book/Period selectors work
- [ ] All approval fields display correctly
- [ ] Error handling works

---

## 📚 Reference Implementation

See the Journal Entry page implementation for a complete reference:

- `frontend/components/pages/journal-entries/JournalEntryCreatePage.tsx`

This file contains all the patterns you need to replicate for AP Bill pages.

---

## 🔗 Related Documentation

- `docs/01-main/COMPREHENSIVE_TESTING_GUIDE.md` - Testing guide
- `docs/01-main/ALL_TASKS_COMPLETE.md` - Complete integration status
- `frontend/components/common/GlobalToolbar.tsx` - Toolbar component
- `frontend/components/common/ApprovalStatusBanner.tsx` - Banner component

---

**END OF AP BILL PAGES INTEGRATION GUIDE**
