import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { glApi, GLAccount, CreateGLAccountRequest } from '@/lib/api/glApi'

export const useGLAccounts = (params?: {
  legal_entity_id?: string
  account_type?: string
  is_active?: boolean
}) => {
  return useQuery({
    queryKey: ['gl-accounts', params],
    queryFn: () => glApi.getGLAccounts(params),
  })
}

export const useGLAccount = (id: string) => {
  return useQuery({
    queryKey: ['gl-account', id],
    queryFn: () => glApi.getGLAccount(id),
    enabled: !!id,
  })
}

export const useCreateGLAccount = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateGLAccountRequest) => glApi.createGLAccount(data),
    // Optimistic update
    onMutate: async (newAccount) => {
      await queryClient.cancelQueries({ queryKey: ['gl-accounts'] })
      const previousAccounts = queryClient.getQueryData(['gl-accounts'])
      
      queryClient.setQueryData(['gl-accounts'], (old: any) => {
        const optimisticAccount = {
          id: `temp-${Date.now()}`,
          created_at: new Date().toISOString(),
          ...newAccount,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticAccount] } : { items: [optimisticAccount] }
      })
      
      return { previousAccounts }
    },
    onError: (err, newAccount, context) => {
      if (context?.previousAccounts) {
        queryClient.setQueryData(['gl-accounts'], context.previousAccounts)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-accounts'] })
    },
  })
}

export const useUpdateGLAccount = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateGLAccountRequest> }) =>
      glApi.updateGLAccount(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['gl-accounts'] })
      await queryClient.cancelQueries({ queryKey: ['gl-account', id] })
      const previousAccounts = queryClient.getQueryData(['gl-accounts'])
      const previousAccount = queryClient.getQueryData(['gl-account', id])
      
      queryClient.setQueryData(['gl-accounts'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((acc: any) =>
            acc.id === id ? { ...acc, ...data, updated_at: new Date().toISOString() } : acc
          ),
        }
      })
      
      queryClient.setQueryData(['gl-account', id], (old: any) => {
        return old ? { ...old, ...data, updated_at: new Date().toISOString() } : old
      })
      
      return { previousAccounts, previousAccount }
    },
    onError: (err, { id }, context) => {
      if (context?.previousAccounts) {
        queryClient.setQueryData(['gl-accounts'], context.previousAccounts)
      }
      if (context?.previousAccount) {
        queryClient.setQueryData(['gl-account', id], context.previousAccount)
      }
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['gl-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['gl-account', id] })
    },
  })
}

export const useDeleteGLAccount = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => glApi.deleteGLAccount(id),
    // Optimistic update
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['gl-accounts'] })
      const previousAccounts = queryClient.getQueryData(['gl-accounts'])
      
      queryClient.setQueryData(['gl-accounts'], (old: any) => {
        return old ? { ...old, items: (old.items || []).filter((acc: any) => acc.id !== deletedId) } : old
      })
      
      return { previousAccounts }
    },
    onError: (err, deletedId, context) => {
      if (context?.previousAccounts) {
        queryClient.setQueryData(['gl-accounts'], context.previousAccounts)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-accounts'] })
    },
  })
}
