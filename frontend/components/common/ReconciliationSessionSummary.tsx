'use client'

/**
 * STUB: ReconciliationSessionSummary component
 * TODO: Implement actual reconciliation session summary
 */

interface Transaction {
  transaction_id: string
  amount: number
  currency: string
  description: string
  status: 'MATCHED' | 'UNMATCHED'
}

interface ReconciliationSession {
  session_id: string
  bank_account_id: string
  start_date: string
  end_date: string
  status: 'OPEN' | 'CLOSED' | 'RECONCILED'
  transactions: Transaction[]
}

interface ReconciliationSessionSummaryProps {
  session: ReconciliationSession
  handleTransactionStatusChange: (transactionId: string, status: 'MATCHED' | 'UNMATCHED') => void
}

export function ReconciliationSessionSummary({
  session,
  handleTransactionStatusChange,
}: ReconciliationSessionSummaryProps) {
  const matchedCount = session.transactions.filter((t) => t.status === 'MATCHED').length
  const unmatchedCount = session.transactions.filter((t) => t.status === 'UNMATCHED').length
  const totalAmount = session.transactions.reduce((sum, t) => sum + t.amount, 0)
  const matchedAmount = session.transactions
    .filter((t) => t.status === 'MATCHED')
    .reduce((sum, t) => sum + t.amount, 0)

  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-4">Session Summary</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-sm text-gray-500">Total Transactions</div>
          <div className="text-xl font-bold">{session.transactions.length}</div>
        </div>
        <div className="p-3 bg-green-50 rounded">
          <div className="text-sm text-green-600">Matched</div>
          <div className="text-xl font-bold text-green-700">{matchedCount}</div>
        </div>
        <div className="p-3 bg-yellow-50 rounded">
          <div className="text-sm text-yellow-600">Unmatched</div>
          <div className="text-xl font-bold text-yellow-700">{unmatchedCount}</div>
        </div>
        <div className="p-3 bg-blue-50 rounded">
          <div className="text-sm text-blue-600">Match Rate</div>
          <div className="text-xl font-bold text-blue-700">
            {session.transactions.length > 0
              ? Math.round((matchedCount / session.transactions.length) * 100)
              : 0}
            %
          </div>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t grid grid-cols-2 gap-4">
        <div>
          <div className="text-sm text-gray-500">Total Amount</div>
          <div className="text-lg font-semibold">
            {totalAmount.toLocaleString('en-US', {
              style: 'currency',
              currency: session.transactions[0]?.currency || 'USD',
            })}
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-500">Matched Amount</div>
          <div className="text-lg font-semibold text-green-700">
            {matchedAmount.toLocaleString('en-US', {
              style: 'currency',
              currency: session.transactions[0]?.currency || 'USD',
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
