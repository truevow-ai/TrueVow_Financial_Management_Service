'use client'

import { useToast } from './useToast'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'

// Generic company operation hook with automatic toast notifications
export function useCompanyOperation<TData = unknown, TVariables = void>({
  operationName,
  mutationFn,
  entityName,
  successMessage,
  errorMessage,
  invalidateKeys,
}: {
  operationName: string
  mutationFn: (variables: TVariables) => Promise<TData>
  entityName: string
  successMessage?: string
  errorMessage?: string
  invalidateKeys?: string[][]
}) {
  const { success, error } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn,
    onSuccess: (data, variables) => {
      // Show success toast
      const defaultMessage = successMessage || `${entityName} ${operationName.toLowerCase()} successful`
      success(defaultMessage)
      
      // Invalidate related queries
      if (invalidateKeys) {
        invalidateKeys.forEach(key => {
          queryClient.invalidateQueries({ queryKey: key })
        })
      }
    },
    onError: (err: Error, variables) => {
      // Show error toast
      const defaultMessage = errorMessage || `Failed to ${operationName.toLowerCase()} ${entityName}: ${err.message}`
      error(defaultMessage)
    },
  })
}

// Specific hooks for common company operations

export function useCreateEntity<TEntity>({ 
  entityName,
  endpoint,
  invalidateKeys
}: {
  entityName: string
  endpoint: string
  invalidateKeys?: string[][]
}) {
  return useCompanyOperation({
    operationName: 'Created',
    entityName,
    mutationFn: async (data: TEntity) => {
      const response = await apiClient.post(endpoint, data)
      return response.data
    },
    invalidateKeys,
  })
}

export function useUpdateEntity<TEntity>({ 
  entityName,
  endpoint,
  invalidateKeys
}: {
  entityName: string
  endpoint: string
  invalidateKeys?: string[][]
}) {
  return useCompanyOperation({
    operationName: 'Updated',
    entityName,
    mutationFn: async ({ id, data }: { id: string; data: TEntity }) => {
      const response = await apiClient.put(`${endpoint}/${id}`, data)
      return response.data
    },
    invalidateKeys,
  })
}

export function useDeleteEntity({ 
  entityName,
  endpoint,
  invalidateKeys
}: {
  entityName: string
  endpoint: string
  invalidateKeys?: string[][]
}) {
  return useCompanyOperation({
    operationName: 'Deleted',
    entityName,
    mutationFn: async (id: string) => {
      const response = await apiClient.delete(`${endpoint}/${id}`)
      return response.data
    },
    invalidateKeys,
  })
}

export function useSyncEntity({ 
  entityName,
  endpoint,
  invalidateKeys
}: {
  entityName: string
  endpoint: string
  invalidateKeys?: string[][]
}) {
  return useCompanyOperation({
    operationName: 'Synced',
    entityName,
    mutationFn: async (params?: Record<string, any>) => {
      const response = await apiClient.post(`${endpoint}/sync`, params)
      return response.data
    },
    invalidateKeys,
  })
}

export function useApproveEntity({ 
  entityName,
  endpoint,
  invalidateKeys
}: {
  entityName: string
  endpoint: string
  invalidateKeys?: string[][]
}) {
  return useCompanyOperation({
    operationName: 'Approved',
    entityName,
    mutationFn: async ({ id, data }: { id: string; data?: Record<string, any> }) => {
      const response = await apiClient.post(`${endpoint}/${id}/approve`, data)
      return response.data
    },
    invalidateKeys,
  })
}

export function useRejectEntity({ 
  entityName,
  endpoint,
  invalidateKeys
}: {
  entityName: string
  endpoint: string
  invalidateKeys?: string[][]
}) {
  return useCompanyOperation({
    operationName: 'Rejected',
    entityName,
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      const response = await apiClient.post(`${endpoint}/${id}/reject`, { reason })
      return response.data
    },
    invalidateKeys,
  })
}

// Pre-built hooks for common financial entities

export function useCreateJournalEntry() {
  return useCreateEntity({
    entityName: 'Journal Entry',
    endpoint: '/fm/journal-entries',
    invalidateKeys: [['journal-entries']],
  })
}

export function useUpdateJournalEntry() {
  return useUpdateEntity({
    entityName: 'Journal Entry',
    endpoint: '/fm/journal-entries',
    invalidateKeys: [['journal-entries'], ['trial-balance']],
  })
}

export function useDeleteJournalEntry() {
  return useDeleteEntity({
    entityName: 'Journal Entry',
    endpoint: '/fm/journal-entries',
    invalidateKeys: [['journal-entries'], ['trial-balance']],
  })
}

export function useCreateCustomer() {
  return useCreateEntity({
    entityName: 'Customer',
    endpoint: '/fm/ar/customers',
    invalidateKeys: [['customers'], ['ar-summary']],
  })
}

export function useUpdateCustomer() {
  return useUpdateEntity({
    entityName: 'Customer',
    endpoint: '/fm/ar/customers',
    invalidateKeys: [['customers'], ['ar-summary']],
  })
}

export function useSyncBillingData() {
  return useSyncEntity({
    entityName: 'Billing Data',
    endpoint: '/fm/ar',
    invalidateKeys: [['customers'], ['invoices'], ['ar-summary']],
  })
}

export function useApproveAPBill() {
  return useApproveEntity({
    entityName: 'AP Bill',
    endpoint: '/fm/ap/bills',
    invalidateKeys: [['ap-bills'], ['vendor-balances']],
  })
}

export function useRejectAPBill() {
  return useRejectEntity({
    entityName: 'AP Bill',
    endpoint: '/fm/ap/bills',
    invalidateKeys: [['ap-bills']],
  })
}