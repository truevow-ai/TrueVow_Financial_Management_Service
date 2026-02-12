# Automated Tests

## Setup

Tests use Jest and React Testing Library. Dependencies are already added to `package.json`.

## Running Tests

```bash
# Install dependencies (if not already installed)
npm install

# Run all tests
npm test

# Run tests in watch mode (for development)
npm run test:watch

# Run tests with coverage report
npm run test:coverage
```

## Test Structure

### Context Tests
- `__tests__/contexts/EntityBookContext.test.tsx`
  - Tests EntityBookProvider functionality
  - Tests useEntityBook hook
  - Tests localStorage persistence
  - Tests auto-selection logic
  - Tests error handling

### Component Tests
- `__tests__/components/common/EntityBookSelector.test.tsx`
  - Tests EntityBookSelector component rendering
  - Tests dropdown interactions
  - Tests loading states
  - Tests status indicator

### API Tests
- `__tests__/lib/api/glApi.test.ts`
  - Tests entity and book API functions
  - Tests error handling

## Test Coverage

The tests cover:
- ✅ Context initialization and state management
- ✅ API integration and mocking
- ✅ localStorage persistence
- ✅ Auto-selection logic (first entity, ACCRUAL book)
- ✅ Component rendering and user interactions
- ✅ Error handling and edge cases
- ✅ Book selection reset when entity changes

## Writing New Tests

When adding new features:
1. Create test file in appropriate `__tests__` directory
2. Follow existing test patterns
3. Mock external dependencies (API, Next.js router, etc.)
4. Use React Testing Library for component tests
5. Test both happy paths and error cases
