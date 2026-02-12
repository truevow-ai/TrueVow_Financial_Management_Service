'use client'

/**
 * STUB: ReconciliationSessionGrid component
 * TODO: Implement actual reconciliation transaction grid
 */

interface Transaction {
  transaction_id: string
  amount: number
  currency: string
  description: string
  status: 'MATCHED' | 'UNMATCHED'
}

interface ReconciliationSessionGridProps {
  transactions: Transaction[]
  handleTransactionStatusChange: (transactionId: string, status: 'MATCHED' | 'UNMATCHED') => void
}

export function ReconciliationSessionGrid({
  transactions,
  handleTransactionStatusChange,
}: ReconciliationSessionGridProps) {
  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
            <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {transactions.map((tx) => (
            <tr key={tx.transaction_id}>
              <td className="px-4 py-2 text-sm text-gray-900">{tx.transaction_id}</td>
              <td className="px-4 py-2 text-sm text-gray-900">{tx.description}</td>
              <td className="px-4 py-2 text-sm text-gray-900 text-right">
                {tx.amount.toLocaleString('en-US', { style: 'currency', currency: tx.currency })}
              </td>
              <td className="px-4 py-2 text-center">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    tx.status === 'MATCHED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {tx.status}
                </span>
              </td>
              <td className="px-4 py-2 text-center">
                <button
                  onClick={() =>
                    handleTransactionStatusChange(tx.transaction_id, tx.status === 'MATCHED' ? 'UNMATCHED' : 'MATCHED')
                  }
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Toggle
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
