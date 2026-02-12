import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  payrollApi,
  Employee,
  PayGroup,
  PayComponent,
  PayrollRun,
  PayrollRunDetail,
  CommissionPlan,
  BonusPlan,
  PaymentBatch,
  Payslip,
  CreateEmployeeRequest,
  CreatePayGroupRequest,
  CreatePayComponentRequest,
  CreatePayrollRunRequest,
  CreateCommissionPlanRequest,
  CreateBonusPlanRequest,
} from '@/lib/api/payrollApi'

// Employees
export const useEmployees = (params?: {
  legal_entity_id?: string
  pay_group_id?: string
  is_active?: boolean
}) => {
  return useQuery({
    queryKey: ['employees', params],
    queryFn: () => payrollApi.getEmployees(params),
  })
}

export const useEmployee = (id: string) => {
  return useQuery({
    queryKey: ['employee', id],
    queryFn: () => payrollApi.getEmployee(id),
    enabled: !!id,
  })
}

export const useCreateEmployee = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateEmployeeRequest) => payrollApi.createEmployee(data),
    // Optimistic update
    onMutate: async (newEmployee) => {
      await queryClient.cancelQueries({ queryKey: ['employees'] })
      const previousEmployees = queryClient.getQueryData(['employees'])
      
      queryClient.setQueryData(['employees'], (old: any) => {
        const optimisticEmployee = {
          id: `temp-${Date.now()}`,
          employee_number: `EMP-TEMP-${Date.now()}`,
          created_at: new Date().toISOString(),
          ...newEmployee,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticEmployee] } : { items: [optimisticEmployee] }
      })
      
      return { previousEmployees }
    },
    onError: (err, newEmployee, context) => {
      if (context?.previousEmployees) {
        queryClient.setQueryData(['employees'], context.previousEmployees)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
    },
  })
}

export const useUpdateEmployee = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateEmployeeRequest> }) =>
      payrollApi.updateEmployee(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['employees'] })
      await queryClient.cancelQueries({ queryKey: ['employee', id] })
      const previousEmployees = queryClient.getQueryData(['employees'])
      const previousEmployee = queryClient.getQueryData(['employee', id])
      
      queryClient.setQueryData(['employees'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((emp: any) =>
            emp.id === id ? { ...emp, ...data, updated_at: new Date().toISOString() } : emp
          ),
        }
      })
      
      queryClient.setQueryData(['employee', id], (old: any) => {
        return old ? { ...old, ...data, updated_at: new Date().toISOString() } : old
      })
      
      return { previousEmployees, previousEmployee }
    },
    onError: (err, { id }, context) => {
      if (context?.previousEmployees) {
        queryClient.setQueryData(['employees'], context.previousEmployees)
      }
      if (context?.previousEmployee) {
        queryClient.setQueryData(['employee', id], context.previousEmployee)
      }
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      queryClient.invalidateQueries({ queryKey: ['employee', id] })
    },
  })
}

export const useDeleteEmployee = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => payrollApi.deleteEmployee(id),
    // Optimistic update
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['employees'] })
      const previousEmployees = queryClient.getQueryData(['employees'])
      
      queryClient.setQueryData(['employees'], (old: any) => {
        return old ? { ...old, items: (old.items || []).filter((emp: any) => emp.id !== deletedId) } : old
      })
      
      return { previousEmployees }
    },
    onError: (err, deletedId, context) => {
      if (context?.previousEmployees) {
        queryClient.setQueryData(['employees'], context.previousEmployees)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
    },
  })
}

// Pay Groups
export const usePayGroups = (params?: { legal_entity_id?: string; is_active?: boolean }) => {
  return useQuery({
    queryKey: ['pay-groups', params],
    queryFn: () => payrollApi.getPayGroups(params),
  })
}

export const useCreatePayGroup = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreatePayGroupRequest) => payrollApi.createPayGroup(data),
    // Optimistic update
    onMutate: async (newPayGroup) => {
      await queryClient.cancelQueries({ queryKey: ['pay-groups'] })
      const previousPayGroups = queryClient.getQueryData(['pay-groups'])
      
      queryClient.setQueryData(['pay-groups'], (old: any) => {
        const optimisticPayGroup = {
          id: `temp-${Date.now()}`,
          created_at: new Date().toISOString(),
          ...newPayGroup,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticPayGroup] } : { items: [optimisticPayGroup] }
      })
      
      return { previousPayGroups }
    },
    onError: (err, newPayGroup, context) => {
      if (context?.previousPayGroups) {
        queryClient.setQueryData(['pay-groups'], context.previousPayGroups)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pay-groups'] })
    },
  })
}

