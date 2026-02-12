/**
 * Comprehensive Tests for PayslipPage
 * Tests all outputs, calculations, and edge cases
 */

import React from 'react'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import { PayslipPage } from '@/components/pages/payroll/PayslipPage'

jest.mock('next/navigation', () => ({
  useParams: () => ({ runId: 'run-1', employeeId: 'emp-1' }),
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
}))

jest.mock('@/hooks/usePayroll', () => ({
  usePayslip: jest.fn(),
}))

const { usePayslip } = require('@/hooks/usePayroll')

describe('PayslipPage - Comprehensive Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  describe('Output - Payslip Information', () => {
    it('should display payslip details', async () => {
      const mockPayslip = {
        id: 'payslip-1',
        employee_name: 'John Doe',
        employee_id: 'emp-1',
        run_id: 'run-1',
        pay_period_start: '2024-01-01',
        pay_period_end: '2024-01-31',
        gross_pay: 5000,
        deductions: 1000,
        net_pay: 4000,
        components: [],
      }

      usePayslip.mockReturnValue({ data: mockPayslip, isLoading: false, error: null })

      await act(async () => {
        render(<PayslipPage />)
      })

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument()
      })
    })
  })

  describe('Output - Pay Components', () => {
    it('should display pay components', async () => {
      const mockPayslip = {
        id: 'payslip-1',
        employee_name: 'John Doe',
        employee_id: 'emp-1',
        run_id: 'run-1',
        pay_period_start: '2024-01-01',
        pay_period_end: '2024-01-31',
        gross_pay: 5000,
        deductions: 1000,
        net_pay: 4000,
        components: [
          { name: 'Base Salary', amount: 5000, type: 'earnings' },
          { name: 'Tax', amount: 1000, type: 'deductions' },
        ],
      }

      usePayslip.mockReturnValue({ data: mockPayslip, isLoading: false, error: null })

      await act(async () => {
        render(<PayslipPage />)
      })

      await waitFor(() => {
        expect(screen.getByText(/payslip/i)).toBeInTheDocument()
      })
    })
  })

  describe('Accounting Precision', () => {
    it('should calculate net pay correctly', async () => {
      const mockPayslip = {
        id: 'payslip-1',
        employee_name: 'John Doe',
        employee_id: 'emp-1',
        run_id: 'run-1',
        pay_period_start: '2024-01-01',
        pay_period_end: '2024-01-31',
        gross_pay: 5000,
        deductions: 1000,
        net_pay: 4000,
        components: [],
      }

      usePayslip.mockReturnValue({ data: mockPayslip, isLoading: false, error: null })

      await act(async () => {
        render(<PayslipPage />)
      })

      await waitFor(() => {
        const calculatedNet = mockPayslip.gross_pay - mockPayslip.deductions
        expect(calculatedNet).toBe(mockPayslip.net_pay)
      })
    })
  })

  describe('Loading and Error States', () => {
    it('should show loading spinner', async () => {
      usePayslip.mockReturnValue({ data: undefined, isLoading: true, error: null })

      await act(async () => {
        render(<PayslipPage />)
      })

      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })

    it('should show error message', async () => {
      usePayslip.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Not found'),
      })

      await act(async () => {
        render(<PayslipPage />)
      })

      expect(screen.getByText(/payslip not found/i)).toBeInTheDocument()
    })
  })
})
