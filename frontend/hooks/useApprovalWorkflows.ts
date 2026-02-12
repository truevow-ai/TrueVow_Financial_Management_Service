"use client"

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useClerkToken } from './useClerkToken'
import { useEntityBook } from '@/contexts/EntityBookContext'

/**
 * Approval Workflow Hooks
 * Handles submit, approve, reject, and post actions for approval workflows
 */

// Payroll Run Approval Hooks
export function useSubmitPayrollRunForApproval() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ runId, reason }: { runId: string; reason?: string }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/payroll/runs/${runId}/submit-approval`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to submit for approval')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-run', variables.runId] })
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
    },
  })
}

export function useApprovePayrollRun() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ 
      runId, 
      reason, 
      overrideReason 
    }: { 
      runId: string
      reason?: string
      overrideReason?: string 
    }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/payroll/runs/${runId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason, override_reason: overrideReason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to approve')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-run', variables.runId] })
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
    },
  })
}

export function useRejectPayrollRun() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ 
      runId, 
      reason, 
      requiredChanges 
    }: { 
      runId: string
      reason: string
      requiredChanges?: string[] 
    }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/payroll/runs/${runId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason, required_changes: requiredChanges }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to reject')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-run', variables.runId] })
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
    },
  })
}

// Reconciliation Adjustment Approval Hooks
export function useSubmitReconciliationAdjustment() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  
  return useMutation({
    mutationFn: async ({ recId, batchId, reason }: { recId: string; batchId: string; reason?: string }) => {
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/reconciliations/${recId}/adjustments/submit-approval`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ batch_id: batchId, reason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to submit for approval')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation', variables.recId] })
    },
  })
}

export function useApproveReconciliationAdjustment() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  
  return useMutation({
    mutationFn: async ({ 
      recId, 
      batchId, 
      reason, 
      overrideReason 
    }: { 
      recId: string
      batchId: string
      reason?: string
      overrideReason?: string 
    }) => {
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/reconciliations/${recId}/adjustments/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ batch_id: batchId, reason, override_reason: overrideReason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to approve')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation', variables.recId] })
    },
  })
}

export function useRejectReconciliationAdjustment() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  
  return useMutation({
    mutationFn: async ({ 
      recId, 
      batchId, 
      reason, 
      requiredChanges 
    }: { 
      recId: string
      batchId: string
      reason: string
      requiredChanges?: string[] 
    }) => {
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/reconciliations/${recId}/adjustments/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ batch_id: batchId, reason, required_changes: requiredChanges }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to reject')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation', variables.recId] })
    },
  })
}

// Period Close Approval Hooks
export function useSubmitPeriodClose() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ periodId, reason }: { periodId: string; reason?: string }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/periods/${periodId}/submit-close`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to submit for close')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['period', variables.periodId] })
      queryClient.invalidateQueries({ queryKey: ['periods'] })
    },
  })
}

export function useApprovePeriodClose() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ 
      periodId, 
      reason, 
      overrideReason 
    }: { 
      periodId: string
      reason?: string
      overrideReason?: string 
    }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/periods/${periodId}/approve-close`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason, override_reason: overrideReason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to approve close')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['period', variables.periodId] })
      queryClient.invalidateQueries({ queryKey: ['periods'] })
    },
  })
}

// Royalty Run Approval Hooks
export function useSubmitRoyaltyRun() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  
  return useMutation({
    mutationFn: async ({ runId, reason }: { runId: string; reason?: string }) => {
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/intercompany/royalties/runs/${runId}/submit-approval`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to submit for approval')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['royalty-run', variables.runId] })
      queryClient.invalidateQueries({ queryKey: ['royalty-runs'] })
    },
  })
}

export function useApproveRoyaltyRun() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  
  return useMutation({
    mutationFn: async ({ 
      runId, 
      reason, 
      overrideReason 
    }: { 
      runId: string
      reason?: string
      overrideReason?: string 
    }) => {
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/intercompany/royalties/runs/${runId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason, override_reason: overrideReason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to approve')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['royalty-run', variables.runId] })
      queryClient.invalidateQueries({ queryKey: ['royalty-runs'] })
    },
  })
}

export function useRejectRoyaltyRun() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  
  return useMutation({
    mutationFn: async ({ 
      runId, 
      reason, 
      requiredChanges 
    }: { 
      runId: string
      reason: string
      requiredChanges?: string[] 
    }) => {
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/intercompany/royalties/runs/${runId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason, required_changes: requiredChanges }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to reject')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['royalty-run', variables.runId] })
      queryClient.invalidateQueries({ queryKey: ['royalty-runs'] })
    },
  })
}

// AP Bill Approval Hooks
export function useSubmitAPBillForApproval() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ billId, reason }: { billId: string; reason?: string }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/ap/bills/${billId}/submit-approval`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to submit for approval')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['ap-bill', selectedBookId, variables.billId] })
      queryClient.invalidateQueries({ queryKey: ['ap-bills'] })
    },
  })
}

export function useApproveAPBill() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ 
      billId, 
      reason, 
      overrideReason 
    }: { 
      billId: string
      reason?: string
      overrideReason?: string 
    }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/ap/bills/${billId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason, override_reason: overrideReason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to approve')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['ap-bill', selectedBookId, variables.billId] })
      queryClient.invalidateQueries({ queryKey: ['ap-bills'] })
    },
  })
}

export function useRejectAPBill() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ billId, reason }: { billId: string; reason: string }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/ap/bills/${billId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to reject')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['ap-bill', selectedBookId, variables.billId] })
      queryClient.invalidateQueries({ queryKey: ['ap-bills'] })
    },
  })
}

export function usePostAPBill() {
  const queryClient = useQueryClient()
  const { getToken } = useClerkToken()
  const { selectedBookId } = useEntityBook()
  
  return useMutation({
    mutationFn: async ({ billId }: { billId: string }) => {
      if (!selectedBookId) {
        throw new Error('Book ID is required')
      }
      
      const token = await getToken()
      const response = await fetch(`/api/v1/fm/books/${selectedBookId}/ap/bills/${billId}/post`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({}),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to post')
      }
      return response.json()
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['ap-bill', selectedBookId, variables.billId] })
      queryClient.invalidateQueries({ queryKey: ['ap-bills'] })
    },
  })
}
