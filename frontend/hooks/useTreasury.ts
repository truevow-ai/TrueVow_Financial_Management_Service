import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  treasuryApi,
  BankAccount,
  BankTransaction,
  Transfer,
  FXConversion,
  ReconciliationSession,
  ReconciliationMatch,
  CashPosition,
  CreateBankAccountRequest,
  ImportTransactionsRequest,
  CreateTransferRequest,
  CreateFXConversionRequest,
  CreateReconciliationSessionRequest,
} from '@/lib/api/treasuryApi'

// Bank Accounts
export const useBankAccounts = (params?: { legal_entity_id?: string; is_active?: boolean }) => {
  return useQuery<BankAccount[]>({
    queryKey: ['bank-accounts', params],
    queryFn: () => treasuryApi.getBankAccounts(params),
  })
}

export const useBankAccount = (id: string) => {
  return useQuery({
    queryKey: ['bank-account', id],
    queryFn: () => treasuryApi.getBankAccount(id),
    enabled: !!id,
  })
}

export const useCreateBankAccount = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateBankAccountRequest) => treasuryApi.createBankAccount(data),
    // Optimistic update
    onMutate: async (newAccount) => {
      await queryClient.cancelQueries({ queryKey: ['bank-accounts'] })
      const previousAccounts = queryClient.getQueryData(['bank-accounts'])
      
      queryClient.setQueryData(['bank-accounts'], (old: any) => {
        const optimisticAccount = {
          id: `temp-${Date.now()}`,
          ...newAccount,
          account_number: newAccount.account_number || `BANK-TEMP-${Date.now()}`,
          is_active: true,
          created_at: new Date().toISOString(),
        }
        return old ? { ...old, items: [...(old.items || []), optimisticAccount] } : { items: [optimisticAccount] }
      })
      
      return { previousAccounts }
    },
    onError: (err, newAccount, context) => {
      if (context?.previousAccounts) {
        queryClient.setQueryData(['bank-accounts'], context.previousAccounts)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
    },
  })
}

export const useUpdateBankAccount = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateBankAccountRequest> }) =>
      treasuryApi.updateBankAccount(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['bank-accounts'] })
      await queryClient.cancelQueries({ queryKey: ['bank-account', id] })
      const previousAccounts = queryClient.getQueryData(['bank-accounts'])
      const previousAccount = queryClient.getQueryData(['bank-account', id])
      
      queryClient.setQueryData(['bank-accounts'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((acc: any) =>
            acc.id === id ? { ...acc, ...data, updated_at: new Date().toISOString() } : acc
          ),
        }
      })
      
      queryClient.setQueryData(['bank-account', id], (old: any) => {
        return old ? { ...old, ...data, updated_at: new Date().toISOString() } : old
      })
      
      return { previousAccounts, previousAccount }
    },
    onError: (err, { id }, context) => {
      if (context?.previousAccounts) {
        queryClient.setQueryData(['bank-accounts'], context.previousAccounts)
      }
      if (context?.previousAccount) {
        queryClient.setQueryData(['bank-account', id], context.previousAccount)
      }
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['bank-account', id] })
    },
  })
}

export const useDeleteBankAccount = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => treasuryApi.deleteBankAccount(id),
    // Optimistic update
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['bank-accounts'] })
      const previousAccounts = queryClient.getQueryData(['bank-accounts'])
      
      queryClient.setQueryData(['bank-accounts'], (old: any) => {
        return old ? { ...old, items: (old.items || []).filter((acc: any) => acc.id !== deletedId) } : old
      })
      
      return { previousAccounts }
    },
    onError: (err, deletedId, context) => {
      if (context?.previousAccounts) {
        queryClient.setQueryData(['bank-accounts'], context.previousAccounts)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
    },
  })
}

// Bank Transactions
export const useBankTransactions = (params?: {
  bank_account_id?: string
  is_reconciled?: boolean
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['bank-transactions', params],
    queryFn: () => treasuryApi.getBankTransactions(params),
  })
}

export const useImportBankTransactions = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ImportTransactionsRequest) => treasuryApi.importBankTransactions(data),
    onSuccess: (_, data) => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] })
      queryClient.invalidateQueries({ queryKey: ['bank-account', data.bank_account_id] })
    },
  })
}

// Transfers
export const useTransfers = (params?: {
  legal_entity_id?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['transfers', params],
    queryFn: () => treasuryApi.getTransfers(params),
  })
}

