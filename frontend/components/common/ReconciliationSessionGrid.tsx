'use client'

import { ReconciliationMatch } from '@/lib/api/treasuryApi'

interface ReconciliationSessionGridProps {
  matches: ReconciliationMatch[]
  onConfirm: (matchId: string) => void
  confirmingId?: string | null
}

const MATCH_TYPE_STYLES: Record<string, string> = {
  exact: 'bg-green-100 text-green-800',
  fuzzy: 'bg-yellow-100 text-yellow-800',
  manual: 'bg-blue-100 text-blue-800',
}

export function ReconciliationSessionGrid({
  matches,
  onConfirm,
  confirmingId,
}: ReconciliationSessionGridProps) {
  if (matches.length === 0) {
    return (
      <div className="border rounded-lg p-8 text-center text-gray-500">
        No matches yet. Run auto-match to generate suggestions.
      </div>
    )
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Bank Txn</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Journal Entry</th>
            <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Type</th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Confidence</th>
            <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Confirmed</th>
            <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Action</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {matches.map((m) => (
            <tr key={m.id}>
              <td className="px-4 py-2 text-sm text-gray-900 font-mono">{m.bank_transaction_id}</td>
              <td className="px-4 py-2 text-sm text-gray-900 font-mono">{m.journal_entry_id}</td>
              <td className="px-4 py-2 text-center">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    MATCH_TYPE_STYLES[m.match_type] || 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {m.match_type}
                </span>
              </td>
              <td className="px-4 py-2 text-sm text-right text-gray-900">
                {m.confidence_score != null ? `${Math.round(m.confidence_score * 100)}%` : '-'}
              </td>
              <td className="px-4 py-2 text-center">
                {m.is_confirmed ? (
                  <span className="text-green-600 font-medium">Yes</span>
                ) : (
                  <span className="text-gray-400">No</span>
                )}
              </td>
              <td className="px-4 py-2 text-center">
                {m.is_confirmed ? (
                  <span className="text-xs text-gray-400">—</span>
                ) : (
                  <button
                    onClick={() => onConfirm(m.id)}
                    disabled={confirmingId === m.id}
                    className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
                  >
                    {confirmingId === m.id ? 'Confirming…' : 'Confirm'}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
