# Critical API Path Mismatch Issue

**Date:** January 26, 2026  
**Status:** 🔴 **CRITICAL - BLOCKS ALL JOURNAL ENTRY OPERATIONS**

---

## Problem

The frontend and backend use **inconsistent API paths** for journal entry operations:

- **Frontend calls:** `/api/v1/general-ledger/journal-entries/...`
- **Backend routes:** `/api/v1/books/{book_id}/journal-entries/...`

This means **ALL journal entry operations except bulk upsert will fail with 404 errors**.

---

## Current State

### Backend Routes (Correct)
- `POST /api/v1/books/{book_id}/journal-entries` - Create entry
- `GET /api/v1/books/{book_id}/journal-entries` - List entries
- `GET /api/v1/books/{book_id}/journal-entries/{entry_id}` - Get entry
- `POST /api/v1/books/{book_id}/journal-entries/{entry_id}/post` - Post entry
- `POST /api/v1/books/{book_id}/journal-entries/{entry_id}/reverse` - Reverse entry
- `POST /api/v1/books/{book_id}/journal-entries/{entry_id}/lines:bulkUpsert` - ✅ **FIXED**

### Frontend Calls (Incorrect)
- `GET /api/v1/general-ledger/journal-entries` - ❌ **404**
- `GET /api/v1/general-ledger/journal-entries/{id}` - ❌ **404**
- `POST /api/v1/general-ledger/journal-entries` - ❌ **404**
- `POST /api/v1/general-ledger/journal-entries/{id}/post` - ❌ **404**
- `POST /api/v1/general-ledger/journal-entries/{id}/reverse` - ❌ **404**
- `POST /api/v1/books/{book_id}/journal-entries/{id}/lines:bulkUpsert` - ✅ **CORRECT**

---

## Solution Options

### Option 1: Update Frontend (Recommended)
Update all frontend API calls to use `/books/{book_id}/journal-entries/...` pattern.

**Files to update:**
- `frontend/lib/api/glApi.ts` - All journal entry functions
- `frontend/hooks/useJournalEntries.ts` - Ensure `bookId` is passed

**Pros:**
- Matches backend architecture
- Consistent with other endpoints (periods, accounts)
- More RESTful (book-scoped resources)

**Cons:**
- Requires updating multiple frontend files
- Need to ensure `bookId` is available in all contexts

### Option 2: Add Backend Compatibility Layer
Create a compatibility router that maps `/general-ledger/journal-entries/...` to `/books/{book_id}/journal-entries/...`.

**Pros:**
- No frontend changes needed
- Backward compatible

**Cons:**
- Adds technical debt
- Requires extracting `book_id` from request body or query params
- Not RESTful

---

## Recommended Fix

**Update frontend to use `/books/{book_id}/journal-entries/...` pattern.**

The frontend already has `selectedBookId` available from `useEntityBook()` context, so this is feasible.

---

## Files Requiring Updates

1. `frontend/lib/api/glApi.ts`:
   - `getJournalEntries()` - Add `bookId` parameter
   - `getJournalEntry()` - Add `bookId` parameter  
   - `createJournalEntry()` - Already has `book_id` in data, but URL needs update
   - `postJournalEntry()` - Add `bookId` parameter
   - `reverseJournalEntry()` - Add `bookId` parameter
   - `updateJournalEntry()` - Add `bookId` parameter
   - `validateJournalEntry()` - Add `bookId` parameter

2. `frontend/hooks/useJournalEntries.ts`:
   - All hooks need to get `bookId` from `useEntityBook()` context
   - Pass `bookId` to all API calls

3. `frontend/components/pages/journal-entries/JournalEntryCreatePage.tsx`:
   - Already uses `selectedBookId` - just needs API calls updated

4. `frontend/components/pages/journal-entries/JournalEntryListPage.tsx`:
   - Needs to get `bookId` from context and pass to API calls

---

## Impact

**Current Impact:** Journal Entry list, create, get, post, reverse, and validate operations **will all fail with 404 errors** until this is fixed.

**After Fix:** All operations will work correctly with book-scoped routing.

---

## Priority

**P0 - CRITICAL** - Must be fixed before any journal entry operations can work.

This should be fixed **immediately** before proceeding with other features, as it blocks all journal entry functionality.

---

**Next Steps:**
1. Update `frontend/lib/api/glApi.ts` to use `/books/{book_id}/journal-entries/...` pattern
2. Update `frontend/hooks/useJournalEntries.ts` to pass `bookId` from context
3. Test all journal entry operations to ensure they work
4. Update any other components that call journal entry APIs directly
