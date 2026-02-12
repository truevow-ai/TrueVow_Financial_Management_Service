import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { glApi, AccountingPeriod, CreatePeriodRequest } from '@/lib/api/glApi'

export const usePeriods = (params?: {
  legal_entity_id?: string
  book_id?: string
  status?: string
}) => {
  return useQuery({
    queryKey: ['periods', params],
    queryFn: () => glApi.getPeriods(params),
  })
}

export const usePeriod = (id: string) => {
  return useQuery({
    queryKey: ['period', id],
    queryFn: () => glApi.getPeriod(id),
    enabled: !!id,
  })
}

export const useCreatePeriod = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreatePeriodRequest) => glApi.createPeriod(data),
    // Optimistic update
    onMutate: async (newPeriod) => {
      await queryClient.cancelQueries({ queryKey: ['periods'] })
      const previousPeriods = queryClient.getQueryData(['periods'])
      
      queryClient.setQueryData(['periods'], (old: any) => {
        const optimisticPeriod = {
          id: `temp-${Date.now()}`,
          status: 'open',
          created_at: new Date().toISOString(),
          ...newPeriod,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticPeriod] } : { items: [optimisticPeriod] }
      })
      
      return { previousPeriods }
    },
    onError: (err, newPeriod, context) => {
      if (context?.previousPeriods) {
        queryClient.setQueryData(['periods'], context.previousPeriods)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['periods'] })
    },
  })
}

export const useClosePeriod = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => glApi.closePeriod(id),
    // Optimistic update
    onMutate: async (periodId) => {
      await queryClient.cancelQueries({ queryKey: ['periods'] })
      await queryClient.cancelQueries({ queryKey: ['period', periodId] })
      const previousPeriods = queryClient.getQueryData(['periods'])
      const previousPeriod = queryClient.getQueryData(['period', periodId])
      
      queryClient.setQueryData(['periods'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((period: any) =>
            period.id === periodId ? { ...period, status: 'closed', closed_at: new Date().toISOString() } : period
          ),
        }
      })
      
      queryClient.setQueryData(['period', periodId], (old: any) => {
        return old ? { ...old, status: 'closed', closed_at: new Date().toISOString() } : old
      })
      
      return { previousPeriods, previousPeriod }
    },
    onError: (err, periodId, context) => {
      if (context?.previousPeriods) {
        queryClient.setQueryData(['periods'], context.previousPeriods)
      }
      if (context?.previousPeriod) {
        queryClient.setQueryData(['period', periodId], context.previousPeriod)
      }
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['periods'] })
      queryClient.invalidateQueries({ queryKey: ['period', id] })
    },
  })
}

export const useLockPeriod = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => glApi.lockPeriod(id),
    // Optimistic update
    onMutate: async (periodId) => {
      await queryClient.cancelQueries({ queryKey: ['periods'] })
      await queryClient.cancelQueries({ queryKey: ['period', periodId] })
      const previousPeriods = queryClient.getQueryData(['periods'])
      const previousPeriod = queryClient.getQueryData(['period', periodId])
      
      queryClient.setQueryData(['periods'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((period: any) =>
            period.id === periodId ? { ...period, status: 'locked', locked_at: new Date().toISOString() } : period
          ),
        }
      })
      
      queryClient.setQueryData(['period', periodId], (old: any) => {
        return old ? { ...old, status: 'locked', locked_at: new Date().toISOString() } : old
      })
      
      return { previousPeriods, previousPeriod }
    },
    onError: (err, periodId, context) => {
      if (context?.previousPeriods) {
        queryClient.setQueryData(['periods'], context.previousPeriods)
      }
      if (context?.previousPeriod) {
        queryClient.setQueryData(['period', periodId], context.previousPeriod)
      }
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['periods'] })
      queryClient.invalidateQueries({ queryKey: ['period', id] })
    },
  })
}
