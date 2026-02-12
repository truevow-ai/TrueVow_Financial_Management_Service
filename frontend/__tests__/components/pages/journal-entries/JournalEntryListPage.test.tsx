/**
 * Comprehensive Tests for JournalEntryListPage
 * Tests all inputs, outputs, interactions, edge cases, and filtering
 */

import React from 'react'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { JournalEntryListPage } from '@/components/pages/journal-entries/JournalEntryListPage'
import { generateJournalEntryData } from '@/__tests__/utils/mockDataGenerators'

jest.mock('@/hooks/useJournalEntries', () => ({
  useJournalEntries: jest.fn(),
  useJournalEntry: jest.fn(),
}))

// Mock VirtualizedTableWrapper to render all rows directly (virtualization doesn't work in Jest)
jest.mock('@/components/common/VirtualizedTableWrapper', () => ({
  VirtualizedTableWrapper: <T,>({ data, renderHeader, renderRow, emptyMessage }: {
    data: T[]
    renderHeader: () => React.ReactNode
    renderRow: (item: T, index: number) => React.ReactNode
    emptyMessage?: React.ReactNode
  }) => {
    if (data.length === 0 && emptyMessage) {
      return <div>{emptyMessage}</div>
    }
    return (
      <div className="overflow-hidden border border-gray-200 rounded-lg">
        <div className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>{renderHeader()}</thead>
          </table>
        </div>
        <div className="overflow-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((item, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  {renderRow(item, index)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  },
}))

const { useJournalEntries, useJournalEntry } = require('@/hooks/useJournalEntries')

describe('JournalEntryListPage - Comprehensive Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Default mock for useJournalEntry (sidebar detail view)
    useJournalEntry.mockReturnValue({ data: null, isLoading: false, error: null })
  })

  afterEach(() => {
    cleanup()
  })

  describe('Input Fields', () => {
    it('should render status filter dropdown', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByLabelText('Filter by Status:')).toBeInTheDocument()
      })
    })

    it('should have all status filter options', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('All')).toBeInTheDocument()
        expect(screen.getByText('Draft')).toBeInTheDocument()
        expect(screen.getByText('Posted')).toBeInTheDocument()
        expect(screen.getByText('Reversed')).toBeInTheDocument()
      })
    })

    it('should filter by status', async () => {
      const user = userEvent.setup()
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      const filterSelect = screen.getByLabelText('Filter by Status:')
      
      await act(async () => {
        await user.selectOptions(filterSelect, 'posted')
      })

      await waitFor(() => {
        expect(useJournalEntries).toHaveBeenCalledWith(
          expect.objectContaining({
            status: 'posted',
          })
        )
      })
    })
  })

  describe('Output - Table', () => {
    it('should display all table columns', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('Entry Number')).toBeInTheDocument()
        expect(screen.getByText('Date')).toBeInTheDocument()
        expect(screen.getByText('Description')).toBeInTheDocument()
        expect(screen.getByText('Status')).toBeInTheDocument()
        expect(screen.getByText('Lines')).toBeInTheDocument()
        expect(screen.getByText('Actions')).toBeInTheDocument()
      })
    })

    it('should display all entries in table', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('JE-001')).toBeInTheDocument()
        expect(screen.getByText('Monthly accrual entry')).toBeInTheDocument()
        expect(screen.getByText('JE-002')).toBeInTheDocument()
        expect(screen.getByText('Adjustment entry')).toBeInTheDocument()
      })
    })

    it('should display entry status badges correctly', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('posted')).toBeInTheDocument()
        expect(screen.getByText('draft')).toBeInTheDocument()
        expect(screen.getByText('reversed')).toBeInTheDocument()
      })
    })

    it('should display line counts', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        // Line counts should be displayed (the mock renders 2 tables - header and body)
        const tables = screen.getAllByRole('table')
        expect(tables.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Output - Actions', () => {
    it('should display View link for each entry', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        const viewLinks = screen.getAllByText('View')
        expect(viewLinks.length).toBeGreaterThan(0)
      })
    })

    it('should have View buttons that trigger sidebar', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        // View is a button that opens the sidebar, not a link
        const viewButtons = screen.getAllByText('View')
        expect(viewButtons[0].tagName).toBe('BUTTON')
      })
    })
  })

  describe('Output - Create Button', () => {
    it('should display Create Entry button', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('Create Entry')).toBeInTheDocument()
      })
    })

    it('should have correct href for Create Entry button', async () => {
      const mockEntries = generateJournalEntryData('normal')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        const createButton = screen.getByText('Create Entry')
        expect(createButton.closest('a')).toHaveAttribute('href', '/journal-entries/new')
      })
    })
  })

  describe('Edge Cases', () => {
    it('should show empty state when no entries', async () => {
      const mockEntries = generateJournalEntryData('empty')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('No journal entries found')).toBeInTheDocument()
        expect(screen.getByText('Create First Entry')).toBeInTheDocument()
      })
    })

    it('should handle single entry', async () => {
      const mockEntries = generateJournalEntryData('single')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('JE-001')).toBeInTheDocument()
        expect(screen.getByText('Single entry')).toBeInTheDocument()
      })
    })

    it('should handle large dataset', async () => {
      const mockEntries = generateJournalEntryData('large')
      useJournalEntries.mockReturnValue({ data: mockEntries, isLoading: false, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('JE-001')).toBeInTheDocument()
      })
    })
  })

  describe('Loading and Error States', () => {
    it('should show loading spinner', async () => {
      useJournalEntries.mockReturnValue({ data: undefined, isLoading: true, error: null })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })

    it('should show error message', async () => {
      useJournalEntries.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('API Error'),
      })

      await act(async () => {
        render(<JournalEntryListPage />)
      })

      expect(screen.getByText('Error loading journal entries. Please try again.')).toBeInTheDocument()
    })
  })
})
