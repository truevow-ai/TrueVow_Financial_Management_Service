import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  arApi,
  ARCustomer,
  ARInvoice,
  ARPayment,
  RevenueSchedule,
  CreateARCustomerRequest,
  CreateARInvoiceRequest,
  CreateARPaymentRequest,
} from '@/lib/api/arApi'

// AR Customers
export const useARCustomers = (params?: { legal_entity_id?: string; is_active?: boolean }) => {
  return useQuery({
    queryKey: ['ar-customers', params],
    queryFn: () => arApi.getARCustomers(params),
  })
}

export const useARCustomer = (id: string) => {
  return useQuery({
    queryKey: ['ar-customer', id],
    queryFn: () => arApi.getARCustomer(id),
    enabled: !!id,
  })
}

export const useCreateARCustomer = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateARCustomerRequest) => arApi.createARCustomer(data),
    // Optimistic update
    onMutate: async (newCustomer) => {
      await queryClient.cancelQueries({ queryKey: ['ar-customers'] })
      const previousCustomers = queryClient.getQueryData(['ar-customers'])
      
      queryClient.setQueryData(['ar-customers'], (old: any) => {
        const optimisticCustomer = {
          id: `temp-${Date.now()}`,
          customer_number: `CUST-TEMP-${Date.now()}`,
          ...newCustomer,
          is_active: true,
          created_at: new Date().toISOString(),
        }
        return old ? { ...old, items: [...(old.items || []), optimisticCustomer] } : { items: [optimisticCustomer] }
      })
      
      return { previousCustomers }
    },
    onError: (err, newCustomer, context) => {
      if (context?.previousCustomers) {
        queryClient.setQueryData(['ar-customers'], context.previousCustomers)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ar-customers'] })
    },
  })
}

export const useUpdateARCustomer = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateARCustomerRequest> }) =>
      arApi.updateARCustomer(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['ar-customers'] })
      await queryClient.cancelQueries({ queryKey: ['ar-customer', id] })
      const previousCustomers = queryClient.getQueryData(['ar-customers'])
      const previousCustomer = queryClient.getQueryData(['ar-customer', id])
      
      queryClient.setQueryData(['ar-customers'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((cust: any) =>
            cust.id === id ? { ...cust, ...data, updated_at: new Date().toISOString() } : cust
          ),
        }
      })
      
      queryClient.setQueryData(['ar-customer', id], (old: any) => {
        return old ? { ...old, ...data, updated_at: new Date().toISOString() } : old
      })
      
      return { previousCustomers, previousCustomer }
    },
    onError: (err, { id }, context) => {
      if (context?.previousCustomers) {
        queryClient.setQueryData(['ar-customers'], context.previousCustomers)
      }
      if (context?.previousCustomer) {
        queryClient.setQueryData(['ar-customer', id], context.previousCustomer)
      }
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['ar-customers'] })
      queryClient.invalidateQueries({ queryKey: ['ar-customer', id] })
    },
  })
}

export const useDeleteARCustomer = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => arApi.deleteARCustomer(id),
    // Optimistic update
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['ar-customers'] })
      const previousCustomers = queryClient.getQueryData(['ar-customers'])
      
      queryClient.setQueryData(['ar-customers'], (old: any) => {
        return old ? { ...old, items: (old.items || []).filter((cust: any) => cust.id !== deletedId) } : old
      })
      
      return { previousCustomers }
    },
    onError: (err, deletedId, context) => {
      if (context?.previousCustomers) {
        queryClient.setQueryData(['ar-customers'], context.previousCustomers)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ar-customers'] })
    },
  })
}

// AR Invoices
export const useARInvoices = (params?: {
  legal_entity_id?: string
  customer_id?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['ar-invoices', params],
    queryFn: () => arApi.getARInvoices(params),
  })
}

export const useARInvoice = (id: string) => {
  return useQuery({
    queryKey: ['ar-invoice', id],
    queryFn: () => arApi.getARInvoice(id),
    enabled: !!id,
  })
}

