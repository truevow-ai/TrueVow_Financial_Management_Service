/**
 * Comprehensive Tests for useReports Hooks
 * Tests all report query hooks
 */

import React from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useTrialBalance,
  usePLBalanceSheet,
  useCashPosition,
  useCashFlow,
  useGLDetail,
} from '@/hooks/useReports'
import { reportingApi } from '@/lib/api/reportingApi'

jest.mock('@/lib/api/reportingApi')
const mockedReportingApi = reportingApi as jest.Mocked<typeof reportingApi>

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useReports Hook Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useTrialBalance', () => {
    it('should fetch trial balance', async () => {
      const mockData = { rows: [], total_debits: 0, total_credits: 0 }
      mockedReportingApi.getTrialBalance.mockResolvedValue(mockData)

      const { result } = renderHook(
        () => useTrialBalance({ legal_entity_id: 'entity-1', book_id: 'book-1' }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedReportingApi.getTrialBalance).toHaveBeenCalledWith({
        legal_entity_id: 'entity-1',
        book_id: 'book-1',
      })
    })

    it('should not fetch when entity or book is missing', () => {
      const { result } = renderHook(
        () => useTrialBalance({ legal_entity_id: '', book_id: '' }),
        { wrapper: createWrapper() }
      )

      expect(result.current.isFetching).toBe(false)
    })
  })

  describe('usePLBalanceSheet', () => {
    it('should fetch P&L balance sheet', async () => {
      const mockData = { revenue: 1000, expenses: 500, net_income: 500, assets: 2000, liabilities: 1000, equity: 1000 }
      mockedReportingApi.getPLBalanceSheet.mockResolvedValue(mockData)

      const { result } = renderHook(
        () => usePLBalanceSheet({ legal_entity_id: 'entity-1', book_id: 'book-1' }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })
    })
  })

  describe('useCashPosition', () => {
    it('should fetch cash position', async () => {
      const mockData = { total_cash: 100000, bank_accounts: [] }
      mockedReportingApi.getCashPosition.mockResolvedValue(mockData)

      const { result } = renderHook(
        () => useCashPosition({ legal_entity_id: 'entity-1', book_id: 'book-1' }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })
    })
  })

  describe('useCashFlow', () => {
    it('should fetch cash flow', async () => {
      const mockData = {
        operating_activities: 1000,
        investing_activities: -500,
        financing_activities: 200,
        net_change: 700,
        beginning_cash: 10000,
        ending_cash: 10700,
      }
      mockedReportingApi.getCashFlow.mockResolvedValue(mockData)

      const { result } = renderHook(
        () => useCashFlow({ legal_entity_id: 'entity-1', book_id: 'book-1' }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })
    })
  })

  describe('useGLDetail', () => {
    it('should fetch GL detail', async () => {
      const mockData = { rows: [], total: 0, page: 1, page_size: 10 }
      mockedReportingApi.getGLDetail.mockResolvedValue(mockData)

      const { result } = renderHook(
        () => useGLDetail({ legal_entity_id: 'entity-1', book_id: 'book-1' }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })
    })

    it('should fetch with filters', async () => {
      const mockData = { rows: [], total: 0, page: 1, page_size: 10 }
      mockedReportingApi.getGLDetail.mockResolvedValue(mockData)

      const { result } = renderHook(
        () =>
          useGLDetail({
            legal_entity_id: 'entity-1',
            book_id: 'book-1',
            account_id: 'account-1',
            search: 'test',
          }),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedReportingApi.getGLDetail).toHaveBeenCalledWith(
        expect.objectContaining({
          account_id: 'account-1',
          search: 'test',
        })
      )
    })
  })
})
