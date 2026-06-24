/**
 * Render tests for JournalEntryDetailPage (drill-down target).
 * Verifies the component mounts, runs the real useQuery path against a mocked
 * glApi, and renders header + lines + balanced totals.
 */
import React from 'react'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { JournalEntryDetailPage } from '@/components/pages/journal-entries/JournalEntryDetailPage'
import { glApi } from '@/lib/api/glApi'

jest.mock('next/navigation', () => ({
  useParams: jest.fn(),
}))

jest.mock('@/contexts/EntityBookContext', () => ({
  useEntityBook: jest.fn(),
}))

jest.mock('@/lib/api/glApi', () => ({
  glApi: { getJournalEntry: jest.fn() },
}))

const { useParams } = require('next/navigation')
const { useEntityBook } = require('@/contexts/EntityBookContext')
const mockedGlApi = glApi as jest.Mocked<typeof glApi>

const createWrapper = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

const sampleEntry = {
  id: 'je-1',
  entry_number: 'JE-20260101-0001',
  legal_entity_id: 'entity-1',
  book_id: 'book-1',
  period_id: 'period-1',
  entry_date: '2026-01-15',
  description: 'Test posting',
  status: 'posted' as const,
  lines: [
    {
      id: 'line-1',
      journal_entry_id: 'je-1',
      gl_account_id: 'acc-dr',
      debit_amount: 100,
      credit_amount: 0,
      description: 'Debit side',
      line_number: 1,
    },
    {
      id: 'line-2',
      journal_entry_id: 'je-1',
      gl_account_id: 'acc-cr',
      debit_amount: 0,
      credit_amount: 100,
      description: 'Credit side',
      line_number: 2,
    },
  ],
  created_at: '2026-01-15T00:00:00Z',
  updated_at: '2026-01-15T00:00:00Z',
}

describe('JournalEntryDetailPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useParams as jest.Mock).mockReturnValue({ id: 'je-1' })
    ;(useEntityBook as jest.Mock).mockReturnValue({ selectedBookId: 'book-1' })
  })

  afterEach(() => cleanup())

  it('prompts to select a book when none is selected', async () => {
    ;(useEntityBook as jest.Mock).mockReturnValue({ selectedBookId: '' })
    await act(async () => {
      render(<JournalEntryDetailPage />, { wrapper: createWrapper() })
    })
    expect(
      screen.getByText('Select an entity and book to view this journal entry.')
    ).toBeInTheDocument()
  })

  it('fetches and renders the entry header, lines and balanced totals', async () => {
    mockedGlApi.getJournalEntry.mockResolvedValue(sampleEntry as any)

    await act(async () => {
      render(<JournalEntryDetailPage />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      expect(screen.getByText('JE-20260101-0001')).toBeInTheDocument()
    })

    expect(mockedGlApi.getJournalEntry).toHaveBeenCalledWith('book-1', 'je-1')
    expect(screen.getByText('Test posting')).toBeInTheDocument()
    expect(screen.getByText('Debit side')).toBeInTheDocument()
    expect(screen.getByText('Credit side')).toBeInTheDocument()
    // Balanced indicator
    expect(screen.getByText('Yes')).toBeInTheDocument()
  })

  it('shows an error state when the fetch fails', async () => {
    mockedGlApi.getJournalEntry.mockRejectedValue(new Error('boom'))

    await act(async () => {
      render(<JournalEntryDetailPage />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      expect(
        screen.getByText('Error loading journal entry. Please try again.')
      ).toBeInTheDocument()
    })
  })
})
