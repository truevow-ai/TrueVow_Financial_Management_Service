'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRevenueSchedules, useRecognizeRevenue } from '@/hooks/useAR'
import { formatDate, formatCurrency } from '@/lib/utils/format'

export function DeferredRevenuePage() {
  const [invoiceFilter, setInvoiceFilter] = useState<string>('')
  const [recognizedFilter, setRecognizedFilter] = useState<string>('')
  const { data: schedules, isLoading, error } = useRevenueSchedules({
    invoice_id: invoiceFilter || undefined,
    is_recognized: recognizedFilter ? recognizedFilter === 'true' : undefined,
  })
  const recognizeMutation = useRecognizeRevenue()

  const handleRecognize = async (scheduleId: string, periodId: string) => {
    if (window.confirm('Are you sure you want to recognize revenue for this period?')) {
      try {
        await recognizeMutation.mutateAsync({ schedule_id: scheduleId, period_id: periodId })
      } catch (error) {
        console.error('Failed to recognize revenue:', error)
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        Error loading revenue schedules. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Deferred Revenue Schedules</h1>
          <p className="text-gray-600 mt-1">Manage revenue recognition schedules</p>
        </div>
        <div className="flex gap-2">
          <select
            value={recognizedFilter}
            onChange={(e) => setRecognizedFilter(e.target.value)}
            className="input"
          >
            <option value="">All Schedules</option>
            <option value="false">Unrecognized</option>
            <option value="true">Recognized</option>
          </select>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-4 mb-4">
          <label htmlFor="invoice-filter" className="text-sm font-medium text-gray-700">
            Filter by Invoice:
          </label>
          <input
            id="invoice-filter"
            type="text"
            value={invoiceFilter}
            onChange={(e) => setInvoiceFilter(e.target.value)}
            className="input"
            placeholder="Invoice ID"
          />
        </div>

        {schedules && schedules.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No revenue schedules found</p>
          </div>
        ) : (
          <div className="space-y-6">
            {schedules?.map((schedule) => {
              const recognizedPeriods = schedule.periods?.filter((p) => p.is_recognized) || []
              const unrecognizedPeriods = schedule.periods?.filter((p) => !p.is_recognized) || []
              const recognitionProgress =
                schedule.total_amount > 0
                  ? (schedule.recognized_amount / schedule.total_amount) * 100
                  : 0

              return (
                <div key={schedule.id} className="border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        Schedule for Invoice: {schedule.invoice_id}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {formatDate(schedule.start_date)} to {formatDate(schedule.end_date)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Recognition Progress</p>
                      <p className="text-lg font-semibold text-gray-900">{recognitionProgress.toFixed(1)}%</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-500">Total Amount</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatCurrency(schedule.total_amount)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Recognized</p>
                      <p className="text-lg font-semibold text-green-600">
                        {formatCurrency(schedule.recognized_amount)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Remaining</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatCurrency(schedule.remaining_amount)}
                      </p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      Recognition Method: {schedule.recognition_method}
                    </p>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full"
                        style={{ width: `${recognitionProgress}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Schedule Periods</h4>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              Period
                            </th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                              Amount
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              Status
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {schedule.periods?.map((period) => (
                            <tr key={period.id}>
                              <td className="px-4 py-2 text-sm text-gray-900">
                                {formatDate(period.period_start)} to {formatDate(period.period_end)}
                              </td>
                              <td className="px-4 py-2 text-sm text-right text-gray-900">
                                {formatCurrency(period.amount)}
                              </td>
                              <td className="px-4 py-2">
                                <span
                                  className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                    period.is_recognized
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-gray-100 text-gray-800'
                                  }`}
                                >
                                  {period.is_recognized ? 'Recognized' : 'Pending'}
                                </span>
                              </td>
                              <td className="px-4 py-2">
                                {!period.is_recognized && (
                                  <button
                                    onClick={() => handleRecognize(schedule.id, period.period_id)}
                                    className="text-sm text-primary-600 hover:text-primary-900"
                                    disabled={recognizeMutation.isPending}
                                  >
                                    Recognize
                                  </button>
                                )}
                                {period.recognized_at && (
                                  <p className="text-xs text-gray-500">
                                    Recognized: {formatDate(period.recognized_at)}
                                  </p>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t">
                    <Link
                      href={`/ar/invoices/${schedule.invoice_id}`}
                      className="text-sm text-primary-600 hover:text-primary-900"
                    >
                      View Invoice →
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
