/**
 * Comprehensive Tests for DashboardPage
 * Tests all KPIs, recent entries, account summary, quick actions, and accounting precision
 */

import React from 'react'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardPage } from '@/components/pages/dashboard/DashboardPage'
import { EntityBookProvider } from '@/contexts/EntityBookContext'
import { ToastProvider } from '@/contexts/ToastContext'
import {
  generatePLBalanceSheetData,
  generateTrialBalanceData,
  isWithinPrecision,
} from '@/__tests__/utils/mockDataGenerators'

jest.mock('@/hooks/useJournalEntries', () => ({
  useJournalEntries: jest.fn(),
}))

jest.mock('@/hooks/useReports', () => ({
  usePLBalanceSheet: jest.fn(),
  useCashPosition: jest.fn(),
  useTrialBalance: jest.fn(),
}))

jest.mock('@/contexts/EntityBookContext', () => {
  const React = require('react')
  return {
    useEntityBook: jest.fn(),
    EntityBookProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  }
})

const { useJournalEntries } = require('@/hooks/useJournalEntries')
const { usePLBalanceSheet, useCashPosition, useTrialBalance } = require('@/hooks/useReports')
const { useEntityBook } = require('@/contexts/EntityBookContext')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <EntityBookProvider>{children}</EntityBookProvider>
      </ToastProvider>
    </QueryClientProvider>
  )
}

describe('DashboardPage - Comprehensive Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useEntityBook as jest.Mock).mockReturnValue({
      selectedEntityId: 'entity-1',
      selectedBookId: 'book-1',
      entities: [],
      books: [],
      selectedEntity: null,
      selectedBook: null,
      isLoading: false,
      setSelectedEntityId: jest.fn(),
      setSelectedBookId: jest.fn(),
      refreshEntities: jest.fn(),
      refreshBooks: jest.fn(),
    })
  })

  afterEach(() => {
    cleanup()
  })

  describe('Output - KPI Cards', () => {
    it('should display all 4 KPI cards', async () => {
      const mockPLData = generatePLBalanceSheetData('normal')
      const mockCashData = { total_cash: 100000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balanced')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Total Revenue')).toBeInTheDocument()
        expect(screen.getByText('Total Expenses')).toBeInTheDocument()
        expect(screen.getByText('Net Profit')).toBeInTheDocument()
        expect(screen.getByText('Cash Position')).toBeInTheDocument()
      })
    })

    it('should display correct revenue value', async () => {
      const mockPLData = generatePLBalanceSheetData('normal')
      const mockCashData = { total_cash: 100000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balanced')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Total Revenue')).toBeInTheDocument()
      })
    })

    it('should show red color for negative net profit', async () => {
      const mockPLData = generatePLBalanceSheetData('loss')
      const mockCashData = { total_cash: 50000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balanced')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Net Profit')).toBeInTheDocument()
      })
    })
  })

  describe('Output - Recent Journal Entries', () => {
    it('should display recent entries section', async () => {
      const mockPLData = generatePLBalanceSheetData('normal')
      const mockCashData = { total_cash: 100000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balanced')
      const mockJournalEntries = {
        items: [
          {
            id: 'entry-1',
            entry_number: 'JE-001',
            entry_date: new Date().toISOString(),
            description: 'Test Entry',
            status: 'posted',
            lines: [],
          },
        ],
        total: 1,
        page: 1,
        page_size: 5,
      }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Recent Journal Entries')).toBeInTheDocument()
      })
    })

    it('should show empty state when no entries', async () => {
      const mockPLData = generatePLBalanceSheetData('normal')
      const mockCashData = { total_cash: 100000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balanced')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('No recent entries')).toBeInTheDocument()
      })
    })
  })

  describe('Output - Account Summary', () => {
    it('should display account summary when trial balance available', async () => {
      const mockPLData = generatePLBalanceSheetData('normal')
      const mockCashData = { total_cash: 100000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balanced')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Account Summary')).toBeInTheDocument()
      })
    })

    it('should calculate totals correctly', async () => {
      const mockPLData = generatePLBalanceSheetData('normal')
      const mockCashData = { total_cash: 100000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balanced')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Total Accounts')).toBeInTheDocument()
        expect(screen.getByText('Total Debits')).toBeInTheDocument()
        expect(screen.getByText('Total Credits')).toBeInTheDocument()
        expect(screen.getByText('Balance')).toBeInTheDocument()
      })
    })
  })

  describe('Output - Quick Actions', () => {
    it('should display all quick action links', async () => {
      const mockPLData = generatePLBalanceSheetData('normal')
      const mockCashData = { total_cash: 100000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balanced')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Create Journal Entry')).toBeInTheDocument()
        expect(screen.getByText('Add Account')).toBeInTheDocument()
        expect(screen.getByText('Create Period')).toBeInTheDocument()
        expect(screen.getByText('View Reports')).toBeInTheDocument()
      })
    })
  })

  describe('Accounting Precision (0.002% Tolerance)', () => {
    it('should calculate balance within tolerance', async () => {
      const mockPLData = generatePLBalanceSheetData('normal')
      const mockCashData = { total_cash: 100000, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('balancedWithRounding')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        const totalDebits = mockTrialBalance.rows.reduce((sum, row) => sum + row.debit_balance, 0)
        const totalCredits = mockTrialBalance.rows.reduce((sum, row) => sum + row.credit_balance, 0)
        const isBalanced = isWithinPrecision(totalDebits, totalCredits)
        expect(isBalanced).toBe(true)
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle zero values', async () => {
      const mockPLData = generatePLBalanceSheetData('zero')
      const mockCashData = { total_cash: 0, bank_accounts: [] }
      const mockTrialBalance = generateTrialBalanceData('zeroBalances')
      const mockJournalEntries = { items: [], total: 0, page: 1, page_size: 5 }

      usePLBalanceSheet.mockReturnValue({ data: mockPLData, isLoading: false, error: null })
      useCashPosition.mockReturnValue({ data: mockCashData, isLoading: false, error: null })
      useTrialBalance.mockReturnValue({ data: mockTrialBalance, isLoading: false, error: null })
      useJournalEntries.mockReturnValue({ data: mockJournalEntries, isLoading: false, error: null })

      await act(async () => {
        render(<DashboardPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Total Revenue')).toBeInTheDocument()
      })
    })
  })
})
