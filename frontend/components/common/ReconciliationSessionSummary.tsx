'use client'

import { ReconciliationSession } from '@/lib/api/treasuryApi'
import { formatCurrency } from '@/lib/utils/format'

interface ReconciliationSessionSummaryProps {
  session: ReconciliationSession
  matchCount: number
  confirmedCount: number
  unreconciledCount: number
  currency?: string
}

const STATUS_STYLES: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
}

export function ReconciliationSessionSummary({
  session,
  matchCount,
  confirmedCount,
  unreconciledCount,
  currency = 'USD',
}: ReconciliationSessionSummaryProps) {
  const difference = session.statement_balance - session.reconciled_balance
  const isReconciled = Math.abs(difference) < 0.01

  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Session Summary</h3>
        <span
          className={`rounded-full px-3 py-1 text-sm font-medium ${
            STATUS_STYLES[session.status] || 'bg-gray-100 text-gray-700'
          }`}
        >
          {session.status}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Statement Balance</div>
          <div className="text-xl font-bold">
            {formatCurrency(session.statement_balance, currency)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Book Balance</div>
          <div className="text-xl font-bold">
            {formatCurrency(session.book_balance, currency)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Reconciled Balance</div>
          <div className="text-xl font-bold">
            {formatCurrency(session.reconciled_balance, currency)}
          </div>
        </div>
        <div className={`p-3 rounded ${isReconciled ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className={`text-sm ${isReconciled ? 'text-green-600' : 'text-red-600'}`}>
            Difference
          </div>
          <div className={`text-xl font-bold ${isReconciled ? 'text-green-700' : 'text-red-700'}`}>
            {formatCurrency(difference, currency)}
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t grid grid-cols-3 gap-4">
        <div>
          <div className="text-sm text-gray-500">Matches</div>
          <div className="text-lg font-semibold">{matchCount}</div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Confirmed</div>
          <div className="text-lg font-semibold text-green-700">{confirmedCount}</div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Unreconciled Bank Txns</div>
          <div className="text-lg font-semibold text-yellow-700">{unreconciledCount}</div>
        </div>
      </div>
    </div>
  )
}
