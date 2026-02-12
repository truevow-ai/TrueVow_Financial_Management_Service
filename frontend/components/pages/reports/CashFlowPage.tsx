'use client'

import { useState } from 'react'
import { useCashFlow } from '@/hooks/useReports'
import { formatCurrency, formatDate } from '@/lib/utils/format'
import { reportingApi } from '@/lib/api/reportingApi'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export function CashFlowPage() {
  const { selectedEntityId, selectedBookId } = useEntityBook()
  const legalEntityId = selectedEntityId || ''
  const bookId = selectedBookId || ''
  const [periodId, setPeriodId] = useState<string>('')
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0])

  const { data: report, isLoading, error } = useCashFlow({
    legal_entity_id: legalEntityId,
    book_id: bookId,
    period_id: periodId || undefined,
    as_of_date: asOfDate,
  })

  const handleExportPDF = async () => {
    try {
      const blob = await reportingApi.exportReportPDF('cash-flow', {
        legal_entity_id: legalEntityId,
        book_id: bookId,
        period_id: periodId,
        as_of_date: asOfDate,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cash_flow_${asOfDate}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export PDF:', error)
      alert('Failed to export PDF')
    }
  }

  const handleExportExcel = async () => {
    try {
      const blob = await reportingApi.exportReportExcel('cash-flow', {
        legal_entity_id: legalEntityId,
        book_id: bookId,
        period_id: periodId,
        as_of_date: asOfDate,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cash_flow_${asOfDate}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export Excel:', error)
      alert('Failed to export Excel')
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
        Error loading cash flow statement. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cash Flow Statement</h1>
          <p className="text-gray-600 mt-1">For period ending {formatDate(report?.as_of_date || asOfDate)}</p>
        </div>
        <div className="flex gap-2">
          <input
            type="date"
            value={asOfDate}
            onChange={(e) => setAsOfDate(e.target.value)}
            className="input"
          />
          <button onClick={handleExportPDF} className="btn-outline">
            Export PDF
          </button>
          <button onClick={handleExportExcel} className="btn-outline">
            Export Excel
          </button>
        </div>
      </div>

      <div className="card">
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Operating Activities</h3>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(report?.operating_activities || 0)}
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Investing Activities</h3>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(report?.investing_activities || 0)}
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Financing Activities</h3>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(report?.financing_activities || 0)}
            </p>
          </div>

          <div className="pt-4 border-t">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Net Change in Cash</h3>
            <p className="text-3xl font-bold text-gray-900">{formatCurrency(report?.net_change || 0)}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Beginning Cash</h3>
              <p className="text-xl font-semibold text-gray-900">
                {formatCurrency(report?.beginning_cash || 0)}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Ending Cash</h3>
              <p className="text-xl font-semibold text-gray-900">
                {formatCurrency(report?.ending_cash || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {report && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Cash Flow Activities</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={[
                {
                  name: 'Operating',
                  value: report.operating_activities || 0,
                },
                {
                  name: 'Investing',
                  value: report.investing_activities || 0,
                },
                {
                  name: 'Financing',
                  value: report.financing_activities || 0,
                },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
