'use client'

import { useState } from 'react'
import { useTrialBalance } from '@/hooks/useReports'
import { formatCurrency, formatDate } from '@/lib/utils/format'
import { reportingApi } from '@/lib/api/reportingApi'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { VirtualizedTableWrapper } from '@/components/common/VirtualizedTableWrapper'

export function TrialBalancePage() {
  const { selectedEntityId, selectedBookId } = useEntityBook()
  const legalEntityId = selectedEntityId || ''
  const bookId = selectedBookId || ''
  const [periodId, setPeriodId] = useState<string>('')
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0])

  const { data: report, isLoading, error } = useTrialBalance({
    legal_entity_id: legalEntityId,
    book_id: bookId,
    period_id: periodId || undefined,
    as_of_date: asOfDate,
  })

  const handleExportPDF = async () => {
    try {
      const blob = await reportingApi.exportReportPDF('trial-balance', {
        legal_entity_id: legalEntityId,
        book_id: bookId,
        period_id: periodId,
        as_of_date: asOfDate,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `trial_balance_${asOfDate}.pdf`
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
      const blob = await reportingApi.exportReportExcel('trial-balance', {
        legal_entity_id: legalEntityId,
        book_id: bookId,
        period_id: periodId,
        as_of_date: asOfDate,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `trial_balance_${asOfDate}.xlsx`
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
        Error loading trial balance. Please try again.
      </div>
    )
  }

  const totalDebits = report?.rows?.reduce((sum, row) => sum + row.debit_balance, 0) || 0
  const totalCredits = report?.rows?.reduce((sum, row) => sum + row.credit_balance, 0) || 0

  // Prepare chart data - top 10 accounts by absolute balance
  const chartData = report?.rows
    ?.map((row) => ({
      account: row.account_code,
      name: row.account_name.substring(0, 20) + (row.account_name.length > 20 ? '...' : ''),
      debit: row.debit_balance,
      credit: row.credit_balance,
      net: row.debit_balance - row.credit_balance,
    }))
    .sort((a, b) => Math.abs(b.net) - Math.abs(a.net))
    .slice(0, 10) || []

  // Balance distribution chart data
  const balanceDistribution = report?.rows
    ?.reduce(
      (acc, row) => {
        const net = row.debit_balance - row.credit_balance
        if (net > 0) {
          acc.debitTotal += net
        } else {
          acc.creditTotal += Math.abs(net)
        }
        return acc
      },
      { debitTotal: 0, creditTotal: 0 }
    ) || { debitTotal: 0, creditTotal: 0 }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trial Balance</h1>
          <p className="text-gray-600 mt-1">Account balances as of {formatDate(report?.as_of_date || asOfDate)}</p>
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Debits</h3>
          <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalDebits)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Credits</h3>
          <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalCredits)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Balance</h3>
          <p
            className={`text-2xl font-bold ${
              Math.abs(totalDebits - totalCredits) < 0.01 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {formatCurrency(totalDebits - totalCredits)}
          </p>
        </div>
      </div>

      {/* Charts */}
      {chartData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Accounts by Balance</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Bar dataKey="debit" fill="#10b981" name="Debit" />
                <Bar dataKey="credit" fill="#ef4444" name="Credit" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Balance Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  { name: 'Total Debits', value: balanceDistribution.debitTotal },
                  { name: 'Total Credits', value: balanceDistribution.creditTotal },
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
        </div>
      )}

      {/* Trial Balance Table */}
      <div className="card">
        {report && report.rows && report.rows.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No data available for the selected period</p>
          </div>
        ) : (
          <>
            <VirtualizedTableWrapper
              data={report?.rows || []}
              height={600}
              renderHeader={() => (
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account Code</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account Name</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debit Balance</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Credit Balance</th>
                </tr>
              )}
              renderRow={(row) => (
                <>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {row.account_code}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{row.account_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {row.debit_balance > 0 ? formatCurrency(row.debit_balance) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {row.credit_balance > 0 ? formatCurrency(row.credit_balance) : '-'}
                  </td>
                </>
              )}
              estimateSize={() => 50}
            />
            {/* Footer with totals */}
            <div className="mt-4 bg-gray-50 border-t border-gray-200 px-6 py-4">
              <div className="flex justify-between">
                <div className="text-sm font-bold text-gray-900">Total</div>
                <div className="flex gap-8">
                  <div className="text-sm font-bold text-right text-gray-900">
                    {formatCurrency(totalDebits)}
                  </div>
                  <div className="text-sm font-bold text-right text-gray-900">
                    {formatCurrency(totalCredits)}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
