"use client"

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useClerkToken } from './useClerkToken'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { apApi, APInvoice, CreateAPInvoiceRequest } from '@/lib/api/apApi'

// AP Bills Hooks
export const useAPBills = (
  bookId: string,
  options?: {
    vendor_id?: string
    status?: string
    enabled?: boolean
  }
) => {
  return useQuery({
    queryKey: ['ap-bills', bookId, options],
    queryFn: () => apApi.getAPBills(bookId, options),
    enabled: !!bookId && (options?.enabled !== false),
  })
}

export const useAPBill = (bookId: string, billId: string, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: ['ap-bill', bookId, billId],
    queryFn: () => apApi.getAPBill(bookId, billId),
    enabled: !!bookId && !!billId && (options?.enabled !== false),
  })
}

export const useCreateAPBill = () => {
  const queryClient = useQueryClient()
  const { selectedBookId } = useEntityBook()
  const { getToken } = useClerkToken()

  return useMutation({
    mutationFn: async (data: CreateAPInvoiceRequest) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return apApi.createAPBill(selectedBookId, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ap-bills'] })
    },
  })
}

export const useUpdateAPBill = () => {
  const queryClient = useQueryClient()
  const { selectedBookId } = useEntityBook()

  return useMutation({
    mutationFn: async ({ billId, data }: { billId: string; data: Partial<CreateAPInvoiceRequest> }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return apApi.updateAPBill(selectedBookId, billId, data)
    },
    onSuccess: (_, { billId }) => {
      queryClient.invalidateQueries({ queryKey: ['ap-bill', selectedBookId, billId] })
      queryClient.invalidateQueries({ queryKey: ['ap-bills'] })
    },
  })
}
