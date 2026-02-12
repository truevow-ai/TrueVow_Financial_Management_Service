'use client'

import { ReactNode } from 'react'
import { Layers } from 'lucide-react'

interface GridBulkActionsProps {
  selectedCount: number
  onApplyDimension: (dimension: 'cost_center' | 'department' | 'location', value: string) => void
  onApplyAccount?: (accountCode: string) => void
  dimensions?: Array<{ type: string; value: string }>
  accounts?: Array<{ code: string; name: string }>
  className?: string
}

/**
 * Bulk Actions Toolbar for Grids
 * Allows applying dimensions/accounts to selected rows
 * Used in: JournalEntryGrid, APBillGrid, PayrollAdjustmentsGrid
 */
export function GridBulkActions({
  selectedCount,
  onApplyDimension,
  onApplyAccount,
  dimensions = [],
  accounts = [],
  className,
}: GridBulkActionsProps) {
  if (selectedCount === 0) return null

  return (
    <div className={`flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg ${className}`}>
      <Layers className="w-4 h-4 text-blue-600" />
      <span className="text-sm font-medium text-blue-900">
        {selectedCount} row{selectedCount !== 1 ? 's' : ''} selected
      </span>
      <div className="flex items-center gap-2 ml-4">
        <span className="text-xs text-blue-700">Apply to selected:</span>
        
        {/* Cost Center */}
        {dimensions.filter((d) => d.type === 'cost_center').length > 0 && (
          <select
            onChange={(e) => {
              if (e.target.value) {
                onApplyDimension('cost_center', e.target.value)
                e.target.value = ''
              }
            }}
            className="text-xs border border-blue-300 rounded px-2 py-1 bg-white"
          >
            <option value="">Cost Center...</option>
            {dimensions
              .filter((d) => d.type === 'cost_center')
              .map((d) => (
                <option key={d.value} value={d.value}>
                  {d.value}
                </option>
              ))}
          </select>
        )}

        {/* Department */}
        {dimensions.filter((d) => d.type === 'department').length > 0 && (
          <select
            onChange={(e) => {
              if (e.target.value) {
                onApplyDimension('department', e.target.value)
                e.target.value = ''
              }
            }}
            className="text-xs border border-blue-300 rounded px-2 py-1 bg-white"
          >
            <option value="">Department...</option>
            {dimensions
              .filter((d) => d.type === 'department')
              .map((d) => (
                <option key={d.value} value={d.value}>
                  {d.value}
                </option>
              ))}
          </select>
        )}

        {/* Location */}
        {dimensions.filter((d) => d.type === 'location').length > 0 && (
          <select
            onChange={(e) => {
              if (e.target.value) {
                onApplyDimension('location', e.target.value)
                e.target.value = ''
              }
            }}
            className="text-xs border border-blue-300 rounded px-2 py-1 bg-white"
          >
            <option value="">Location...</option>
            {dimensions
              .filter((d) => d.type === 'location')
              .map((d) => (
                <option key={d.value} value={d.value}>
                  {d.value}
                </option>
              ))}
          </select>
        )}

        {/* Account (if applicable) */}
        {onApplyAccount && accounts.length > 0 && (
          <select
            onChange={(e) => {
              if (e.target.value) {
                onApplyAccount(e.target.value)
                e.target.value = ''
              }
            }}
            className="text-xs border border-blue-300 rounded px-2 py-1 bg-white"
          >
            <option value="">Account...</option>
            {accounts.map((acc) => (
              <option key={acc.code} value={acc.code}>
                {acc.code} - {acc.name}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  )
}
