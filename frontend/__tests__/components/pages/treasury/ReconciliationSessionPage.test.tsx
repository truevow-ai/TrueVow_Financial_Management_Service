/**
 * Render + interaction tests for the reconciliation workspace.
 * Exercises the real query/mutation paths against a mocked treasuryApi.
 */
import React from 'react'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReconciliationSessionPage } from '@/components/pages/treasury/ReconciliationSessionPage'
import { treasuryApi } from '@/lib/api/treasuryApi'

jest.mock('@/lib/api/treasuryApi', () => ({
  treasuryApi: {
    getReconciliationSession: jest.fn(),
    getReconciliationMatches: jest.fn(),
    getBankTransactions: jest.fn(),
    autoMatchReconciliation: jest.fn(),
    confirmReconciliationMatch: jest.fn(),
    completeReconciliation: jest.fn(),
  },
}))

const mockedApi = treasuryApi as jest.Mocked<typeof treasuryApi>

const createWrapper = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

const session = {
  id: 'sess-1',
  bank_account_id: 'ba-1',
  period_start: '2026-01-01',
  period_end: '2026-01-31',
  statement_balance: 1000,
  book_balance: 900,
  reconciled_balance: 900,
  status: 'in_progress' as const,
  created_at: '2026-01-31T00:00:00Z',
  updated_at: '2026-01-31T00:00:00Z',
}

const matches = [
  {
    id: 'm1',
    session_id: 'sess-1',
    bank_transaction_id: 'bt-1',
    journal_entry_id: 'je-1',
    match_type: 'fuzzy' as const,
    confidence_score: 0.9,
    is_confirmed: false,
    created_at: '2026-01-31T00:00:00Z',
  },
]

const bankTxns = {
  items: [
    {
      id: 'bt-9',
      bank_account_id: 'ba-1',
      transaction_date: '2026-01-10',
      description: 'ACH deposit',
      amount: 250,
      currency: 'USD',
      transaction_type: 'credit' as const,
      balance_after: 1250,
      is_reconciled: false,
      created_at: '2026-01-10T00:00:00Z',
      updated_at: '2026-01-10T00:00:00Z',
    },
  ],
  total: 1,
}

describe('ReconciliationSessionPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedApi.getReconciliationSession.mockResolvedValue(session as any)
    mockedApi.getReconciliationMatches.mockResolvedValue(matches as any)
    mockedApi.getBankTransactions.mockResolvedValue(bankTxns as any)
    mockedApi.confirmReconciliationMatch.mockResolvedValue(matches[0] as any)
  })

  afterEach(() => cleanup())

  it('renders summary, matches and unreconciled bank transactions', async () => {
    await act(async () => {
      render(<ReconciliationSessionPage sessionId="sess-1" />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      expect(screen.getByText('Session Summary')).toBeInTheDocument()
    })
    expect(screen.getByText('Statement Balance')).toBeInTheDocument()
    // Unreconciled list is a dependent query (needs bank_account_id from the session).
    await waitFor(() => {
      expect(screen.getByText('ACH deposit')).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText('Confirm')).toBeInTheDocument()
    })
  })

  it('confirms a suggested match', async () => {
    const user = userEvent.setup()
    await act(async () => {
      render(<ReconciliationSessionPage sessionId="sess-1" />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      expect(screen.getByText('Confirm')).toBeInTheDocument()
    })

    await act(async () => {
      await user.click(screen.getByText('Confirm'))
    })

    await waitFor(() => {
      expect(mockedApi.confirmReconciliationMatch).toHaveBeenCalledWith('sess-1', 'm1')
    })
  })

  it('runs auto-match', async () => {
    mockedApi.autoMatchReconciliation.mockResolvedValue({ matched: 1, suggestions: 2 })
    const user = userEvent.setup()
    await act(async () => {
      render(<ReconciliationSessionPage sessionId="sess-1" />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      expect(screen.getByText('Auto-match')).toBeInTheDocument()
    })

    await act(async () => {
      await user.click(screen.getByText('Auto-match'))
    })

    await waitFor(() => {
      expect(mockedApi.autoMatchReconciliation).toHaveBeenCalledWith('sess-1')
    })
  })
})