export const useTransfer = (id: string) => {
  return useQuery({
    queryKey: ['transfer', id],
    queryFn: () => treasuryApi.getTransfer(id),
    enabled: !!id,
  })
}

export const useCreateTransfer = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateTransferRequest) => treasuryApi.createTransfer(data),
    // Optimistic update
    onMutate: async (newTransfer) => {
      await queryClient.cancelQueries({ queryKey: ['transfers'] })
      await queryClient.cancelQueries({ queryKey: ['bank-accounts'] })
      const previousTransfers = queryClient.getQueryData(['transfers'])
      
      queryClient.setQueryData(['transfers'], (old: any) => {
        const optimisticTransfer = {
          id: `temp-${Date.now()}`,
          transfer_number: `TRF-TEMP-${Date.now()}`,
          status: 'pending',
          created_at: new Date().toISOString(),
          ...newTransfer,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticTransfer] } : { items: [optimisticTransfer] }
      })
      
      return { previousTransfers }
    },
    onError: (err, newTransfer, context) => {
      if (context?.previousTransfers) {
        queryClient.setQueryData(['transfers'], context.previousTransfers)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transfers'] })
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
    },
  })
}

// FX Conversions
export const useFXConversions = (params?: {
  legal_entity_id?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['fx-conversions', params],
    queryFn: () => treasuryApi.getFXConversions(params),
  })
}

export const useFXConversion = (id: string) => {
  return useQuery({
    queryKey: ['fx-conversion', id],
    queryFn: () => treasuryApi.getFXConversion(id),
    enabled: !!id,
  })
}

export const useCreateFXConversion = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateFXConversionRequest) => treasuryApi.createFXConversion(data),
    // Optimistic update
    onMutate: async (newConversion) => {
      await queryClient.cancelQueries({ queryKey: ['fx-conversions'] })
      await queryClient.cancelQueries({ queryKey: ['bank-accounts'] })
      const previousConversions = queryClient.getQueryData(['fx-conversions'])
      
      queryClient.setQueryData(['fx-conversions'], (old: any) => {
        const optimisticConversion = {
          id: `temp-${Date.now()}`,
          conversion_number: `FX-TEMP-${Date.now()}`,
          status: 'pending',
          created_at: new Date().toISOString(),
          ...newConversion,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticConversion] } : { items: [optimisticConversion] }
      })
      
      return { previousConversions }
    },
    onError: (err, newConversion, context) => {
      if (context?.previousConversions) {
        queryClient.setQueryData(['fx-conversions'], context.previousConversions)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fx-conversions'] })
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
    },
  })
}

// Reconciliation
export const useReconciliationSessions = (params?: {
  bank_account_id?: string
  status?: string
}) => {
  return useQuery({
    queryKey: ['reconciliation-sessions', params],
    queryFn: () => treasuryApi.getReconciliationSessions(params),
  })
}

export const useReconciliationSession = (id: string) => {
  return useQuery({
    queryKey: ['reconciliation-session', id],
    queryFn: () => treasuryApi.getReconciliationSession(id),
    enabled: !!id,
  })
}

export const useCreateReconciliationSession = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateReconciliationSessionRequest) => treasuryApi.createReconciliationSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation-sessions'] })
    },
  })
}

export const useReconciliationMatches = (sessionId: string) => {
  return useQuery({
    queryKey: ['reconciliation-matches', sessionId],
    queryFn: () => treasuryApi.getReconciliationMatches(sessionId),
    enabled: !!sessionId,
  })
}

export const useAutoMatchReconciliation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => treasuryApi.autoMatchReconciliation(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation-matches', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-session', sessionId] })
    },
  })
}

export const useConfirmReconciliationMatch = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sessionId, matchId }: { sessionId: string; matchId: string }) =>
      treasuryApi.confirmReconciliationMatch(sessionId, matchId),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation-matches', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-session', sessionId] })
    },
  })
}

export const useCompleteReconciliation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => treasuryApi.completeReconciliation(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['reconciliation-session', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['bank-transactions'] })
    },
  })
}

// Cash Position
export const useCashPosition = (params: { legal_entity_id: string; as_of_date?: string }) => {
  return useQuery({
    queryKey: ['cash-position', params],
    queryFn: () => treasuryApi.getCashPosition(params),
    enabled: !!params.legal_entity_id,
  })
}