// Pay Components
export const usePayComponents = (params?: {
  legal_entity_id?: string
  component_type?: string
  is_active?: boolean
}) => {
  return useQuery({
    queryKey: ['pay-components', params],
    queryFn: () => payrollApi.getPayComponents(params),
  })
}

export const useCreatePayComponent = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreatePayComponentRequest) => payrollApi.createPayComponent(data),
    // Optimistic update
    onMutate: async (newComponent) => {
      await queryClient.cancelQueries({ queryKey: ['pay-components'] })
      const previousComponents = queryClient.getQueryData(['pay-components'])
      
      queryClient.setQueryData(['pay-components'], (old: any) => {
        const optimisticComponent = {
          id: `temp-${Date.now()}`,
          created_at: new Date().toISOString(),
          ...newComponent,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticComponent] } : { items: [optimisticComponent] }
      })
      
      return { previousComponents }
    },
    onError: (err, newComponent, context) => {
      if (context?.previousComponents) {
        queryClient.setQueryData(['pay-components'], context.previousComponents)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pay-components'] })
    },
  })
}

export const useUpdatePayComponent = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreatePayComponentRequest> }) =>
      payrollApi.updatePayComponent(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['pay-components'] })
      const previousComponents = queryClient.getQueryData(['pay-components'])
      
      queryClient.setQueryData(['pay-components'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((comp: any) =>
            comp.id === id ? { ...comp, ...data, updated_at: new Date().toISOString() } : comp
          ),
        }
      })
      
      return { previousComponents }
    },
    onError: (err, { id }, context) => {
      if (context?.previousComponents) {
        queryClient.setQueryData(['pay-components'], context.previousComponents)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pay-components'] })
    },
  })
}

// Payroll Runs
export const usePayrollRuns = (params?: {
  legal_entity_id?: string
  pay_group_id?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return useQuery({
    queryKey: ['payroll-runs', params],
    queryFn: () => payrollApi.getPayrollRuns(params),
  })
}

export const usePayrollRun = (id: string) => {
  return useQuery({
    queryKey: ['payroll-run', id],
    queryFn: () => payrollApi.getPayrollRun(id),
    enabled: !!id,
  })
}

export const usePayrollRunDetails = (id: string) => {
  return useQuery({
    queryKey: ['payroll-run-details', id],
    queryFn: () => payrollApi.getPayrollRunDetails(id),
    enabled: !!id,
  })
}

export const useCreatePayrollRun = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreatePayrollRunRequest) => payrollApi.createPayrollRun(data),
    // Optimistic update
    onMutate: async (newPayrollRun) => {
      await queryClient.cancelQueries({ queryKey: ['payroll-runs'] })
      const previousPayrollRuns = queryClient.getQueryData(['payroll-runs'])
      
      queryClient.setQueryData(['payroll-runs'], (old: any) => {
        const optimisticPayrollRun = {
          id: `temp-${Date.now()}`,
          run_number: `PR-TEMP-${Date.now()}`,
          status: 'draft',
          created_at: new Date().toISOString(),
          ...newPayrollRun,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticPayrollRun] } : { items: [optimisticPayrollRun] }
      })
      
      return { previousPayrollRuns }
    },
    onError: (err, newPayrollRun, context) => {
      if (context?.previousPayrollRuns) {
        queryClient.setQueryData(['payroll-runs'], context.previousPayrollRuns)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
    },
  })
}

export const useCalculatePayrollRun = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => payrollApi.calculatePayrollRun(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
      queryClient.invalidateQueries({ queryKey: ['payroll-run', id] })
      queryClient.invalidateQueries({ queryKey: ['payroll-run-details', id] })
    },
  })
}

export const useApprovePayrollRun = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => payrollApi.approvePayrollRun(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
      queryClient.invalidateQueries({ queryKey: ['payroll-run', id] })
    },
  })
}

export const usePostPayrollRun = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => payrollApi.postPayrollRun(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
      queryClient.invalidateQueries({ queryKey: ['payroll-run', id] })
    },
  })
}

// Commission Plans
export const useCommissionPlans = (params?: {
  legal_entity_id?: string
  is_active?: boolean
}) => {
  return useQuery({
    queryKey: ['commission-plans', params],
    queryFn: () => payrollApi.getCommissionPlans(params),
  })
}

export const useCreateCommissionPlan = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateCommissionPlanRequest) => payrollApi.createCommissionPlan(data),
    // Optimistic update
    onMutate: async (newPlan) => {
      await queryClient.cancelQueries({ queryKey: ['commission-plans'] })
      const previousPlans = queryClient.getQueryData(['commission-plans'])
      
      queryClient.setQueryData(['commission-plans'], (old: any) => {
        const optimisticPlan = {
          id: `temp-${Date.now()}`,
          created_at: new Date().toISOString(),
          ...newPlan,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticPlan] } : { items: [optimisticPlan] }
      })
      
      return { previousPlans }
    },
    onError: (err, newPlan, context) => {
      if (context?.previousPlans) {
        queryClient.setQueryData(['commission-plans'], context.previousPlans)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commission-plans'] })
    },
  })
}

