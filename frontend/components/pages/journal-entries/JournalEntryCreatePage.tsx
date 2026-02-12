'use client'

import { useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { usePeriods } from '@/hooks/usePeriods'
import { useCreateJournalEntry, useBulkUpsertJournalLines, useValidateJournalEntry, usePostJournalEntry, useJournalEntry } from '@/hooks/useJournalEntries'
import { DualModeEditor } from '@/components/common/DualModeEditor'
import { JournalEntryGrid, JournalLine } from '@/components/common/JournalEntryGrid'
import { GlobalToolbar, ApprovalStatus } from '@/components/common/GlobalToolbar'
import { ApprovalStatusBanner } from '@/components/common/ApprovalStatusBanner'
import { useToast } from '@/hooks/useToast'
import { formatDate } from '@/lib/utils/format'

interface JournalEntryFormData {
  legal_entity_id: string
  book_id: string
  period_id: string
  entry_date: string
  description: string
}

export function JournalEntryCreatePage() {
  const router = useRouter()
  const { showToast } = useToast()
  const { selectedEntityId, selectedBookId, selectedEntity, selectedBook } = useEntityBook()
  const [mode, setMode] = useState<'form' | 'grid'>('form')
  const [lines, setLines] = useState<JournalLine[]>([
    {
      client_row_id: `temp-${Date.now()}-1`,
      account_code: '',
      description: '',
      debit_amount: 0,
      credit_amount: 0,
    },
  ])
  const [entryId, setEntryId] = useState<string | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)

  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm<JournalEntryFormData>({
    defaultValues: {
      legal_entity_id: selectedEntityId || '',
      book_id: selectedBookId || '',
      entry_date: new Date().toISOString().split('T')[0],
      description: '',
    },
  })

  const { data: periods } = usePeriods({
    legal_entity_id: selectedEntityId || undefined,
    book_id: selectedBookId || undefined,
    status: 'open',
  })

  const createMutation = useCreateJournalEntry()
  const bulkUpsertMutation = useBulkUpsertJournalLines()
  const validateMutation = useValidateJournalEntry()
  const postMutation = usePostJournalEntry()
  
  const watchedValues = watch()
  
  // Fetch entry data if entryId exists (for edit mode)
  const { data: entryData } = useJournalEntry(entryId || '', {
    enabled: !!entryId,
  })
  
  // Determine status - for now, journal entries use DRAFT -> POSTED (no approval workflow)
  // Map backend status to ApprovalStatus type
  const normalizedStatus = entryData?.status?.toLowerCase()
  const entryStatus: ApprovalStatus = normalizedStatus === 'posted' ? 'POSTED' : 
                                      normalizedStatus === 'reversed' ? 'REJECTED' : 
                                      entryId ? 'DRAFT' : 'DRAFT'
  
  const selectedPeriod = periods?.find((p) => p.id === watchedValues.period_id)
  const isReadOnly = entryStatus === 'POSTED'
  const isLocked = isReadOnly
  
  // Handle lines change with debounced save
  const handleLinesChange = useCallback(
    (newLines: JournalLine[]) => {
      setLines(newLines)
      // Auto-save if entry exists
      if (entryId && newLines.length > 0) {
        // Debounce the save
        const timeoutId = setTimeout(() => {
          bulkUpsertMutation.mutate(
            {
              entryId,
              lines: newLines.map((line) => ({
                client_row_id: line.client_row_id,
                line_id: line.line_id,
                account_code: line.account_code,
                description: line.description,
                debit_amount: line.debit_amount,
                credit_amount: line.credit_amount,
                cost_center: line.cost_center,
                department: line.department,
                location: line.location,
                project: line.project,
                currency: line.currency,
                fx_rate: line.fx_rate,
              })),
            },
            {
              onSuccess: (data) => {
                // Update lines with server IDs
                setLines(data.lines.map((line, index) => ({ ...newLines[index], line_id: line.id })))
              },
            }
          )
        }, 500)

        return () => clearTimeout(timeoutId)
      }
    },
    [entryId, bulkUpsertMutation]
  )

  // Validate entry
  const handleValidate = useCallback(async () => {
    if (!entryId) {
      showToast('Please save the entry first', 'error')
      return
    }

    setIsValidating(true)
    validateMutation.mutate(
      { entryId },
      {
        onSuccess: (result) => {
          setValidationResult(result)
          if (result.is_valid) {
            showToast('Entry is valid and balanced', 'success')
          } else {
            showToast(`Validation failed: ${result.errors.length} error(s)`, 'error')
          }
          setIsValidating(false)
        },
        onError: () => {
          setIsValidating(false)
        },
      }
    )
  }, [entryId, validateMutation, showToast])

  // Create draft entry
  const onSubmit = useCallback(
    async (data: JournalEntryFormData) => {
      try {
        const entry = await createMutation.mutateAsync({
          ...data,
          lines: lines.map((line) => ({
            gl_account_id: '', // Will be resolved by account_code
            account_code: line.account_code,
            description: line.description || '',
            debit_amount: line.debit_amount || 0,
            credit_amount: line.credit_amount || 0,
          })),
        })
        setEntryId(entry.id)
        setLastSavedAt(new Date())
        showToast('Journal entry created', 'success')
      } catch (error: any) {
        showToast(error.message || 'Failed to create journal entry', 'error')
      }
    },
    [createMutation, lines, showToast]
  )
  
  // Handle save (auto-save for existing entries)
  const handleSave = useCallback(async () => {
    if (!entryId) {
      // If no entry exists, create one
      const formData = watch()
      await handleSubmit(onSubmit)()
      return
    }
    
    // Auto-save lines if entry exists
    if (lines.length > 0) {
      try {
        await bulkUpsertMutation.mutateAsync({
          entryId,
          lines: lines.map((line) => ({
            client_row_id: line.client_row_id,
            line_id: line.line_id,
            account_code: line.account_code,
            description: line.description,
            debit_amount: line.debit_amount,
            credit_amount: line.credit_amount,
            cost_center: line.cost_center,
            department: line.department,
            location: line.location,
            project: line.project,
            currency: line.currency,
            fx_rate: line.fx_rate,
          })),
        })
        setLastSavedAt(new Date())
        showToast('Entry saved', 'success')
      } catch (error: any) {
        showToast(error.message || 'Failed to save entry', 'error')
      }
    }
  }, [entryId, lines, bulkUpsertMutation, watch, handleSubmit, onSubmit, showToast])

  // Post entry
  const handlePost = useCallback(async () => {
    if (!entryId) {
      showToast('Please save the entry first', 'error')
      return
    }

    // Validate first
    await handleValidate()
    if (!validationResult?.is_valid) {
      showToast('Cannot post: Entry has validation errors', 'error')
      return
    }

    try {
      await postMutation.mutateAsync(entryId)
      showToast('Journal entry posted successfully', 'success')
      router.push('/journal-entries')
    } catch (error: any) {
      showToast(error.message || 'Failed to post journal entry', 'error')
    }
  }, [entryId, handleValidate, validationResult, postMutation, showToast, router])

  // Form mode component
  const formMode = (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Entry Header</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="entry_date" className="block text-sm font-medium text-gray-700 mb-1">
              Entry Date *
            </label>
            <input
              type="date"
              id="entry_date"
              {...register('entry_date', { required: 'Entry date is required' })}
              className="input"
              disabled={isLocked}
            />
            {errors.entry_date && <p className="text-red-600 text-sm mt-1">{errors.entry_date.message}</p>}
          </div>

          <div>
            <label htmlFor="period_id" className="block text-sm font-medium text-gray-700 mb-1">
              Period *
            </label>
            <select
              id="period_id"
              {...register('period_id', { required: 'Period is required' })}
              className="input"
              disabled={isLocked}
            >
              <option value="">Select Period</option>
              {periods?.map((period) => (
                <option key={period.id} value={period.id}>
                  {period.period_name} ({formatDate(period.start_date)} - {formatDate(period.end_date)})
                </option>
              ))}
            </select>
            {errors.period_id && <p className="text-red-600 text-sm mt-1">{errors.period_id.message}</p>}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <input
              type="text"
              id="description"
              {...register('description', { required: 'Description is required' })}
              className="input"
              placeholder="Enter journal entry description"
              disabled={isLocked}
            />
            {errors.description && <p className="text-red-600 text-sm mt-1">{errors.description.message}</p>}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Journal Lines</h2>
        <p className="text-gray-600 text-sm mb-4">
          Switch to Grid mode for faster entry with Excel-like features
        </p>
        <div className="space-y-4">
          {lines.map((line, index) => (
            <div key={line.client_row_id || index} className="p-4 border border-gray-200 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Account</label>
                  <input
                    type="text"
                    value={line.account_code}
                    onChange={(e) => {
                      if (!isLocked) {
                        const newLines = [...lines]
                        newLines[index] = { ...line, account_code: e.target.value }
                        setLines(newLines)
                      }
                    }}
                    className="input"
                    placeholder="Account code"
                    disabled={isLocked}
                  />
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
                        setLines(newLines)
                      }
                    }}
                    className="input"
                    disabled={isLocked}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Debit</label>
                    <input
                      type="number"
                      value={line.debit_amount || 0}
                      onChange={(e) => {
                        if (!isLocked) {
                          const newLines = [...lines]
                          newLines[index] = {
                            ...line,
                            debit_amount: parseFloat(e.target.value) || 0,
                            credit_amount: 0,
                          }
                          setLines(newLines)
                        }
                      }}
                      className="input"
                      step="0.01"
                      disabled={isLocked}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Credit</label>
                    <input
                      type="number"
                      value={line.credit_amount || 0}
                      onChange={(e) => {
                        if (!isLocked) {
                          const newLines = [...lines]
                          newLines[index] = {
                            ...line,
                            credit_amount: parseFloat(e.target.value) || 0,
                            debit_amount: 0,
                          }
                          setLines(newLines)
                        }
                      }}
                      className="input"
                      step="0.01"
                      disabled={isLocked}
                    />
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
                    debit_amount: 0,
                    credit_amount: 0,
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
      </div>
    </div>
  )

  // Grid mode component
  const gridMode = (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Entry Header</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="grid_entry_date" className="block text-sm font-medium text-gray-700 mb-1">
              Entry Date *
            </label>
            <input
              type="date"
              id="grid_entry_date"
              {...register('entry_date', { required: 'Entry date is required' })}
              className="input"
              disabled={isLocked}
            />
          </div>
          <div>
            <label htmlFor="grid_period_id" className="block text-sm font-medium text-gray-700 mb-1">
              Period *
            </label>
            <select
              id="grid_period_id"
              {...register('period_id', { required: 'Period is required' })}
              className="input"
              disabled={isLocked}
            >
              <option value="">Select Period</option>
              {periods?.map((period) => (
                <option key={period.id} value={period.id}>
                  {period.period_name}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label htmlFor="grid_description" className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <input
              type="text"
              id="grid_description"
              {...register('description', { required: 'Description is required' })}
              className="input"
              disabled={isLocked}
            />
          </div>
        </div>
      </div>

      <div className="card">
        <JournalEntryGrid
          lines={lines}
          onLinesChange={isLocked ? () => {} : handleLinesChange}
          legalEntityId={selectedEntityId || undefined}
          bookId={selectedBookId || undefined}
          defaultCurrency="USD"
        />
      </div>
    </div>
  )

  return (
    <div className="flex flex-col h-screen">
      {/* Global Toolbar */}
      {entryId && (
        <GlobalToolbar
          entityId={selectedEntityId || undefined}
          entityName={selectedEntity?.entity_name}
          bookId={selectedBookId || undefined}
          bookName={selectedBook?.book_name}
          periodId={watchedValues.period_id || undefined}
          periodName={selectedPeriod?.period_name}
          status={entryStatus}
          isPosted={entryStatus === 'POSTED'}
          lastSavedAt={lastSavedAt || undefined}
          canSubmit={false} // Journal entries don't use approval workflow
          canApprove={false}
          canReject={false}
          canPost={entryStatus === 'DRAFT' && validationResult?.is_valid}
          canReverse={entryStatus === 'POSTED'}
          onPost={handlePost}
          onSave={handleSave}
          isLocked={isLocked}
        />
      )}
      
      <div className="flex-1 overflow-auto p-6">
        {/* Approval Status Banner */}
        {entryId && entryData && entryStatus !== 'DRAFT' && (
          <ApprovalStatusBanner
            status={entryStatus}
            postedBy={entryData.posted_by}
            postedAt={entryData.posted_at}
            className="mb-6"
          />
        )}
        
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {entryId ? 'Edit Journal Entry' : 'Create Journal Entry'}
              </h1>
              <p className="text-gray-600 mt-1">Enter journal entry details and lines</p>
            </div>
            {!entryId && (
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

          <DualModeEditor
            formMode={formMode}
            gridMode={gridMode}
            defaultMode={mode}
            onModeChange={setMode}
          />

          {/* Validation Results */}
          {validationResult && (
            <div className={`card ${validationResult.is_valid ? 'bg-green-50' : 'bg-red-50'}`}>
              <h3 className="font-semibold mb-2">
                {validationResult.is_valid ? '✓ Entry is Valid' : '✗ Validation Errors'}
              </h3>
              {validationResult.totals && (
                <div className="mb-2">
                  <p>Debits: {validationResult.totals.debit}</p>
                  <p>Credits: {validationResult.totals.credit}</p>
                  <p>Balance: {validationResult.totals.balance}</p>
                </div>
              )}
              {validationResult.errors && validationResult.errors.length > 0 && (
                <ul className="list-disc list-inside">
                  {validationResult.errors.map((error: any, index: number) => (
                    <li key={index} className="text-sm">
                      {error.scope === 'line' ? `Line ${error.line_id || error.client_row_id}: ` : 'Header: '}
                      {error.field}: {error.message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
