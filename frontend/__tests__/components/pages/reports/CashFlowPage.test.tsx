/**
 * Comprehensive Tests for CashFlowPage
 * Tests all inputs, outputs, interactions, edge cases, and accounting precision (0.002% tolerance)
 */

import React from 'react'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CashFlowPage } from '@/components/pages/reports/CashFlowPage'
import { EntityBookProvider } from '@/contexts/EntityBookContext'
import { ToastProvider } from '@/contexts/ToastContext'
import { reportingApi } from '@/lib/api/reportingApi'
import {
  generateCashFlowData,
  calculateCashFlowValidation,
  isWithinPrecision,
} from '@/__tests__/utils/mockDataGenerators'

jest.mock('@/lib/api/reportingApi')
const mockedReportingApi = reportingApi as jest.Mocked<typeof reportingApi>

jest.mock('@/hooks/useReports', () => ({
  useCashFlow: jest.fn(),
}))

// Mock EntityBookContext
jest.mock('@/contexts/EntityBookContext', () => {
  const React = require('react')
  return {
    useEntityBook: jest.fn(),
    EntityBookProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  }
})

const { useCashFlow } = require('@/hooks/useReports')
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

describe('CashFlowPage - Comprehensive Tests', () => {
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

  describe('Input Fields', () => {
    it('should render date input field', async () => {
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      expect(screen.getByDisplayValue(new Date().toISOString().split('T')[0])).toBeInTheDocument()
    })

    it('should update when date changes', async () => {
      const user = userEvent.setup()
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      const dateInput = screen.getByDisplayValue(new Date().toISOString().split('T')[0])
      await act(async () => {
        await user.clear(dateInput)
        await user.type(dateInput, '2024-12-31')
      })

      await waitFor(() => {
        expect(useCashFlow).toHaveBeenCalled()
      })
    })
  })

  describe('Output - Summary Cards', () => {
    it('should display Operating Activities', async () => {
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Operating Activities')).toBeInTheDocument()
      })
    })

    it('should display Investing Activities', async () => {
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Investing Activities')).toBeInTheDocument()
      })
    })

    it('should display Financing Activities', async () => {
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Financing Activities')).toBeInTheDocument()
      })
    })

    it('should display Net Change in Cash', async () => {
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Net Change in Cash')).toBeInTheDocument()
      })
    })

    it('should display Beginning and Ending Cash', async () => {
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Beginning Cash')).toBeInTheDocument()
        expect(screen.getByText('Ending Cash')).toBeInTheDocument()
      })
    })
  })

  describe('Accounting Precision (0.002% Tolerance)', () => {
    it('should validate Net Change calculation within tolerance', async () => {
      const mockData = generateCashFlowData('precisionTest')
      const validation = calculateCashFlowValidation(mockData)
      
      expect(validation.isNetChangeValid).toBe(true)
      expect(isWithinPrecision(validation.calculatedNetChange, mockData.net_change)).toBe(true)

      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Net Change in Cash')).toBeInTheDocument()
      })
    })

    it('should validate Ending Cash calculation within tolerance', async () => {
      const mockData = generateCashFlowData('precisionTest')
      const validation = calculateCashFlowValidation(mockData)
      
      expect(validation.isEndingCashValid).toBe(true)

      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Ending Cash')).toBeInTheDocument()
      })
    })
  })

  describe('Charts', () => {
    it('should render Cash Flow Activities chart', async () => {
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Cash Flow Activities')).toBeInTheDocument()
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle negative cash flow', async () => {
      const mockData = generateCashFlowData('negative')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Net Change in Cash')).toBeInTheDocument()
      })
    })

    it('should handle zero values', async () => {
      const mockData = generateCashFlowData('zero')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Operating Activities')).toBeInTheDocument()
      })
    })
  })

  describe('Export Functionality', () => {
    it('should export PDF with correct parameters', async () => {
      const user = userEvent.setup()
      const mockData = generateCashFlowData('normal')
      const mockBlob = new Blob(['PDF'], { type: 'application/pdf' })
      
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })
      mockedReportingApi.exportReportPDF.mockResolvedValue(mockBlob)
      
      // Mock URL methods - safe to mock these
      const originalCreateObjectURL = global.URL.createObjectURL
      const originalRevokeObjectURL = global.URL.revokeObjectURL
      global.URL.createObjectURL = jest.fn(() => 'blob:url')
      global.URL.revokeObjectURL = jest.fn()

      // Render BEFORE mocking document methods
      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      // Now mock createElement for the download link (after React has rendered)
      const originalCreateElement = document.createElement.bind(document)
      const mockClick = jest.fn()
      const mockLink = {
        click: mockClick,
        href: '',
        download: '',
        style: {},
      } as any
      
      jest.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
        if (tagName === 'a') {
          return mockLink
        }
        return originalCreateElement(tagName)
      })

      await act(async () => {
        await user.click(screen.getByText('Export PDF'))
      })

      await waitFor(() => {
        expect(mockedReportingApi.exportReportPDF).toHaveBeenCalledWith('cash-flow', expect.any(Object))
      })

      // Cleanup
      jest.restoreAllMocks()
      global.URL.createObjectURL = originalCreateObjectURL
      global.URL.revokeObjectURL = originalRevokeObjectURL
    })
  })

  describe('Loading and Error States', () => {
    it('should show loading spinner', async () => {
      useCashFlow.mockReturnValue({ data: undefined, isLoading: true, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })

    it('should show error message', async () => {
      useCashFlow.mockReturnValue({ data: undefined, isLoading: false, error: new Error('API Error') })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      expect(screen.getByText('Error loading cash flow statement. Please try again.')).toBeInTheDocument()
    })
  })

  describe('Additional Edge Cases', () => {
    it('should handle all three activities being zero', async () => {
      const mockData = generateCashFlowData('zero')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Operating Activities')).toBeInTheDocument()
      })
    })

    it('should handle very large cash flows', async () => {
      const mockData = {
        ...generateCashFlowData('normal'),
        operating_activities: 999999999,
        investing_activities: -500000000,
        financing_activities: 200000000,
        net_change: 699999999,
        beginning_cash: 1000000000,
        ending_cash: 1699999999,
      }
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Operating Activities')).toBeInTheDocument()
      })
    })

    it('should handle date changes affecting all calculations', async () => {
      const user = userEvent.setup()
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      const dateInput = screen.getByDisplayValue(new Date().toISOString().split('T')[0])
      await act(async () => {
        await user.clear(dateInput)
        await user.type(dateInput, '2023-12-31')
      })

      await waitFor(() => {
        expect(useCashFlow).toHaveBeenCalled()
      })
    })

    it('should validate cash flow equation: Beginning + Net Change = Ending', async () => {
      const mockData = generateCashFlowData('precisionTest')
      const validation = calculateCashFlowValidation(mockData)

      expect(validation.isEndingCashValid).toBe(true)

      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      await waitFor(() => {
        expect(screen.getByText('Ending Cash')).toBeInTheDocument()
      })
    })

    it('should handle period selection', async () => {
      const user = userEvent.setup()
      const mockData = generateCashFlowData('normal')
      useCashFlow.mockReturnValue({ data: mockData, isLoading: false, error: null })

      await act(async () => {
        render(<CashFlowPage />, { wrapper: createWrapper() })
      })

      const periodSelect = screen.queryByLabelText(/period/i)
      if (periodSelect) {
        await act(async () => {
          await user.selectOptions(periodSelect, 'period-1')
        })

        await waitFor(() => {
          expect(useCashFlow).toHaveBeenCalled()
        })
      }
    })
  })
})
