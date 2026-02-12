import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { glApi, Dimension, CreateDimensionRequest } from '@/lib/api/glApi'

export const useDimensions = (params?: {
  legal_entity_id?: string
  is_active?: boolean
}) => {
  return useQuery({
    queryKey: ['dimensions', params],
    queryFn: () => glApi.getDimensions(params),
  })
}

export const useDimension = (id: string) => {
  return useQuery({
    queryKey: ['dimension', id],
    queryFn: () => glApi.getDimension(id),
    enabled: !!id,
  })
}

export const useCreateDimension = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateDimensionRequest) => glApi.createDimension(data),
    // Optimistic update
    onMutate: async (newDimension) => {
      await queryClient.cancelQueries({ queryKey: ['dimensions'] })
      const previousDimensions = queryClient.getQueryData(['dimensions'])
      
      queryClient.setQueryData(['dimensions'], (old: any) => {
        const optimisticDimension = {
          id: `temp-${Date.now()}`,
          ...newDimension,
          is_active: true,
          created_at: new Date().toISOString(),
        }
        return old ? { ...old, items: [...(old.items || []), optimisticDimension] } : { items: [optimisticDimension] }
      })
      
      return { previousDimensions }
    },
    onError: (err, newDimension, context) => {
      if (context?.previousDimensions) {
        queryClient.setQueryData(['dimensions'], context.previousDimensions)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dimensions'] })
    },
  })
}

export const useUpdateDimension = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateDimensionRequest> }) =>
      glApi.updateDimension(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['dimensions'] })
      await queryClient.cancelQueries({ queryKey: ['dimension', id] })
      const previousDimensions = queryClient.getQueryData(['dimensions'])
      const previousDimension = queryClient.getQueryData(['dimension', id])
      
      queryClient.setQueryData(['dimensions'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((dim: any) =>
            dim.id === id ? { ...dim, ...data, updated_at: new Date().toISOString() } : dim
          ),
        }
      })
      
      queryClient.setQueryData(['dimension', id], (old: any) => {
        return old ? { ...old, ...data, updated_at: new Date().toISOString() } : old
      })
      
      return { previousDimensions, previousDimension }
    },
    onError: (err, { id }, context) => {
      if (context?.previousDimensions) {
        queryClient.setQueryData(['dimensions'], context.previousDimensions)
      }
      if (context?.previousDimension) {
        queryClient.setQueryData(['dimension', id], context.previousDimension)
      }
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['dimensions'] })
      queryClient.invalidateQueries({ queryKey: ['dimension', id] })
    },
  })
}

export const useDeleteDimension = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => glApi.deleteDimension(id),
    // Optimistic update
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['dimensions'] })
      const previousDimensions = queryClient.getQueryData(['dimensions'])
      
      queryClient.setQueryData(['dimensions'], (old: any) => {
        return old ? { ...old, items: (old.items || []).filter((dim: any) => dim.id !== deletedId) } : old
      })
      
      return { previousDimensions }
    },
    onError: (err, deletedId, context) => {
      if (context?.previousDimensions) {
        queryClient.setQueryData(['dimensions'], context.previousDimensions)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dimensions'] })
    },
  })
}
