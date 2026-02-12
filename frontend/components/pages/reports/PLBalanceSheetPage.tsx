'use client'

import { useState } from 'react'
import { usePLBalanceSheet } from '@/hooks/useReports'
import { formatCurrency, formatDate } from '@/lib/utils/format'
import { reportingApi } from '@/lib/api/reportingApi'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

export function PLBalanceSheetPage() {
  const { selectedEntityId, selectedBookId } = useEntityBook()
  const legalEntityId = selectedEntityId || ''
  const bookId = selectedBookId || ''
  const [periodId, setPeriodId] = useState<string>('')
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0])
  const [reportType, setReportType] = useState<'pl' | 'balance-sheet'>('pl')

  const { data: report, isLoading, error } = usePLBalanceSheet({
    legal_entity_id: legalEntityId,
    book_id: bookId,
    period_id: periodId || undefined,
    as_of_date: asOfDate,
  })

  const handleExportPDF = async () => {
    try {
      const blob = await reportingApi.exportReportPDF(reportType, {
        legal_entity_id: legalEntityId,
        book_id: bookId,
        period_id: periodId,
        as_of_date: asOfDate,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${reportType}_${asOfDate}.pdf`
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
      const blob = await reportingApi.exportReportExcel(reportType, {
        legal_entity_id: legalEntityId,
        book_id: bookId,
        period_id: periodId,
        as_of_date: asOfDate,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${reportType}_${asOfDate}.xlsx`
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
        Error loading report. Please try again.
      </div>
    )
  }

  // Prepare chart data
  const plChartData = reportType === 'pl' && report ? [
    { name: 'Revenue', value: report.revenue || 0 },
    { name: 'Expenses', value: Math.abs(report.expenses || 0) },
    { name: 'Net Income', value: report.net_income || 0 },
  ] : []

  const balanceSheetChartData = reportType === 'balance-sheet' && report ? [
    { name: 'Assets', value: report.assets || 0 },
    { name: 'Liabilities', value: report.liabilities || 0 },
    { name: 'Equity', value: report.equity || 0 },
  ] : []

  const COLORS = ['#10b981', '#ef4444', '#3b82f6']

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {reportType === 'pl' ? 'Profit & Loss Statement' : 'Balance Sheet'}
          </h1>
          <p className="text-gray-600 mt-1">As of {formatDate(report?.as_of_date || asOfDate)}</p>
        </div>
        <div className="flex gap-2">
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value as 'pl' | 'balance-sheet')}
            className="input"
          >
            <option value="pl">Profit & Loss</option>
            <option value="balance-sheet">Balance Sheet</option>
          </select>
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

      {reportType === 'pl' ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Revenue</h2>
              <p className="text-3xl font-bold text-green-600">{formatCurrency(report?.revenue || 0)}</p>
            </div>
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Expenses</h2>
              <p className="text-3xl font-bold text-red-600">{formatCurrency(report?.expenses || 0)}</p>
            </div>
            <div className="card md:col-span-2">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Net Income</h2>
              <p
                className={`text-4xl font-bold ${
                  (report?.net_income || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {formatCurrency(report?.net_income || 0)}
              </p>
            </div>
          </div>

          {plChartData.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">P&L Overview</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={plChartData}>
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
        </>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Assets</h2>
              <p className="text-3xl font-bold text-gray-900">{formatCurrency(report?.assets || 0)}</p>
            </div>
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Liabilities</h2>
              <p className="text-3xl font-bold text-gray-900">{formatCurrency(report?.liabilities || 0)}</p>
            </div>
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Equity</h2>
              <p className="text-3xl font-bold text-gray-900">{formatCurrency(report?.equity || 0)}</p>
            </div>
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Balance</h2>
              <p
                className={`text-2xl font-bold ${
                  Math.abs((report?.assets || 0) - (report?.liabilities || 0) - (report?.equity || 0)) < 0.01
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {formatCurrency(
                  (report?.assets || 0) - (report?.liabilities || 0) - (report?.equity || 0)
                )}
              </p>
            </div>
          </div>

          {balanceSheetChartData.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Balance Sheet Composition</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={balanceSheetChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {balanceSheetChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  )
}
