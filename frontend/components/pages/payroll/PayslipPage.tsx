'use client'

import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { usePayslip } from '@/hooks/usePayroll'
import { formatDate, formatCurrency } from '@/lib/utils/format'

export function PayslipPage() {
  const params = useParams()
  const router = useRouter()
  const runId = params?.runId as string
  const employeeId = params?.employeeId as string
  const { data: payslip, isLoading, error } = usePayslip(runId || '', employeeId || '')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !payslip) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        Payslip not found.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href={`/payroll/runs/${runId}`}
          className="text-primary-600 hover:text-primary-900 text-sm mb-2 inline-block"
        >
          ← Back to Payroll Run
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Payslip</h1>
        <p className="text-gray-600 mt-1">{payslip.employee_name}</p>
      </div>

      <div className="card">
        <div className="border-b border-gray-200 pb-4 mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Pay Period Information</h2>
          <div className="grid grid-cols-2 gap-4 mt-2">
            <div>
              <p className="text-sm text-gray-500">Period</p>
              <p className="text-sm font-medium text-gray-900">
                {formatDate(payslip.period_start)} - {formatDate(payslip.period_end)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Pay Date</p>
              <p className="text-sm font-medium text-gray-900">{formatDate(payslip.pay_date)}</p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Earnings</h3>
            <div className="space-y-1">
              {payslip.components
                ?.filter((c) => c.amount > 0)
                .map((component, index) => (
                  <div key={component.id || `earnings-${index}`} className="flex justify-between text-sm">
                    <span className="text-gray-600">{component.component_name}</span>
                    <span className="text-gray-900">{formatCurrency(component.amount)}</span>
                  </div>
                ))}
              <div className="flex justify-between text-sm font-semibold pt-2 border-t">
                <span className="text-gray-900">Gross Pay</span>
                <span className="text-gray-900">{formatCurrency(payslip.gross_pay)}</span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Deductions</h3>
            <div className="space-y-1">
              {payslip.components
                ?.filter((c) => c.amount < 0)
                .map((component, index) => (
                  <div key={component.id || `deduction-${index}`} className="flex justify-between text-sm">
                    <span className="text-gray-600">{component.component_name}</span>
                    <span className="text-gray-900">{formatCurrency(Math.abs(component.amount))}</span>
                  </div>
                ))}
              {payslip.components?.filter((c) => c.amount < 0).length === 0 && (
                <p className="text-sm text-gray-500">No deductions</p>
              )}
              <div className="flex justify-between text-sm font-semibold pt-2 border-t">
                <span className="text-gray-900">Total Deductions</span>
                <span className="text-gray-900">{formatCurrency(payslip.deductions)}</span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t">
            <div className="flex justify-between text-lg font-bold">
              <span className="text-gray-900">Net Pay</span>
              <span className="text-gray-900">{formatCurrency(payslip.net_pay)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
