import { useQuery } from '@tanstack/react-query'
import { reportingApi } from '@/lib/api/reportingApi'

export const useTrialBalance = (params: {
  legal_entity_id: string
  book_id: string
  period_id?: string
  as_of_date?: string
}) => {
  return useQuery({
    queryKey: ['trial-balance', params],
    queryFn: () => reportingApi.getTrialBalance(params),
    enabled: !!params.legal_entity_id && !!params.book_id,
  })
}

export const usePLBalanceSheet = (params: {
  legal_entity_id: string
  book_id: string
  period_id?: string
  as_of_date?: string
}) => {
  return useQuery({
    queryKey: ['pl-balance-sheet', params],
    queryFn: () => reportingApi.getPLBalanceSheet(params),
    enabled: !!params.legal_entity_id && !!params.book_id,
  })
}

export const useCashPosition = (params: {
  legal_entity_id: string
  book_id: string
  as_of_date?: string
}) => {
  return useQuery({
    queryKey: ['cash-position', params],
    queryFn: () => reportingApi.getCashPosition(params),
    enabled: !!params.legal_entity_id,
  })
}

export const useCashFlow = (params: {
  legal_entity_id: string
  book_id: string
  period_id?: string
  as_of_date?: string
}) => {
  return useQuery({
    queryKey: ['cash-flow', params],
    queryFn: () => reportingApi.getCashFlow(params),
    enabled: !!params.legal_entity_id && !!params.book_id,
  })
}

export const useGLDetail = (params: {
  legal_entity_id: string
  book_id: string
  period_id?: string
  as_of_date?: string
  account_id?: string
  dimension_id?: string
  search?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['gl-detail', params],
    queryFn: () => reportingApi.getGLDetail(params),
    enabled: !!params.legal_entity_id && !!params.book_id,
  })
}
