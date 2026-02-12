'use client'

import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { useState } from 'react'
import {
  usePayrollRun,
  usePayrollRunDetails,
  useCalculatePayrollRun,
  useApprovePayrollRun,
  usePostPayrollRun,
  useEmployees,
  useBulkUpsertPayrollAdjustments,
  useRecalculatePayrollRun,
} from '@/hooks/usePayroll'
import { formatDate, formatCurrency } from '@/lib/utils/format'
import { PayrollAdjustmentsGrid, PayrollAdjustment } from '@/components/common/PayrollAdjustmentsGrid'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { useToast } from '@/hooks/useToast'

export function PayrollRunDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { showToast } = useToast()
  const { selectedEntityId } = useEntityBook()
  const id = params?.id as string
  const { data: run, isLoading, error } = usePayrollRun(id)
  const { data: details } = usePayrollRunDetails(id)
  const { data: employees } = useEmployees({ legal_entity_id: selectedEntityId || undefined })
  const calculateMutation = useCalculatePayrollRun()
  const approveMutation = useApprovePayrollRun()
  const postMutation = usePostPayrollRun()
  const bulkUpsertMutation = useBulkUpsertPayrollAdjustments()
  const recalculateMutation = useRecalculatePayrollRun()

  const [selectedEmployee, setSelectedEmployee] = useState<string | null>(null)
  const [adjustments, setAdjustments] = useState<PayrollAdjustment[]>([])
  const [showAdjustmentsGrid, setShowAdjustmentsGrid] = useState(false)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !run) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        Payroll run not found.
      </div>
    )
  }

  const handleCalculate = async () => {
    if (window.confirm('Calculate payroll for this run? This will compute all employee payments.')) {
      try {
        await calculateMutation.mutateAsync(run.id)
      } catch (error) {
        console.error('Failed to calculate payroll:', error)
      }
    }
  }

  const handleApprove = async () => {
    if (window.confirm('Approve this payroll run? This will allow posting to the general ledger.')) {
      try {
        await approveMutation.mutateAsync(run.id)
      } catch (error) {
        console.error('Failed to approve payroll:', error)
      }
    }
  }

  const handlePost = async () => {
    if (
      window.confirm(
        'Post this payroll run? This will create journal entries in the general ledger. This action cannot be undone.'
      )
    ) {
      try {
        await postMutation.mutateAsync(run.id)
      } catch (error) {
        console.error('Failed to post payroll:', error)
      }
    }
  }

  const selectedDetail = details?.find((d) => d.employee_id === selectedEmployee)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/payroll/runs" className="text-primary-600 hover:text-primary-900 text-sm mb-2 inline-block">
            ← Back to Payroll Runs
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Payroll Run Details</h1>
          <p className="text-gray-600 mt-1">
            Period: {formatDate(run.period_start)} - {formatDate(run.period_end)}
          </p>
        </div>
        <div className="flex gap-2">
          {run.status === 'draft' && (
            <button
              onClick={handleCalculate}
              className="btn-primary"
              disabled={calculateMutation.isPending}
            >
              {calculateMutation.isPending ? 'Calculating...' : 'Calculate Payroll'}
            </button>
          )}
          {run.status === 'calculated' && (
            <button
              onClick={handleApprove}
              className="btn-primary"
              disabled={approveMutation.isPending}
            >
              {approveMutation.isPending ? 'Approving...' : 'Approve'}
            </button>
          )}
          {run.status === 'approved' && (
            <button onClick={handlePost} className="btn-primary" disabled={postMutation.isPending}>
              {postMutation.isPending ? 'Posting...' : 'Post to GL'}
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Run Information</h2>
          <dl className="space-y-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Period</dt>
              <dd className="text-sm text-gray-900">
                {formatDate(run.period_start)} to {formatDate(run.period_end)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Pay Date</dt>
              <dd className="text-sm text-gray-900">{formatDate(run.pay_date)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="text-sm">
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    run.status === 'posted'
                      ? 'bg-green-100 text-green-800'
                      : run.status === 'approved'
                      ? 'bg-blue-100 text-blue-800'
                      : run.status === 'calculated'
                      ? 'bg-yellow-100 text-yellow-800'
                      : run.status === 'cancelled'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {run.status}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Employee Count</dt>
              <dd className="text-sm text-gray-900">{run.employee_count}</dd>
            </div>
          </dl>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Totals</h2>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-sm font-medium text-gray-500">Total Gross</dt>
              <dd className="text-sm font-semibold text-gray-900">{formatCurrency(run.total_gross)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm font-medium text-gray-500">Total Deductions</dt>
              <dd className="text-sm font-semibold text-gray-900">{formatCurrency(run.total_deductions)}</dd>
            </div>
            <div className="flex justify-between pt-2 border-t">
              <dt className="text-sm font-medium text-gray-500">Net Pay</dt>
              <dd className="text-sm font-bold text-gray-900">{formatCurrency(run.total_net)}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Employee Details</h2>
        {details && details.length === 0 ? (
          <p className="text-gray-500 text-sm">No employee details available</p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Gross</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Net</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {details?.map((detail) => (
                    <tr
                      key={detail.id}
                      className={`hover:bg-gray-50 cursor-pointer ${
                        selectedEmployee === detail.employee_id ? 'bg-primary-50' : ''
                      }`}
                      onClick={() => setSelectedEmployee(detail.employee_id)}
                    >
                      <td className="px-4 py-2 text-sm text-gray-900">{detail.employee_id}</td>
                      <td className="px-4 py-2 text-sm text-right text-gray-900">
                        {formatCurrency(detail.gross_pay)}
                      </td>
                      <td className="px-4 py-2 text-sm text-right font-semibold text-gray-900">
                        {formatCurrency(detail.net_pay)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedDetail && (
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Component Breakdown</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Gross Pay</span>
                    <span className="font-medium text-gray-900">{formatCurrency(selectedDetail.gross_pay)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Deductions</span>
                    <span className="font-medium text-gray-900">{formatCurrency(selectedDetail.deductions)}</span>
                  </div>
                  <div className="flex justify-between text-sm pt-2 border-t font-semibold">
                    <span className="text-gray-900">Net Pay</span>
                    <span className="text-gray-900">{formatCurrency(selectedDetail.net_pay)}</span>
                  </div>
                  {selectedDetail.components && selectedDetail.components.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-xs font-medium text-gray-700 mb-2">Components</h4>
                      <div className="space-y-1">
                        {selectedDetail.components.map((comp) => (
                          <div key={comp.id} className="flex justify-between text-xs">
                            <span className="text-gray-600">{comp.component_name}</span>
                            <span className="text-gray-900">{formatCurrency(comp.amount)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Payroll Adjustments Grid */}
      {showAdjustmentsGrid && run.status === 'draft' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Payroll Adjustments</h2>
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  if (!run.id) return
                  try {
                    const result = await recalculateMutation.mutateAsync({ runId: run.id })
                    if (result.is_valid) {
                      showToast('Payroll recalculated successfully', 'success')
                    } else {
                      showToast(`Recalculation completed with ${result.errors.length} error(s)`, 'warning')
                    }
                  } catch (error: any) {
                    showToast(error.message || 'Failed to recalculate', 'error')
                  }
                }}
                className="btn-secondary text-sm"
                disabled={recalculateMutation.isPending}
              >
                {recalculateMutation.isPending ? 'Recalculating...' : 'Recalculate'}
              </button>
            </div>
          </div>
          <PayrollAdjustmentsGrid
            adjustments={adjustments}
            onAdjustmentsChange={(newAdjustments) => {
              setAdjustments(newAdjustments)
              // Auto-save with debounce
              if (run.id) {
                const timeoutId = setTimeout(() => {
                  bulkUpsertMutation.mutate(
                    {
                      runId: run.id!,
                      adjustments: newAdjustments.map((adj) => ({
                        client_row_id: adj.client_row_id,
                        adjustment_id: adj.adjustment_id,
                        employee_id: adj.employee_id,
                        component_type: adj.component_type,
                        amount: adj.amount,
                        currency: adj.currency,
                        memo: adj.memo,
                        cost_center: adj.cost_center,
                        department: adj.department,
                        location: adj.location,
                      })),
                    },
                    {
                      onSuccess: (data) => {
                        setAdjustments(
                          data.adjustments.map((adj, index) => ({
                            ...newAdjustments[index],
                            adjustment_id: adj.id,
                          }))
                        )
                      },
                    }
                  )
                }, 500)
                return () => clearTimeout(timeoutId)
              }
            }}
            employees={
              employees?.map((emp) => ({
                id: emp.id,
                employee_name: `${emp.first_name} ${emp.last_name}`,
                employee_number: emp.employee_code,
              })) || []
            }
            defaultCurrency="USD"
          />
        </div>
      )}
    </div>
  )
}
