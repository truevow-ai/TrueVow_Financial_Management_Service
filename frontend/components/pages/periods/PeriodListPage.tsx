'use client'

import Link from 'next/link'
import { usePeriods, useClosePeriod, useLockPeriod } from '@/hooks/usePeriods'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { formatDate } from '@/lib/utils/format'

const STATUS_STYLES: Record<string, string> = {
  open: 'bg-green-100 text-green-800',
  closed: 'bg-yellow-100 text-yellow-800',
  locked: 'bg-gray-200 text-gray-700',
}

export function PeriodListPage() {
  const { selectedEntityId, selectedBookId } = useEntityBook()
  const hasSelection = !!selectedEntityId && !!selectedBookId

  const { data, isLoading, error } = usePeriods(
    hasSelection
      ? { legal_entity_id: selectedEntityId, book_id: selectedBookId }
      : undefined
  )
  const closeMutation = useClosePeriod()
  const lockMutation = useLockPeriod()

  const closingId = closeMutation.isPending ? closeMutation.variables : null
  const lockingId = lockMutation.isPending ? lockMutation.variables : null

  const handleClose = (id: string, name: string) => {
    if (window.confirm(`Close period "${name}"? Postings will require an elevated role afterwards.`)) {
      closeMutation.mutate(id)
    }
  }

  const handleLock = (id: string, name: string) => {
    if (window.confirm(`Lock period "${name}"? This permanently blocks postings to it.`)) {
      lockMutation.mutate(id)
    }
  }

  const periods = data || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Accounting Periods</h1>
          <p className="text-gray-600 mt-1">Open, close and lock periods for month-end control</p>
        </div>
        <Link href="/periods/new" className="btn-primary text-sm">
          New Period
        </Link>
      </div>

      {!hasSelection ? (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg">
          Select an entity and book to view periods.
        </div>
      ) : isLoading ? (
        <div className="flex items-center justify-center min-h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          Error loading periods. Please try again.
        </div>
      ) : (
        <div className="card">
          {periods.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No periods yet. Create one to begin.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Period</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">End</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {periods.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{p.period_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{formatDate(p.start_date)}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{formatDate(p.end_date)}</td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            STATUS_STYLES[p.status] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right space-x-3">
                        {p.status === 'open' && (
                          <button
                            onClick={() => handleClose(p.id, p.period_name)}
                            disabled={closingId === p.id}
                            className="text-sm text-yellow-700 hover:text-yellow-900 disabled:opacity-50"
                          >
                            {closingId === p.id ? 'Closing…' : 'Close'}
                          </button>
                        )}
                        {p.status === 'closed' && (
                          <button
                            onClick={() => handleLock(p.id, p.period_name)}
                            disabled={lockingId === p.id}
                            className="text-sm text-gray-700 hover:text-gray-900 disabled:opacity-50"
                          >
                            {lockingId === p.id ? 'Locking…' : 'Lock'}
                          </button>
                        )}
                        {p.status === 'locked' && <span className="text-xs text-gray-400">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
