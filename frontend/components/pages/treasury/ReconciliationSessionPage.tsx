'use client'

import { useEffect, useState, useCallback } from 'react'
import { useReconciliationSession } from '@/hooks/useTreasury'
import { formatCurrency } from '@/lib/utils/format'
import { ReconciliationSessionGrid } from '@/components/common/ReconciliationSessionGrid'
import { ReconciliationSessionSummary } from '@/components/common/ReconciliationSessionSummary'

export interface ReconciliationSession {
  session_id: string
  bank_account_id: string
  start_date: string
  end_date: string
  status: 'OPEN' | 'CLOSED' | 'RECONCILED'
  transactions: {
    transaction_id: string
    amount: number
    currency: string
    description: string
    status: 'MATCHED' | 'UNMATCHED'
  }[]
  _errors?: Record<string, string>
}

interface ReconciliationSessionPageProps {
  sessionId: string
  className?: string
}

/**
 * Reconciliation Session Page Component
 * Displays and manages a single reconciliation session
 * Supports: viewing transactions, marking matches, closing sessions
 */
export function ReconciliationSessionPage({
  sessionId,
  className,
}: ReconciliationSessionPageProps) {
  const { data: sessionData, isLoading } = useReconciliationSession(sessionId)
  const [session, setSession] = useState<ReconciliationSession | null>(null)

  // Load session data
  const loadSession = useCallback(async () => {
    if (!sessionData) return

    // sessionData is the session directly from the API
    // Cast through unknown to handle API type differences
    setSession(sessionData as unknown as ReconciliationSession)
  }, [sessionData])

  useEffect(() => {
    loadSession()
  }, [loadSession])

  // Handle transaction status change
  const handleTransactionStatusChange = useCallback(
    (transactionId: string, newStatus: 'MATCHED' | 'UNMATCHED') => {
      if (!session) return

      const updatedTransactions = session.transactions.map((tx) =>
        tx.transaction_id === transactionId ? { ...tx, status: newStatus } : tx
      )

      setSession({ ...session, transactions: updatedTransactions })
    },
    [session]
  )

  // Close session
  const closeSession = useCallback(async () => {
    if (!session || session.status !== 'OPEN') return

    // Simulate closing session (this would typically involve an API call)
    setSession({ ...session, status: 'CLOSED' })
  }, [session])

  // Reconcile session
  const reconcileSession = useCallback(async () => {
    if (!session || session.status !== 'OPEN') return

    // Simulate reconciling session (this would typically involve an API call)
    setSession({ ...session, status: 'RECONCILED' })
  }, [session])

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={closeSession} className="btn-secondary text-sm">
            Close Session
          </button>
          <button onClick={reconcileSession} className="btn-secondary text-sm">
            Reconcile Session
          </button>
        </div>
        <div className="flex items-center gap-4 text-sm">
          {session && (
            <>
              <span className="text-gray-600">
                Bank Account: <strong>{session.bank_account_id}</strong>
              </span>
              <span className="text-gray-600">
                Start Date: <strong>{session.start_date}</strong>
              </span>
              <span className="text-gray-600">
                End Date: <strong>{session.end_date}</strong>
              </span>
              <span className="text-gray-600">
                Status: <strong>{session.status}</strong>
              </span>
            </>
          )}
        </div>
      </div>

      {/* Summary */}
      {session && (
        <ReconciliationSessionSummary
          session={session}
          handleTransactionStatusChange={handleTransactionStatusChange}
        />
      )}

      {/* Grid */}
      {session && (
        <ReconciliationSessionGrid
          transactions={session.transactions}
          handleTransactionStatusChange={handleTransactionStatusChange}
        />
      )}

      {/* Footer with totals */}
      {session && (
        <div className="bg-gray-50 border-t border-gray-200 px-4 py-2 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">
              Total Transactions: <strong>{session.transactions.length}</strong>
            </span>
            <div className="flex gap-4">
              <span className="font-semibold text-gray-900">
                Total Amount: {formatCurrency(session.transactions.reduce((sum, tx) => sum + tx.amount, 0), session.transactions[0]?.currency || 'USD')}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}