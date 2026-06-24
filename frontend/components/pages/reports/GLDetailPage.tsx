'use client'

import { useState, useMemo, useEffect } from 'react'
import Link from 'next/link'
import { useGLDetail } from '@/hooks/useReports'
import { formatCurrency, formatDate } from '@/lib/utils/format'
import { reportingApi } from '@/lib/api/reportingApi'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'
import { VirtualizedTableWrapper } from '@/components/common/VirtualizedTableWrapper'

export function GLDetailPage() {
  const { selectedEntityId, selectedBookId } = useEntityBook()
  const legalEntityId = selectedEntityId || ''
  const bookId = selectedBookId || ''
  const [periodId, setPeriodId] = useState<string>('')
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0])
  const [accountId, setAccountId] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [page, setPage] = useState(1)
  const pageSize = 50

  // Drill-down: when navigated from Trial Balance (?account=CODE), filter to that account.
  const [accountCode, setAccountCode] = useState<string>('')
  useEffect(() => {
    const fromQuery = new URLSearchParams(window.location.search).get('account')
    if (fromQuery) setAccountCode(fromQuery)
  }, [])

  const { data: report, isLoading, error } = useGLDetail({
    legal_entity_id: legalEntityId,
    book_id: bookId,
    period_id: periodId || undefined,
    as_of_date: asOfDate,
    account_id: accountId || undefined,
    search: searchTerm || undefined,
    page,
    page_size: pageSize,
  })

  // Prepare chart data (must run before any return to satisfy rules-of-hooks)
  const chartData = useMemo(() => {
    if (!report?.rows) return null
    const dailyActivity = report.rows.reduce((acc, row) => {
      const date = row.entry_date.split('T')[0]
      if (!acc[date]) {
        acc[date] = { date, count: 0, debits: 0, credits: 0 }
      }
      acc[date].count++
      acc[date].debits += row.debit_amount
      acc[date].credits += row.credit_amount
      return acc
    }, {} as Record<string, { date: string; count: number; debits: number; credits: number }>)
    const dailyActivityArray = Object.values(dailyActivity).sort((a, b) => a.date.localeCompare(b.date))
    const accountActivity = report.rows.reduce((acc, row) => {
      const key = `${row.account_code} - ${row.account_name}`
      if (!acc[key]) {
        acc[key] = { account: row.account_code, name: row.account_name, count: 0, total: 0 }
      }
      acc[key].count++
      acc[key].total += Math.abs(row.debit_amount) + Math.abs(row.credit_amount)
      return acc
    }, {} as Record<string, { account: string; name: string; count: number; total: number }>)
    const topAccounts = Object.values(accountActivity)
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
      .map((acc) => ({ name: acc.account, fullName: `${acc.account} - ${acc.name}`, count: acc.count, total: acc.total }))
    const accountDistribution = Object.values(accountActivity)
      .sort((a, b) => b.total - a.total)
      .slice(0, 8)
      .map((acc) => ({ name: acc.account, value: acc.total }))
    return { dailyActivity: dailyActivityArray, topAccounts, accountDistribution }
  }, [report?.rows])

  const handleExportPDF = async () => {
    try {
      const blob = await reportingApi.exportReportPDF('gl-detail', {
        legal_entity_id: legalEntityId,
        book_id: bookId,
        period_id: periodId,
        as_of_date: asOfDate,
        account_id: accountId,
        search: searchTerm,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `gl_detail_${asOfDate}.pdf`
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
      const blob = await reportingApi.exportReportExcel('gl-detail', {
        legal_entity_id: legalEntityId,
        book_id: bookId,
        period_id: periodId,
        as_of_date: asOfDate,
        account_id: accountId,
        search: searchTerm,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `gl_detail_${asOfDate}.xlsx`
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
        Error loading GL detail. Please try again.
      </div>
    )
  }

  const totalDebits = report?.total_debits || 0
  const totalCredits = report?.total_credits || 0
  const netBalance = totalDebits - totalCredits
  const transactionCount = report?.rows?.length || 0

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

  const allRows = report?.rows || []
  const displayedRows = accountCode
    ? allRows.filter((r) => r.account_code === accountCode)
    : allRows

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">GL Detail Report</h1>
          <p className="text-gray-600 mt-1">Detailed journal entry transactions</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleExportPDF} className="btn-outline">
            Export PDF
          </button>
          <button onClick={handleExportExcel} className="btn-outline">
            Export Excel
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Debits</h3>
          <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalDebits)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Credits</h3>
          <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalCredits)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Net Balance</h3>
          <p
            className={`text-2xl font-bold ${
              Math.abs(netBalance) < 0.01 ? 'text-green-600' : 'text-gray-900'
            }`}
          >
            {formatCurrency(netBalance)}
          </p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Transactions</h3>
          <p className="text-2xl font-bold text-gray-900">{transactionCount}</p>
        </div>
      </div>

      {/* Charts */}
      {chartData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Debit vs Credit Distribution */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Debit vs Credit Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  { name: 'Total Debits', value: totalDebits },
                  { name: 'Total Credits', value: totalCredits },
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

          {/* Account Distribution */}
          {chartData.accountDistribution.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Accounts by Volume</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData.accountDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.accountDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Daily Transaction Activity */}
          {chartData.dailyActivity.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Transaction Activity</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData.dailyActivity}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    angle={-45} 
                    textAnchor="end" 
                    height={80}
                    tickFormatter={(value) => formatDate(value)}
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value: number) => formatCurrency(value)}
                    labelFormatter={(value) => formatDate(value)}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="debits" stroke="#10b981" name="Debits" />
                  <Line type="monotone" dataKey="credits" stroke="#ef4444" name="Credits" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top Accounts by Transaction Count */}
          {chartData.topAccounts.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Accounts by Transaction Count</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData.topAccounts}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="name" 
                    angle={-45} 
                    textAnchor="end" 
                    height={100}
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value: number, name: string) => {
                      if (name === 'count') return value
                      return formatCurrency(value)
                    }}
                  />
                  <Legend />
                  <Bar dataKey="count" fill="#3b82f6" name="Transaction Count" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      <div className="card">
        <div className="flex items-center gap-4 mb-4">
          <input
            type="date"
            value={asOfDate}
            onChange={(e) => setAsOfDate(e.target.value)}
            className="input"
            placeholder="As of Date"
          />
          <input
            type="text"
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            className="input"
            placeholder="Filter by Account ID"
          />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input"
            placeholder="Search description..."
          />
          {accountCode && (
            <span className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1 text-sm text-primary-700">
              Account: {accountCode}
              <button
                type="button"
                onClick={() => setAccountCode('')}
                className="font-bold hover:text-primary-900"
                title="Clear account filter"
                aria-label="Clear account filter"
              >
                ×
              </button>
            </span>
          )}
        </div>

        {displayedRows.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">
              {accountCode
                ? `No transactions found for account ${accountCode}`
                : 'No transactions found'}
            </p>
          </div>
        ) : (
          <>
            <VirtualizedTableWrapper
              data={displayedRows}
              height={600}
              renderHeader={() => (
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Entry #</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debit</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Credit</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Balance</th>
                </tr>
              )}
              renderRow={(row) => (
                <>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(row.entry_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Link
                      href={`/journal-entries/${row.entry_id}`}
                      className="text-primary-600 hover:underline"
                      title="View journal entry"
                    >
                      {row.entry_number}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.account_code} - {row.account_name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{row.description || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {row.debit_amount > 0 ? formatCurrency(row.debit_amount) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {row.credit_amount > 0 ? formatCurrency(row.credit_amount) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-gray-900">
                    {formatCurrency(row.balance)}
                  </td>
                </>
              )}
              estimateSize={() => 50}
            />

            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Showing page {page} of {Math.ceil((report?.rows?.length || 0) / pageSize)}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-sm"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={(report?.rows?.length || 0) < pageSize}
                  className="btn-secondary text-sm"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
