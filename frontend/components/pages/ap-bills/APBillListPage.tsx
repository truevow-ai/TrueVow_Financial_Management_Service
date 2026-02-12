'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAPBills, useAPBill } from '@/hooks/useAPBills'
import { formatDate, formatCurrency } from '@/lib/utils/format'
import { VirtualizedTableWrapper } from '@/components/common/VirtualizedTableWrapper'
import { ContextualSidebar } from '@/components/common/ContextualSidebar'
import { useListPageShortcuts } from '@/hooks/useKeyboardShortcuts'
import { useEntityBook } from '@/contexts/EntityBookContext'

export function APBillListPage() {
  const { selectedBookId } = useEntityBook()
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [vendorFilter, setVendorFilter] = useState<string>('')
  const [selectedBillId, setSelectedBillId] = useState<string | null>(null)
  
  const { data: bills, isLoading, error } = useAPBills(selectedBookId || '', {
    status: statusFilter || undefined,
    vendor_id: vendorFilter || undefined,
    enabled: !!selectedBookId,
  })
  
  const { data: selectedBill } = useAPBill(selectedBookId || '', selectedBillId || '', {
    enabled: !!selectedBookId && !!selectedBillId,
  })

  // Keyboard shortcuts
  useListPageShortcuts({
    onNew: () => {
      window.location.href = '/ap-bills/new'
    },
    onSearch: () => {
      const event = new KeyboardEvent('keydown', {
        key: 'k',
        metaKey: true,
        bubbles: true,
      })
      window.dispatchEvent(event)
    },
    enabled: true,
  })

  if (!selectedBookId) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg">
        Please select a book to view AP bills.
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

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        Error loading AP bills. Please try again.
      </div>
    )
  }

  const billsList = bills || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AP Bills</h1>
          <p className="text-gray-600 mt-1">Manage and review accounts payable bills</p>
        </div>
        <Link href="/ap-bills/new" className="btn-primary">
          Create Bill
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
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {billsList.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No AP bills found</p>
            <Link href="/ap-bills/new" className="btn-primary mt-4 inline-block">
              Create First Bill
            </Link>
          </div>
        ) : (
          <VirtualizedTableWrapper
            data={billsList}
            height={600}
            renderHeader={() => (
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bill Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Vendor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Due Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            )}
            renderRow={(bill: any) => (
              <>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {bill.invoice_number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {bill.vendor_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(bill.invoice_date)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {bill.due_date ? formatDate(bill.due_date) : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {formatCurrency(bill.total_amount || 0, bill.currency || 'USD')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      bill.status === 'posted'
                        ? 'bg-green-100 text-green-800'
                        : bill.status === 'cancelled'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {bill.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => setSelectedBillId(bill.id)}
                    className="text-primary-600 hover:text-primary-900"
                  >
                    View
                  </button>
                  {' | '}
                  <Link
                    href={`/ap-bills/${bill.id}`}
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
        isOpen={!!selectedBillId}
        onClose={() => setSelectedBillId(null)}
        title={selectedBill ? `Bill ${selectedBill.invoice_number}` : 'Bill Details'}
      >
        {selectedBill ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Bill Information</h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-xs text-gray-500">Bill Number</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {selectedBill.invoice_number}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Vendor</dt>
                  <dd className="text-sm text-gray-900">{selectedBill.vendor_id}</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Date</dt>
                  <dd className="text-sm text-gray-900">
                    {formatDate(selectedBill.invoice_date)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Due Date</dt>
                  <dd className="text-sm text-gray-900">
                    {selectedBill.due_date ? formatDate(selectedBill.due_date) : '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Total Amount</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {formatCurrency(selectedBill.total_amount || 0, selectedBill.currency || 'USD')}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Status</dt>
                  <dd className="text-sm">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        selectedBill.status === 'posted'
                          ? 'bg-green-100 text-green-800'
                          : selectedBill.status === 'cancelled'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {selectedBill.status}
                    </span>
                  </dd>
                </div>
              </dl>
            </div>

            {selectedBill.lines && selectedBill.lines.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Bill Lines</h3>
                <div className="space-y-2">
                  {selectedBill.lines.map((line: any, index: number) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{line.description}</p>
                          <p className="text-xs text-gray-500">
                            Qty: {line.quantity || 1} × {formatCurrency(line.unit_price || 0, selectedBill.currency || 'USD')}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-gray-900">
                            {formatCurrency(line.total_amount || line.line_amount || 0, selectedBill.currency || 'USD')}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-4 border-t border-gray-200">
              <Link
                href={`/ap-bills/${selectedBill.id}`}
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
