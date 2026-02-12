# Test Expansion Plan to Reach 500+ Tests

**Current:** ~290 tests  
**Target:** 500+ tests  
**Remaining:** 210+ tests needed

---

## Expansion Strategy

### 1. Expand Existing Page Tests (100+ tests)
- Add more edge case tests to each page (10-15 per page)
- Add more interaction tests (5-10 per page)
- Add more precision tests (5 per page)
- Add more validation tests (5 per page)

### 2. Create Hook Tests (50+ tests)
- useJournalEntries.test.ts - 15 tests
- useGLAccounts.test.ts - 15 tests
- useReports.test.ts - 10 tests
- useTreasury.test.ts - 10 tests

### 3. Create API Tests (40+ tests)
- reportingApi.test.ts - 15 tests
- glApi.test.ts - Expand to 15 tests
- treasuryApi.test.ts - 10 tests

### 4. Create Utility Tests (30+ tests)
- format.test.ts - 10 tests
- calculations.test.ts - 10 tests
- validators.test.ts - 10 tests

### 5. Create Integration Tests (30+ tests)
- EntityBookContext integration - 10 tests
- Form submission flows - 10 tests
- Navigation flows - 10 tests

---

## Implementation Priority

1. **Expand existing page tests** - Highest impact
2. **Create hook tests** - Critical for coverage
3. **Create utility tests** - Foundation testing
4. **Create API tests** - Data layer testing
5. **Create integration tests** - End-to-end flows

---

**Status:** Implementing expansion systematically
