'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useJournalEntries, useJournalEntry } from '@/hooks/useJournalEntries'
import { formatDate, formatCurrency } from '@/lib/utils/format'
import { VirtualizedTableWrapper } from '@/components/common/VirtualizedTableWrapper'
import { ContextualSidebar } from '@/components/common/ContextualSidebar'
import { useListPageShortcuts } from '@/hooks/useKeyboardShortcuts'

export function JournalEntryListPage() {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null)
  const { data, isLoading, error } = useJournalEntries({
    status: statusFilter || undefined,
  })
  const { data: selectedEntry } = useJournalEntry(selectedEntryId || '', {
    enabled: !!selectedEntryId,
  })

  // Keyboard shortcuts
  useListPageShortcuts({
    onNew: () => {
      window.location.href = '/journal-entries/new'
    },
    onSearch: () => {
      // Trigger global search
      const event = new KeyboardEvent('keydown', {
        key: 'k',
        metaKey: true,
        bubbles: true,
      })
      window.dispatchEvent(event)
    },
    enabled: true,
  })

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
        Error loading journal entries. Please try again.
      </div>
    )
  }

  const entries = data?.items || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Journal Entries</h1>
          <p className="text-gray-600 mt-1">Manage and review journal entries</p>
        </div>
        <Link href="/journal-entries/new" className="btn-primary">
          Create Entry
        </Link>
      </div>

      <div className="card">
        <div className="flex items-center gap-4 mb-4">
          <label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
            Filter by Status:
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input"
          >
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="posted">Posted</option>
            <option value="reversed">Reversed</option>
          </select>
        </div>

        {entries.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No journal entries found</p>
            <Link href="/journal-entries/new" className="btn-primary mt-4 inline-block">
              Create First Entry
            </Link>
          </div>
        ) : (
          <VirtualizedTableWrapper
            data={entries}
            height={600}
            renderHeader={() => (
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entry Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lines
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            )}
            renderRow={(entry) => (
              <>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {entry.entry_number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(entry.entry_date)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{entry.description}</td>
                <td className="px-6 py-4 whitespace-nowrap">
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
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {entry.lines?.length || 0}
                </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => setSelectedEntryId(entry.id)}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        View
                      </button>
                      {' | '}
                      <Link
                        href={`/journal-entries/${entry.id}`}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        Details
                      </Link>
                    </td>
              </>
            )}
            estimateSize={() => 60}
          />
        )}
      </div>

      {/* Contextual Sidebar */}
      <ContextualSidebar
        isOpen={!!selectedEntryId}
        onClose={() => setSelectedEntryId(null)}
        title={selectedEntry ? `Entry ${selectedEntry.entry_number}` : 'Entry Details'}
      >
        {selectedEntry ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Entry Information</h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-xs text-gray-500">Entry Number</dt>
                  <dd className="text-sm font-medium text-gray-900">{selectedEntry.entry_number}</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Date</dt>
                  <dd className="text-sm text-gray-900">{formatDate(selectedEntry.entry_date)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Status</dt>
                  <dd className="text-sm">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        selectedEntry.status === 'posted'
                          ? 'bg-green-100 text-green-800'
                          : selectedEntry.status === 'reversed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {selectedEntry.status}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Description</dt>
                  <dd className="text-sm text-gray-900">{selectedEntry.description}</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Lines</dt>
                  <dd className="text-sm text-gray-900">{selectedEntry.lines?.length || 0}</dd>
                </div>
              </dl>
            </div>

            {selectedEntry.lines && selectedEntry.lines.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Journal Lines</h3>
                <div className="space-y-2">
                  {selectedEntry.lines.map((line: any, index: number) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{line.account_code}</p>
                          <p className="text-xs text-gray-500">{line.description}</p>
                        </div>
                        <div className="text-right">
                          {line.debit_amount > 0 && (
                            <p className="text-sm font-semibold text-gray-900">
                              {formatCurrency(line.debit_amount)}
                            </p>
                          )}
                          {line.credit_amount > 0 && (
                            <p className="text-sm font-semibold text-gray-900">
                              {formatCurrency(line.credit_amount)}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-4 border-t border-gray-200">
              <Link
                href={`/journal-entries/${selectedEntry.id}`}
                className="btn-primary w-full text-center"
              >
                View Full Details
              </Link>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        )}
      </ContextualSidebar>
    </div>
  )
}
