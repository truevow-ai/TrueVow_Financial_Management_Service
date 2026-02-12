import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { glApi, JournalEntry, CreateJournalEntryRequest, JournalLine } from '@/lib/api/glApi'
import { useEntityBook } from '@/contexts/EntityBookContext'

export const useJournalEntries = (params?: {
  legal_entity_id?: string
  period_id?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  const { selectedBookId } = useEntityBook()
  
  return useQuery({
    queryKey: ['journal-entries', selectedBookId, params],
    queryFn: () => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return glApi.getJournalEntries(selectedBookId, params)
    },
    enabled: !!selectedBookId,
  })
}

export const useJournalEntry = (id: string, options?: { enabled?: boolean }) => {
  const { selectedBookId } = useEntityBook()
  
  return useQuery({
    queryKey: ['journal-entry', selectedBookId, id],
    queryFn: () => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return glApi.getJournalEntry(selectedBookId, id)
    },
    enabled: !!selectedBookId && !!id && (options?.enabled !== false),
  })
}

export const useCreateJournalEntry = () => {
  const queryClient = useQueryClient()
  const { selectedBookId } = useEntityBook()

  return useMutation({
    mutationFn: (data: CreateJournalEntryRequest) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return glApi.createJournalEntry(selectedBookId, data)
    },
    // Optimistic update
    onMutate: async (newEntry) => {
      await queryClient.cancelQueries({ queryKey: ['journal-entries'] })
      const previousEntries = queryClient.getQueryData(['journal-entries'])
      
      queryClient.setQueryData(['journal-entries'], (old: any) => {
        const optimisticEntry = {
          id: `temp-${Date.now()}`,
          entry_number: `JE-TEMP-${Date.now()}`,
          ...newEntry,
          status: 'draft',
          created_at: new Date().toISOString(),
        }
        return old ? { ...old, items: [...(old.items || []), optimisticEntry] } : { items: [optimisticEntry] }
      })
      
      return { previousEntries }
    },
    onError: (err, newEntry, context) => {
      if (context?.previousEntries) {
        queryClient.setQueryData(['journal-entries'], context.previousEntries)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] })
    },
  })
}

export const usePostJournalEntry = () => {
  const queryClient = useQueryClient()
  const { selectedBookId } = useEntityBook()
  // TODO: Get user ID from Clerk auth - for now backend extracts from token
  const userId = '00000000-0000-0000-0000-000000000000' // Placeholder - backend uses token user

  return useMutation({
    mutationFn: (id: string) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return glApi.postJournalEntry(selectedBookId, id, userId)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] })
      queryClient.invalidateQueries({ queryKey: ['journal-entry', selectedBookId, id] })
    },
  })
}

export const useReverseJournalEntry = () => {
  const queryClient = useQueryClient()
  const { selectedBookId } = useEntityBook()
  // TODO: Get user ID from Clerk auth - for now backend extracts from token
  const userId = '00000000-0000-0000-0000-000000000000' // Placeholder - backend uses token user

  return useMutation({
    mutationFn: ({ id, reversal_date, reason }: { id: string; reversal_date: string; reason: string }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return glApi.reverseJournalEntry(selectedBookId, id, userId, reason, reversal_date)
    },
    // Optimistic update
    onMutate: async ({ id, reversal_date }) => {
      await queryClient.cancelQueries({ queryKey: ['journal-entries'] })
      await queryClient.cancelQueries({ queryKey: ['journal-entry', id] })
      const previousEntries = queryClient.getQueryData(['journal-entries'])
      const previousEntry = queryClient.getQueryData(['journal-entry', id])
      
      queryClient.setQueryData(['journal-entries'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((entry: any) =>
            entry.id === id ? { ...entry, status: 'reversed', reversed_at: reversal_date } : entry
          ),
        }
      })
      
      queryClient.setQueryData(['journal-entry', id], (old: any) => {
        return old ? { ...old, status: 'reversed', reversed_at: reversal_date } : old
      })
      
      return { previousEntries, previousEntry }
    },
    onError: (err, { id }, context) => {
      if (context?.previousEntries) {
        queryClient.setQueryData(['journal-entries'], context.previousEntries)
      }
      if (context?.previousEntry) {
        queryClient.setQueryData(['journal-entry', id], context.previousEntry)
      }
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] })
      queryClient.invalidateQueries({ queryKey: ['journal-entry', id] })
    },
  })
}

export const useBulkUpsertJournalLines = () => {
  const queryClient = useQueryClient()
  const { selectedBookId } = useEntityBook()

  return useMutation({
    mutationFn: ({
      entryId,
      lines,
    }: {
      entryId: string
      lines: Array<{
        client_row_id?: string
        line_id?: string
        gl_account_id?: string
        account_code?: string
        description?: string
        debit_amount?: number
        credit_amount?: number
        cost_center?: string
        department?: string
        location?: string
        project?: string
        currency?: string
        fx_rate?: number
        deleted?: boolean
      }>
    }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return glApi.bulkUpsertJournalLines(entryId, lines, selectedBookId)
    },
    onSuccess: (_, { entryId }) => {
      queryClient.invalidateQueries({ queryKey: ['journal-entry', entryId] })
    },
  })
}

export const useValidateJournalEntry = () => {
  const { selectedBookId } = useEntityBook()

  return useMutation({
    mutationFn: ({ entryId }: { entryId: string }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      return glApi.validateJournalEntry(selectedBookId, entryId)
    },
  })
}
