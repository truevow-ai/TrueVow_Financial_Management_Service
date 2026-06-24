'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { treasuryApi } from '@/lib/api/treasuryApi'
import { formatCurrency, formatDate } from '@/lib/utils/format'
import { ReconciliationSessionGrid } from '@/components/common/ReconciliationSessionGrid'
import { ReconciliationSessionSummary } from '@/components/common/ReconciliationSessionSummary'

interface ReconciliationSessionPageProps {
  sessionId: string
  className?: string
}

/**
 * Reconciliation workspace for a single session, wired to the treasury API.
 * Workflow: review unreconciled bank transactions -> auto-match -> confirm
 * suggested matches -> complete the reconciliation.
 */
export function ReconciliationSessionPage({
  sessionId,
  className,
}: ReconciliationSessionPageProps) {
  const queryClient = useQueryClient()

  const sessionQuery = useQuery({
    queryKey: ['recon-session', sessionId],
    queryFn: () => treasuryApi.getReconciliationSession(sessionId),
    enabled: !!sessionId,
  })

  const matchesQuery = useQuery({
    queryKey: ['recon-matches', sessionId],
    queryFn: () => treasuryApi.getReconciliationMatches(sessionId),
    enabled: !!sessionId,
  })

  const bankAccountId = sessionQuery.data?.bank_account_id
  const unreconciledQuery = useQuery({
    queryKey: ['recon-unreconciled', bankAccountId],
    queryFn: () =>
      treasuryApi.getBankTransactions({
        bank_account_id: bankAccountId,
        is_reconciled: false,
      }),
    enabled: !!bankAccountId,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['recon-session', sessionId] })
    queryClient.invalidateQueries({ queryKey: ['recon-matches', sessionId] })
    queryClient.invalidateQueries({ queryKey: ['recon-unreconciled', bankAccountId] })
  }

  const autoMatchMutation = useMutation({
    mutationFn: () => treasuryApi.autoMatchReconciliation(sessionId),
    onSuccess: invalidate,
  })

  const confirmMutation = useMutation({
    mutationFn: (matchId: string) =>
      treasuryApi.confirmReconciliationMatch(sessionId, matchId),
    onSuccess: invalidate,
  })

  const completeMutation = useMutation({
    mutationFn: () => treasuryApi.completeReconciliation(sessionId),
    onSuccess: invalidate,
  })

  if (sessionQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (sessionQuery.error || !sessionQuery.data) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        Error loading reconciliation session. Please try again.
      </div>
    )
  }

  const session = sessionQuery.data
  const matches = matchesQuery.data || []
  const unreconciled = unreconciledQuery.data?.items || []
  const currency = unreconciled[0]?.currency || 'USD'
  const confirmedCount = matches.filter((m) => m.is_confirmed).length
  const isCompleted = session.status === 'completed' || session.status === 'cancelled'

  return (
    <div className={`space-y-4 ${className || ''}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reconciliation</h1>
          <p className="text-gray-600 mt-1">
            {formatDate(session.period_start)} – {formatDate(session.period_end)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => autoMatchMutation.mutate()}
            disabled={autoMatchMutation.isPending || isCompleted}
            className="btn-secondary text-sm disabled:opacity-50"
          >
            {autoMatchMutation.isPending ? 'Auto-matching…' : 'Auto-match'}
          </button>
          <button
            onClick={() => completeMutation.mutate()}
            disabled={completeMutation.isPending || isCompleted}
            className="btn-primary text-sm disabled:opacity-50"
          >
            {completeMutation.isPending ? 'Completing…' : 'Complete Reconciliation'}
          </button>
        </div>
      </div>

      <ReconciliationSessionSummary
        session={session}
        matchCount={matches.length}
        confirmedCount={confirmedCount}
        unreconciledCount={unreconciled.length}
        currency={currency}
      />

      {/* Matches */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Matches</h2>
        <ReconciliationSessionGrid
          matches={matches}
          onConfirm={(matchId) => confirmMutation.mutate(matchId)}
          confirmingId={confirmMutation.isPending ? confirmMutation.variables ?? null : null}
        />
      </div>

      {/* Unreconciled bank transactions */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Unreconciled Bank Transactions
        </h2>
        {unreconciled.length === 0 ? (
          <div className="border rounded-lg p-8 text-center text-gray-500">
            No unreconciled bank transactions.
          </div>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Reference</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {unreconciled.map((tx) => (
                  <tr key={tx.id}>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {formatDate(tx.transaction_date)}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-900">{tx.description}</td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {tx.reference_number || '-'}
                    </td>
                    <td className="px-4 py-2 text-sm text-right text-gray-900">
                      {formatCurrency(tx.amount, tx.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