export const useUpdateCommissionPlan = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateCommissionPlanRequest> }) =>
      payrollApi.updateCommissionPlan(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['commission-plans'] })
      const previousPlans = queryClient.getQueryData(['commission-plans'])
      
      queryClient.setQueryData(['commission-plans'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((plan: any) =>
            plan.id === id ? { ...plan, ...data, updated_at: new Date().toISOString() } : plan
          ),
        }
      })
      
      return { previousPlans }
    },
    onError: (err, { id }, context) => {
      if (context?.previousPlans) {
        queryClient.setQueryData(['commission-plans'], context.previousPlans)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commission-plans'] })
    },
  })
}

// Bonus Plans
export const useBonusPlans = (params?: {
  legal_entity_id?: string
  is_active?: boolean
}) => {
  return useQuery({
    queryKey: ['bonus-plans', params],
    queryFn: () => payrollApi.getBonusPlans(params),
  })
}

export const useCreateBonusPlan = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateBonusPlanRequest) => payrollApi.createBonusPlan(data),
    // Optimistic update
    onMutate: async (newPlan) => {
      await queryClient.cancelQueries({ queryKey: ['bonus-plans'] })
      const previousPlans = queryClient.getQueryData(['bonus-plans'])
      
      queryClient.setQueryData(['bonus-plans'], (old: any) => {
        const optimisticPlan = {
          id: `temp-${Date.now()}`,
          created_at: new Date().toISOString(),
          ...newPlan,
        }
        return old ? { ...old, items: [...(old.items || []), optimisticPlan] } : { items: [optimisticPlan] }
      })
      
      return { previousPlans }
    },
    onError: (err, newPlan, context) => {
      if (context?.previousPlans) {
        queryClient.setQueryData(['bonus-plans'], context.previousPlans)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bonus-plans'] })
    },
  })
}

export const useUpdateBonusPlan = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateBonusPlanRequest> }) =>
      payrollApi.updateBonusPlan(id, data),
    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['bonus-plans'] })
      const previousPlans = queryClient.getQueryData(['bonus-plans'])
      
      queryClient.setQueryData(['bonus-plans'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: (old.items || []).map((plan: any) =>
            plan.id === id ? { ...plan, ...data, updated_at: new Date().toISOString() } : plan
          ),
        }
      })
      
      return { previousPlans }
    },
    onError: (err, { id }, context) => {
      if (context?.previousPlans) {
        queryClient.setQueryData(['bonus-plans'], context.previousPlans)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bonus-plans'] })
    },
  })
}

// Payment Batches
export const usePaymentBatches = (params?: {
  payroll_run_id?: string
  status?: string
}) => {
  return useQuery({
    queryKey: ['payment-batches', params],
    queryFn: () => payrollApi.getPaymentBatches(params),
  })
}

export const useGeneratePaymentBatch = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ payroll_run_id, payment_method }: { payroll_run_id: string; payment_method: string }) =>
      payrollApi.generatePaymentBatch(payroll_run_id, payment_method),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment-batches'] })
    },
  })
}

// Payslips
export const usePayslip = (payroll_run_id: string, employee_id: string) => {
  return useQuery({
    queryKey: ['payslip', payroll_run_id, employee_id],
    queryFn: () => payrollApi.getPayslip(payroll_run_id, employee_id),
    enabled: !!payroll_run_id && !!employee_id,
  })
}

export const useBulkUpsertPayrollAdjustments = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      runId,
      adjustments,
    }: {
      runId: string
      adjustments: Array<{
        client_row_id?: string
        adjustment_id?: string
        employee_id: string
        component_type: 'BONUS' | 'COMMISSION' | 'ADJUSTMENT' | 'DEDUCTION'
        amount: number
        currency?: string
        memo?: string
        cost_center?: string
        department?: string
        location?: string
        deleted?: boolean
      }>
    }) => payrollApi.bulkUpsertPayrollAdjustments(runId, adjustments),
    onSuccess: (_, { runId }) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-run', runId] })
      queryClient.invalidateQueries({ queryKey: ['payroll-run-details', runId] })
    },
  })
}

export const useRecalculatePayrollRun = () => {
  return useMutation({
    mutationFn: ({ runId }: { runId: string }) => payrollApi.recalculatePayrollRun(runId),
  })
}
