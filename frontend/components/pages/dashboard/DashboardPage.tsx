'use client'

import Link from 'next/link'
import { useJournalEntries } from '@/hooks/useJournalEntries'
import { usePLBalanceSheet } from '@/hooks/useReports'
import { useCashPosition } from '@/hooks/useReports'
import { useTrialBalance } from '@/hooks/useReports'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { formatCurrency, formatDate } from '@/lib/utils/format'

export function DashboardPage() {
  const { selectedEntityId, selectedBookId } = useEntityBook()
  const legalEntityId = selectedEntityId || ''
  const bookId = selectedBookId || ''

  const { data: journalEntries } = useJournalEntries({ page_size: 5 })
  const { data: plData } = usePLBalanceSheet({
    legal_entity_id: legalEntityId,
    book_id: bookId,
  })
  const { data: cashData } = useCashPosition({
    legal_entity_id: legalEntityId,
    book_id: bookId,
  })
  const { data: trialBalance } = useTrialBalance({
    legal_entity_id: legalEntityId,
    book_id: bookId,
  })

  const revenue = plData?.revenue || 0
  const expenses = plData?.expenses || 0
  const netProfit = plData?.net_income || 0
  const cashPosition = cashData?.total_cash || 0

  const recentEntries = journalEntries?.items?.slice(0, 5) || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome to TrueVow Financial Management</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Total Revenue</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{formatCurrency(revenue)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Total Expenses</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{formatCurrency(expenses)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Net Profit</h3>
          <p className={`text-2xl font-bold mt-2 ${netProfit >= 0 ? 'text-gray-900' : 'text-red-600'}`}>
            {formatCurrency(netProfit)}
          </p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Cash Position</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{formatCurrency(cashPosition)}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Journal Entries</h2>
            <Link href="/journal-entries" className="text-sm text-primary-600 hover:text-primary-900">
              View All
            </Link>
          </div>
          {recentEntries.length === 0 ? (
            <p className="text-gray-500 text-sm">No recent entries</p>
          ) : (
            <div className="space-y-3">
              {recentEntries.map((entry) => (
                <div key={entry.id} className="border-b border-gray-200 pb-3 last:border-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <Link
                        href={`/journal-entries/${entry.id}`}
                        className="text-sm font-medium text-primary-600 hover:text-primary-900"
                      >
                        {entry.entry_number}
                      </Link>
                      <p className="text-sm text-gray-500">{entry.description}</p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          entry.status === 'posted'
                            ? 'bg-green-100 text-green-800'
                            : entry.status === 'reversed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {entry.status}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">{formatDate(entry.entry_date)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <Link href="/journal-entries/new" className="btn-primary w-full block text-center">
              Create Journal Entry
            </Link>
            <Link href="/chart-of-accounts/new" className="btn-secondary w-full block text-center">
              Add Account
            </Link>
            <Link href="/periods/new" className="btn-secondary w-full block text-center">
              Create Period
            </Link>
            <Link href="/reports" className="btn-outline w-full block text-center">
              View Reports
            </Link>
          </div>
        </div>
      </div>

      {trialBalance && trialBalance.rows && trialBalance.rows.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Account Summary</h2>
            <Link href="/reports/trial-balance" className="text-sm text-primary-600 hover:text-primary-900">
              View Full Trial Balance
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-500">Total Accounts</p>
              <p className="text-lg font-semibold text-gray-900">{trialBalance.rows.length}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Debits</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(
                  trialBalance.rows.reduce((sum, row) => sum + row.debit_balance, 0)
                )}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Credits</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(
                  trialBalance.rows.reduce((sum, row) => sum + row.credit_balance, 0)
                )}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Balance</p>
              <p
                className={`text-lg font-semibold ${
                  Math.abs(
                    trialBalance.rows.reduce((sum, row) => sum + row.debit_balance, 0) -
                      trialBalance.rows.reduce((sum, row) => sum + row.credit_balance, 0)
                  ) < 0.01
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {formatCurrency(
                  trialBalance.rows.reduce((sum, row) => sum + row.debit_balance, 0) -
                    trialBalance.rows.reduce((sum, row) => sum + row.credit_balance, 0)
                )}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
