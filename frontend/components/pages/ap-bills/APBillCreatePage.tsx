'use client'

import { useState, useCallback, useMemo } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { useAPVendors } from '@/hooks/useAP'
import { useCreateAPBill, useUpdateAPBill, useAPBill } from '@/hooks/useAPBills'
import { useGLAccounts } from '@/hooks/useGLAccounts'
import { GlobalToolbar, ApprovalStatus } from '@/components/common/GlobalToolbar'
import { ApprovalStatusBanner } from '@/components/common/ApprovalStatusBanner'
import { useToast } from '@/hooks/useToast'
import { formatDate } from '@/lib/utils/format'
import {
  useSubmitAPBillForApproval,
  useApproveAPBill,
  useRejectAPBill,
  usePostAPBill
} from '@/hooks/useApprovalWorkflows'

interface APBillFormData {
  legal_entity_id: string
  ap_vendor_id: string
  bill_number: string
  bill_date: string
  due_date: string
  currency: string
  description: string
  reference_number: string
}

interface APBillLine {
  client_row_id: string
  line_id?: string
  gl_account_id?: string
  account_code: string
  description: string
  quantity: number
  unit_price: number
  line_amount: number
  tax_code?: string
}

export function APBillCreatePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const billId = searchParams.get('id')
  const { showToast } = useToast()
  const { selectedEntityId, selectedBookId, selectedEntity, selectedBook } = useEntityBook()
  const [mode, setMode] = useState<'form' | 'grid'>('form')
  const [lines, setLines] = useState<APBillLine[]>([
    {
      client_row_id: `temp-${Date.now()}-1`,
      account_code: '',
      description: '',
      quantity: 1,
      unit_price: 0,
      line_amount: 0,
    },
  ])
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)

  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm<APBillFormData>({
    defaultValues: {
      legal_entity_id: selectedEntityId || '',
      ap_vendor_id: '',
      bill_number: '',
      bill_date: new Date().toISOString().split('T')[0],
      due_date: '',
      currency: selectedBook?.currency || 'USD',
      description: '',
      reference_number: '',
    },
  })

  const { data: vendors } = useAPVendors({ legal_entity_id: selectedEntityId ?? undefined, is_active: true })
  const { data: accounts } = useGLAccounts({ legal_entity_id: selectedEntityId ?? undefined })
  const { data: billData } = useAPBill(selectedBookId || '', billId || '', {
    enabled: !!billId && !!selectedBookId,
  })

  const createMutation = useCreateAPBill()
  const updateMutation = useUpdateAPBill()
  const submitApproval = useSubmitAPBillForApproval()
  const approve = useApproveAPBill()
  const reject = useRejectAPBill()
  const post = usePostAPBill()

  const watchedValues = watch()

  // Determine status
  const billStatus: ApprovalStatus = billData?.status === 'posted' ? 'POSTED' :
                                     billId ? 'DRAFT' : 'DRAFT'

  const isReadOnly = billStatus === 'POSTED'
  const isLocked = billStatus === 'POSTED'

  // Calculate total
  const totalAmount = useMemo(() => {
    return lines.reduce((sum, line) => sum + (line.line_amount || 0), 0)
  }, [lines])

  // Handle lines change
  const handleLinesChange = useCallback((newLines: APBillLine[]) => {
    setLines(newLines.map(line => ({
      ...line,
      line_amount: (line.quantity || 1) * (line.unit_price || 0)
    })))
  }, [])

  // Create or update bill
  const onSubmit = useCallback(
    async (data: APBillFormData) => {
      if (!selectedBookId) {
        showToast('Please select a book', 'error')
        return
      }

      try {
        if (billId) {
          // Update existing bill
          await updateMutation.mutateAsync({
            billId,
            data: {
              ...data,
              lines: lines.map((line, idx) => ({
                gl_account_id: line.gl_account_id || '',
                description: line.description || '',
                quantity: line.quantity || 1,
                unit_price: line.unit_price || 0,
                total_amount: (line.quantity || 1) * (line.unit_price || 0),
                line_number: idx + 1,
                currency: data.currency,
                tax_code: line.tax_code,
              })),
            },
          })
          setLastSavedAt(new Date())
          showToast('AP bill updated', 'success')
        } else {
          // Create new bill
          const created = await createMutation.mutateAsync({
            legal_entity_id: data.legal_entity_id,
            vendor_id: data.ap_vendor_id,
            invoice_date: data.bill_date,
            due_date: data.due_date,
            currency: data.currency,
            description: data.description,
            lines: lines.map((line, idx) => ({
              gl_account_id: line.gl_account_id || '',
              description: line.description || '',
              quantity: line.quantity || 1,
              unit_price: line.unit_price || 0,
              total_amount: (line.quantity || 1) * (line.unit_price || 0),
              line_number: idx + 1,
              currency: data.currency,
              tax_code: line.tax_code,
            })),
          })
          setLastSavedAt(new Date())
          showToast('AP bill created', 'success')
          router.push(`/ap-bills?id=${created.id}`)
        }
      } catch (error: any) {
        showToast(error.message || 'Failed to save AP bill', 'error')
      }
    },
    [billId, selectedBookId, lines, createMutation, updateMutation, showToast, router]
  )

  // Handle approval actions
  const handleSubmitApproval = useCallback(async () => {
    if (!billId) {
      showToast('Please save the bill first', 'error')
      return
    }

    try {
      await submitApproval.mutateAsync({ billId, reason: 'Submitted for approval' })
      showToast('Bill submitted for approval', 'success')
    } catch (error: any) {
      showToast(error.message || 'Failed to submit for approval', 'error')
    }
  }, [billId, submitApproval, showToast])

  const handleApprove = useCallback(async () => {
    if (!billId) {
      showToast('Bill ID is required', 'error')
      return
    }

    try {
      await approve.mutateAsync({ billId, reason: 'Approved' })
      showToast('Bill approved', 'success')
    } catch (error: any) {
      showToast(error.message || 'Failed to approve', 'error')
    }
  }, [billId, approve, showToast])

  const handleReject = useCallback(async () => {
    if (!billId) {
      showToast('Bill ID is required', 'error')
      return
    }

    const reason = prompt('Please provide a reason for rejection:')
    if (!reason) return

    try {
      await reject.mutateAsync({ billId, reason })
      showToast('Bill rejected', 'success')
    } catch (error: any) {
      showToast(error.message || 'Failed to reject', 'error')
    }
  }, [billId, reject, showToast])

  const handlePost = useCallback(async () => {
    if (!billId) {
      showToast('Please save the bill first', 'error')
      return
    }

    try {
      await post.mutateAsync({ billId })
      showToast('AP bill posted successfully', 'success')
      router.push('/ap-bills')
    } catch (error: any) {
      showToast(error.message || 'Failed to post AP bill', 'error')
    }
  }, [billId, post, showToast, router])

  // Form mode component
  const formMode = (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Bill Header</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="bill_number" className="block text-sm font-medium text-gray-700 mb-1">
              Bill Number *
            </label>
            <input
              type="text"
              id="bill_number"
              {...register('bill_number', { required: 'Bill number is required' })}
              className="input"
              disabled={isLocked}
            />
            {errors.bill_number && <p className="text-red-600 text-sm mt-1">{errors.bill_number.message}</p>}
          </div>

          <div>
            <label htmlFor="ap_vendor_id" className="block text-sm font-medium text-gray-700 mb-1">
              Vendor *
            </label>
            <select
              id="ap_vendor_id"
              {...register('ap_vendor_id', { required: 'Vendor is required' })}
              className="input"
              disabled={isLocked}
            >
              <option value="">Select Vendor</option>
              {vendors?.map((vendor) => (
                <option key={vendor.id} value={vendor.id}>
                  {vendor.vendor_name} ({vendor.vendor_code})
                </option>
              ))}
            </select>
            {errors.ap_vendor_id && <p className="text-red-600 text-sm mt-1">{errors.ap_vendor_id.message}</p>}
          </div>

          <div>
            <label htmlFor="bill_date" className="block text-sm font-medium text-gray-700 mb-1">
              Bill Date *
            </label>
            <input
              type="date"
              id="bill_date"
              {...register('bill_date', { required: 'Bill date is required' })}
              className="input"
              disabled={isLocked}
            />
            {errors.bill_date && <p className="text-red-600 text-sm mt-1">{errors.bill_date.message}</p>}
          </div>

          <div>
            <label htmlFor="due_date" className="block text-sm font-medium text-gray-700 mb-1">
              Due Date
            </label>
            <input
              type="date"
              id="due_date"
              {...register('due_date')}
              className="input"
              disabled={isLocked}
            />
          </div>

          <div>
            <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-1">
              Currency *
            </label>
            <select
              id="currency"
              {...register('currency', { required: 'Currency is required' })}
              className="input"
              disabled={isLocked}
            >
              <option value="USD">USD</option>
              <option value="AED">AED</option>
              <option value="PKR">PKR</option>
            </select>
            {errors.currency && <p className="text-red-600 text-sm mt-1">{errors.currency.message}</p>}
          </div>

          <div>
            <label htmlFor="reference_number" className="block text-sm font-medium text-gray-700 mb-1">
              Reference Number
            </label>
            <input
              type="text"
              id="reference_number"
              {...register('reference_number')}
              className="input"
              placeholder="Vendor invoice number"
              disabled={isLocked}
            />
          </div>

          <div className="md:col-span-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              {...register('description')}
              className="input"
              rows={3}
              disabled={isLocked}
            />
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Bill Lines</h2>
        <p className="text-gray-600 text-sm mb-4">
          Switch to Grid mode for faster entry with Excel-like features (coming soon)
        </p>
        <div className="space-y-4">
          {lines.map((line, index) => (
            <div key={line.client_row_id || index} className="p-4 border border-gray-200 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Account</label>
                  <select
                    value={line.account_code}
                    onChange={(e) => {
                      if (!isLocked) {
                        const account = accounts?.find(a => a.account_code === e.target.value)
                        const newLines = [...lines]
                        newLines[index] = { ...line, account_code: e.target.value, gl_account_id: account?.id }
                        handleLinesChange(newLines)
                      }
                    }}
                    className="input"
                    disabled={isLocked}
                  >
                    <option value="">Select Account</option>
                    {accounts?.map((account) => (
                      <option key={account.id} value={account.account_code}>
                        {account.account_code} - {account.account_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    value={line.description}
                    onChange={(e) => {
                      if (!isLocked) {
                        const newLines = [...lines]
                        newLines[index] = { ...line, description: e.target.value }
                        handleLinesChange(newLines)
                      }
                    }}
                    className="input"
                    disabled={isLocked}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                  <input
                    type="number"
                    value={line.quantity || 1}
                    onChange={(e) => {
                      if (!isLocked) {
                        const newLines = [...lines]
                        const qty = parseFloat(e.target.value) || 1
                        newLines[index] = { ...line, quantity: qty, line_amount: qty * (line.unit_price || 0) }
                        handleLinesChange(newLines)
                      }
                    }}
                    className="input"
                    step="0.01"
                    disabled={isLocked}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Unit Price</label>
                  <input
                    type="number"
                    value={line.unit_price || 0}
                    onChange={(e) => {
                      if (!isLocked) {
                        const newLines = [...lines]
                        const price = parseFloat(e.target.value) || 0
                        newLines[index] = { ...line, unit_price: price, line_amount: (line.quantity || 1) * price }
                        handleLinesChange(newLines)
                      }
                    }}
                    className="input"
                    step="0.01"
                    disabled={isLocked}
                  />
                </div>
                <div className="md:col-span-5">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Line Total:</span>
                    <span className="text-lg font-semibold text-gray-900">
                      {watchedValues.currency || 'USD'} {line.line_amount.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
          <button
            onClick={() => {
              if (!isLocked) {
                setLines([
                  ...lines,
                  {
                    client_row_id: `temp-${Date.now()}-${lines.length + 1}`,
                    account_code: '',
                    description: '',
                    quantity: 1,
                    unit_price: 0,
                    line_amount: 0,
                  },
                ])
              }
            }}
            className="btn-secondary"
            disabled={isLocked}
          >
            Add Line
          </button>
        </div>
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-lg font-semibold text-gray-900">Total Amount:</span>
            <span className="text-xl font-bold text-gray-900">
              {watchedValues.currency || 'USD'} {totalAmount.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )

  // Grid mode component (placeholder - will be implemented with APBillGrid)
  const gridMode = (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Bill Header</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="grid_bill_number" className="block text-sm font-medium text-gray-700 mb-1">
              Bill Number *
            </label>
            <input
              type="text"
              id="grid_bill_number"
              {...register('bill_number', { required: 'Bill number is required' })}
              className="input"
              disabled={isLocked}
            />
          </div>
          <div>
            <label htmlFor="grid_vendor" className="block text-sm font-medium text-gray-700 mb-1">
              Vendor *
            </label>
            <select
              id="grid_vendor"
              {...register('ap_vendor_id', { required: 'Vendor is required' })}
              className="input"
              disabled={isLocked}
            >
              <option value="">Select Vendor</option>
              {vendors?.map((vendor) => (
                <option key={vendor.id} value={vendor.id}>
                  {vendor.vendor_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="grid_bill_date" className="block text-sm font-medium text-gray-700 mb-1">
              Bill Date *
            </label>
            <input
              type="date"
              id="grid_bill_date"
              {...register('bill_date', { required: 'Bill date is required' })}
              className="input"
              disabled={isLocked}
            />
          </div>
          <div>
            <label htmlFor="grid_due_date" className="block text-sm font-medium text-gray-700 mb-1">
              Due Date
            </label>
            <input
              type="date"
              id="grid_due_date"
              {...register('due_date')}
              className="input"
              disabled={isLocked}
            />
          </div>
        </div>
      </div>

      <div className="card">
        <p className="text-gray-600 text-sm mb-4">
          Grid mode for AP Bill lines is coming soon. Use Form mode for now.
        </p>
        {/* TODO: Add APBillGrid component here */}
      </div>
    </div>
  )

  return (
    <div className="flex flex-col h-screen">
      {/* Global Toolbar */}
      {billId && (
        <GlobalToolbar
          entityId={selectedEntityId || undefined}
          entityName={selectedEntity?.entity_name}
          bookId={selectedBookId || undefined}
          bookName={selectedBook?.book_name}
          status={billStatus}
          isPosted={billStatus === 'POSTED'}
          lastSavedAt={lastSavedAt || undefined}
          canSubmit={billStatus === 'DRAFT'}
          canApprove={false}
          canReject={false}
          canPost={false}
          onSubmitApproval={handleSubmitApproval}
          onApprove={handleApprove}
          onReject={handleReject}
          onPost={handlePost}
          onSave={handleSubmit(onSubmit)}
          isLocked={isLocked}
        />
      )}

      <div className="flex-1 overflow-auto p-6">
        {/* Approval Status Banner */}
        {billId && billData && billStatus !== 'DRAFT' && (
          <ApprovalStatusBanner
            status={billStatus}
            className="mb-6"
          />
        )}

        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {billId ? 'Edit AP Bill' : 'Create AP Bill'}
              </h1>
              <p className="text-gray-600 mt-1">Enter AP bill details and line items</p>
            </div>
            {!billId && (
              <div className="flex gap-2">
                <button onClick={() => router.back()} className="btn-outline">
                  Cancel
                </button>
                <button onClick={handleSubmit(onSubmit)} className="btn-primary" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Save Draft'}
                </button>
              </div>
            )}
          </div>

          {/* TODO: Add DualModeEditor when APBillGrid is ready */}
          {formMode}

          {/* Total Summary */}
          <div className="card bg-blue-50">
            <div className="flex justify-between items-center">
              <span className="text-lg font-semibold text-gray-900">Total Bill Amount:</span>
              <span className="text-2xl font-bold text-primary-600">
                {watchedValues.currency || 'USD'} {totalAmount.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
