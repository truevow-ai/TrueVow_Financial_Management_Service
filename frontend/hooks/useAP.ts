import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  apApi,
  APVendor,
  APInvoice,
  APPayment,
  CreateAPVendorRequest,
  CreateAPInvoiceRequest,
  CreateAPPaymentRequest,
} from '@/lib/api/apApi'

// AP Vendors
export const useAPVendors = (params?: { legal_entity_id?: string; is_active?: boolean }) => {
  return useQuery({
    queryKey: ['ap-vendors', params],
    queryFn: () => apApi.getAPVendors(params),
  })
}

export const useAPVendor = (id: string) => {
  return useQuery({
    queryKey: ['ap-vendor', id],
    queryFn: () => apApi.getAPVendor(id),
    enabled: !!id,
  })
}

export const useCreateAPVendor = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateAPVendorRequest) => apApi.createAPVendor(data),
    // Optimistic update
    onMutate: async (newVendor) => {
      await queryClient.cancelQueries({ queryKey: ['ap-vendors'] })
      const previousVendors = queryClient.getQueryData(['ap-vendors'])
      
      queryClient.setQueryData(['ap-vendors'], (old: any) => {
        const optimisticVendor = {
          id: `temp-${Date.now()}`,
          created_at: new Date().toISOString(),
          ...newVendor,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticVendor] } : { items: [optimisticVendor] }
      })
      
      return { previousVendors }
    },
    onError: (err, newVendor, context) => {
      if (context?.previousVendors) {
        queryClient.setQueryData(['ap-vendors'], context.previousVendors)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ap-vendors'] })
    },
  })
}

export const useUpdateAPVendor = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateAPVendorRequest> }) =>
      apApi.updateAPVendor(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['ap-vendors'] })
      await queryClient.cancelQueries({ queryKey: ['ap-vendor', id] })
      const previousVendors = queryClient.getQueryData(['ap-vendors'])
      const previousVendor = queryClient.getQueryData(['ap-vendor', id])
      
      queryClient.setQueryData(['ap-vendors'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((vend: any) =>
            vend.id === id ? { ...vend, ...data, updated_at: new Date().toISOString() } : vend
          ),
        }
      })
      
      queryClient.setQueryData(['ap-vendor', id], (old: any) => {
        return old ? { ...old, ...data, updated_at: new Date().toISOString() } : old
      })
      
      return { previousVendors, previousVendor }
    },
    onError: (err, { id }, context) => {
      if (context?.previousVendors) {
        queryClient.setQueryData(['ap-vendors'], context.previousVendors)
      }
      if (context?.previousVendor) {
        queryClient.setQueryData(['ap-vendor', id], context.previousVendor)
      }
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['ap-vendors'] })
      queryClient.invalidateQueries({ queryKey: ['ap-vendor', id] })
    },
  })
}

export const useDeleteAPVendor = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apApi.deleteAPVendor(id),
    // Optimistic update
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['ap-vendors'] })
      const previousVendors = queryClient.getQueryData(['ap-vendors'])
      
      queryClient.setQueryData(['ap-vendors'], (old: any) => {
        return old ? { ...old, items: (old.items || []).filter((vend: any) => vend.id !== deletedId) } : old
      })
      
      return { previousVendors }
    },
    onError: (err, deletedId, context) => {
      if (context?.previousVendors) {
        queryClient.setQueryData(['ap-vendors'], context.previousVendors)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ap-vendors'] })
    },
  })
}

// AP Invoices
export const useAPInvoices = (params?: {
  legal_entity_id?: string
  vendor_id?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['ap-invoices', params],
    queryFn: () => apApi.getAPInvoices(params),
  })
}

export const useAPInvoice = (id: string) => {
  return useQuery({
    queryKey: ['ap-invoice', id],
    queryFn: () => apApi.getAPInvoice(id),
    enabled: !!id,
  })
}