export const useCreateARInvoice = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateARInvoiceRequest) => arApi.createARInvoice(data),
    // Optimistic update
    onMutate: async (newInvoice) => {
      await queryClient.cancelQueries({ queryKey: ['ar-invoices'] })
      const previousInvoices = queryClient.getQueryData(['ar-invoices'])
      
      queryClient.setQueryData(['ar-invoices'], (old: any) => {
        const optimisticInvoice = {
          id: `temp-${Date.now()}`,
          invoice_number: `INV-TEMP-${Date.now()}`,
          ...newInvoice,
          status: 'draft',
          created_at: new Date().toISOString(),
        }
        return old ? { ...old, items: [...(old.items || []), optimisticInvoice] } : { items: [optimisticInvoice] }
      })
      
      return { previousInvoices }
    },
    onError: (err, newInvoice, context) => {
      if (context?.previousInvoices) {
        queryClient.setQueryData(['ar-invoices'], context.previousInvoices)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ar-invoices'] })
    },
  })
}

export const usePostARInvoice = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => arApi.postARInvoice(id),
    // Optimistic update
    onMutate: async (invoiceId) => {
      await queryClient.cancelQueries({ queryKey: ['ar-invoices'] })
      await queryClient.cancelQueries({ queryKey: ['ar-invoice', invoiceId] })
      const previousInvoices = queryClient.getQueryData(['ar-invoices'])
      const previousInvoice = queryClient.getQueryData(['ar-invoice', invoiceId])
      
      queryClient.setQueryData(['ar-invoices'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((inv: any) =>
            inv.id === invoiceId ? { ...inv, status: 'posted', posted_at: new Date().toISOString() } : inv
          ),
        }
      })
      
      queryClient.setQueryData(['ar-invoice', invoiceId], (old: any) => {
        return old ? { ...old, status: 'posted', posted_at: new Date().toISOString() } : old
      })
      
      return { previousInvoices, previousInvoice }
    },
    onError: (err, invoiceId, context) => {
      if (context?.previousInvoices) {
        queryClient.setQueryData(['ar-invoices'], context.previousInvoices)
      }
      if (context?.previousInvoice) {
        queryClient.setQueryData(['ar-invoice', invoiceId], context.previousInvoice)
      }
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['ar-invoices'] })
      queryClient.invalidateQueries({ queryKey: ['ar-invoice', id] })
    },
  })
}

// AR Payments
export const useARPayments = (params?: {
  legal_entity_id?: string
  customer_id?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['ar-payments', params],
    queryFn: () => arApi.getARPayments(params),
  })
}

export const useARPayment = (id: string) => {
  return useQuery({
    queryKey: ['ar-payment', id],
    queryFn: () => arApi.getARPayment(id),
    enabled: !!id,
  })
}

export const useCreateARPayment = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateARPaymentRequest) => arApi.createARPayment(data),
    // Optimistic update
    onMutate: async (newPayment) => {
      await queryClient.cancelQueries({ queryKey: ['ar-payments'] })
      await queryClient.cancelQueries({ queryKey: ['ar-invoices'] })
      const previousPayments = queryClient.getQueryData(['ar-payments'])
      const previousInvoices = queryClient.getQueryData(['ar-invoices'])
      
      queryClient.setQueryData(['ar-payments'], (old: any) => {
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
        queryClient.setQueryData(['ar-payments'], context.previousPayments)
      }
      if (context?.previousInvoices) {
        queryClient.setQueryData(['ar-invoices'], context.previousInvoices)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ar-payments'] })
      queryClient.invalidateQueries({ queryKey: ['ar-invoices'] })
    },
  })
}

// Revenue Schedules
export const useRevenueSchedules = (params?: {
  legal_entity_id?: string
  invoice_id?: string
  is_recognized?: boolean
}) => {
  return useQuery({
    queryKey: ['revenue-schedules', params],
    queryFn: () => arApi.getRevenueSchedules(params),
  })
}

export const useRevenueSchedule = (id: string) => {
  return useQuery({
    queryKey: ['revenue-schedule', id],
    queryFn: () => arApi.getRevenueSchedule(id),
    enabled: !!id,
  })
}

export const useRecognizeRevenue = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ schedule_id, period_id }: { schedule_id: string; period_id: string }) =>
      arApi.recognizeRevenue(schedule_id, period_id),
    onSuccess: (_, { schedule_id }) => {
      queryClient.invalidateQueries({ queryKey: ['revenue-schedules'] })
      queryClient.invalidateQueries({ queryKey: ['revenue-schedule', schedule_id] })
    },
  })
}

// AR Aging
export const useARAging = (params: { legal_entity_id: string; as_of_date: string }) => {
  return useQuery({
    queryKey: ['ar-aging', params],
    queryFn: () => arApi.getARAging(params),
    enabled: !!params.legal_entity_id && !!params.as_of_date,
  })
}
