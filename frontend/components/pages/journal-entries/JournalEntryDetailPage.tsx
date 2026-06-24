'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { glApi } from '@/lib/api/glApi'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { formatCurrency, formatDate } from '@/lib/utils/format'

const STATUS_STYLES: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  posted: 'bg-green-100 text-green-700',
  reversed: 'bg-red-100 text-red-700',
}

export function JournalEntryDetailPage() {
  const params = useParams()
  const id = (Array.isArray(params?.id) ? params.id[0] : params?.id) || ''
  const { selectedBookId } = useEntityBook()
  const bookId = selectedBookId || ''

  const { data: entry, isLoading, error } = useQuery({
    queryKey: ['journal-entry', bookId, id],
    queryFn: () => glApi.getJournalEntry(bookId, id),
    enabled: !!bookId && !!id,
  })

  if (!bookId) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg">
        Select an entity and book to view this journal entry.
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !entry) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        Error loading journal entry. Please try again.
      </div>
    )
  }

  const totalDebit = entry.lines.reduce((sum, l) => sum + (l.debit_amount || 0), 0)
  const totalCredit = entry.lines.reduce((sum, l) => sum + (l.credit_amount || 0), 0)
  const balanced = Math.abs(totalDebit - totalCredit) < 0.01
  const statusKey = (entry.status || '').toLowerCase()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/journal-entries" className="text-sm text-primary-600 hover:underline">
            ← Back to Journal Entries
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{entry.entry_number}</h1>
          <p className="text-gray-600 mt-1">{entry.description}</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-sm font-medium ${
            STATUS_STYLES[statusKey] || 'bg-gray-100 text-gray-700'
          }`}
        >
          {entry.status}
        </span>
      </div>

      {/* Header detail */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Entry Date</h3>
          <p className="text-lg font-medium text-gray-900">{formatDate(entry.entry_date)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Debits</h3>
          <p className="text-lg font-medium text-gray-900">{formatCurrency(totalDebit)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Credits</h3>
          <p className="text-lg font-medium text-gray-900">{formatCurrency(totalCredit)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Balanced</h3>
          <p className={`text-lg font-bold ${balanced ? 'text-green-600' : 'text-red-600'}`}>
            {balanced ? 'Yes' : 'No'}
          </p>
        </div>
      </div>

      {entry.reversal_entry_id && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          This entry was reversed.{' '}
          <Link
            href={`/journal-entries/${entry.reversal_entry_id}`}
            className="font-medium underline"
          >
            View reversal entry
          </Link>
        </div>
      )}

      {/* Lines */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Lines</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debit</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Credit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {entry.lines
                .slice()
                .sort((a, b) => a.line_number - b.line_number)
                .map((line) => (
                  <tr key={line.id}>
                    <td className="px-4 py-3 text-sm text-gray-500">{line.line_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{line.gl_account_id}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{line.description || '-'}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">
                      {line.debit_amount ? formatCurrency(line.debit_amount) : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">
                      {line.credit_amount ? formatCurrency(line.credit_amount) : '-'}
                    </td>
                  </tr>
                ))}
            </tbody>
            <tfoot>
              <tr className="bg-gray-50 font-bold">
                <td className="px-4 py-3 text-sm text-gray-900" colSpan={3}>
                  Total
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {formatCurrency(totalDebit)}
                </td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {formatCurrency(totalCredit)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  )
}