export const useCreateAPInvoice = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateAPInvoiceRequest) => apApi.createAPInvoice(data),
    // Optimistic update
    onMutate: async (newInvoice) => {
      await queryClient.cancelQueries({ queryKey: ['ap-invoices'] })
      const previousInvoices = queryClient.getQueryData(['ap-invoices'])
      
      queryClient.setQueryData(['ap-invoices'], (old: any) => {
        const optimisticInvoice = {
          id: `temp-${Date.now()}`,
          invoice_number: `BILL-TEMP-${Date.now()}`,
          status: 'draft',
          created_at: new Date().toISOString(),
          ...newInvoice,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticInvoice] } : { items: [optimisticInvoice] }
      })
      
      return { previousInvoices }
    },
    onError: (err, newInvoice, context) => {
      if (context?.previousInvoices) {
        queryClient.setQueryData(['ap-invoices'], context.previousInvoices)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ap-invoices'] })
    },
  })
}

export const usePostAPInvoice = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apApi.postAPInvoice(id),
    // Optimistic update
    onMutate: async (invoiceId) => {
      await queryClient.cancelQueries({ queryKey: ['ap-invoices'] })
      await queryClient.cancelQueries({ queryKey: ['ap-invoice', invoiceId] })
      const previousInvoices = queryClient.getQueryData(['ap-invoices'])
      const previousInvoice = queryClient.getQueryData(['ap-invoice', invoiceId])
      
      queryClient.setQueryData(['ap-invoices'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((inv: any) =>
            inv.id === invoiceId ? { ...inv, status: 'posted', posted_at: new Date().toISOString() } : inv
          ),
        }
      })
      
      queryClient.setQueryData(['ap-invoice', invoiceId], (old: any) => {
        return old ? { ...old, status: 'posted', posted_at: new Date().toISOString() } : old
      })
      
      return { previousInvoices, previousInvoice }
    },
    onError: (err, invoiceId, context) => {
      if (context?.previousInvoices) {
        queryClient.setQueryData(['ap-invoices'], context.previousInvoices)
      }
      if (context?.previousInvoice) {
        queryClient.setQueryData(['ap-invoice', invoiceId], context.previousInvoice)
      }
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['ap-invoices'] })
      queryClient.invalidateQueries({ queryKey: ['ap-invoice', id] })
    },
  })
}

// AP Payments
export const useAPPayments = (params?: {
  legal_entity_id?: string
  vendor_id?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['ap-payments', params],
    queryFn: () => apApi.getAPPayments(params),
  })
}

export const useAPPayment = (id: string) => {
  return useQuery({
    queryKey: ['ap-payment', id],
    queryFn: () => apApi.getAPPayment(id),
    enabled: !!id,
  })
}

export const useCreateAPPayment = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateAPPaymentRequest) => apApi.createAPPayment(data),
    // Optimistic update
    onMutate: async (newPayment) => {
      await queryClient.cancelQueries({ queryKey: ['ap-payments'] })
      await queryClient.cancelQueries({ queryKey: ['ap-invoices'] })
      const previousPayments = queryClient.getQueryData(['ap-payments'])
      const previousInvoices = queryClient.getQueryData(['ap-invoices'])
      
      queryClient.setQueryData(['ap-payments'], (old: any) => {
        const optimisticPayment = {
          id: `temp-${Date.now()}`,
          payment_number: `PAY-TEMP-${Date.now()}`,
          created_at: new Date().toISOString(),
          ...newPayment,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticPayment] } : { items: [optimisticPayment] }
      })
      
      return { previousPayments, previousInvoices }
    },
    onError: (err, newPayment, context) => {
      if (context?.previousPayments) {
        queryClient.setQueryData(['ap-payments'], context.previousPayments)
      }
      if (context?.previousInvoices) {
        queryClient.setQueryData(['ap-invoices'], context.previousInvoices)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ap-payments'] })
      queryClient.invalidateQueries({ queryKey: ['ap-invoices'] })
    },
  })
}

// AP Aging
export const useAPAging = (params: { legal_entity_id: string; as_of_date: string }) => {
  return useQuery({
    queryKey: ['ap-aging', params],
    queryFn: () => apApi.getAPAging(params),
    enabled: !!params.legal_entity_id && !!params.as_of_date,
  })
}
