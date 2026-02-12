'use client'

import { useMemo, useCallback, useRef, useState, useEffect } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi, CellValueChangedEvent } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { useGLAccounts } from '@/hooks/useGLAccounts'
import { useDimensions } from '@/hooks/useDimensions'
import { formatCurrency } from '@/lib/utils/format'
import { GridBulkActions } from './GridBulkActions'
import { ContextualSidebar } from './ContextualSidebar'
import { useUndoRedo, useUndoRedoKeyboard } from '@/hooks/useUndoRedo'
import { handlePasteEvent, mapPastedDataToGrid, showPasteNotification } from '@/utils/excelPasteHandler'
import { useToast } from '@/hooks/useToast'

export interface JournalLine {
  client_row_id?: string
  line_id?: string
  account_code: string
  account_name?: string
  description: string
  debit_amount: number
  credit_amount: number
  currency?: string
  fx_rate?: number
  cost_center?: string
  department?: string
  location?: string
  project?: string
  customer_id?: string
  vendor_id?: string
  tax_code?: string
  _errors?: Record<string, string>
}

interface JournalEntryGridProps {
  lines: JournalLine[]
  onLinesChange: (lines: JournalLine[]) => void
  onValidationChange?: (isValid: boolean, errors: any[]) => void
  legalEntityId?: string
  bookId?: string
  defaultCurrency?: string
  className?: string
}

/**
 * Journal Entry Grid Component
 * Excel-like grid for fast journal entry line entry
 * Supports: keyboard nav, copy/paste, bulk operations, inline validation
 */
export function JournalEntryGrid({
  lines,
  onLinesChange,
  onValidationChange,
  legalEntityId,
  bookId,
  defaultCurrency = 'USD',
  className,
}: JournalEntryGridProps) {
  const gridRef = useRef<typeof AgGridReact>(null)
  const [gridApi, setGridApi] = useState<GridApi | null>(null)
  const [columnApi, setColumnApi] = useState<ColumnApi | null>(null)
  const [lastUsedAccount, setLastUsedAccount] = useState<string>('')
  const [lastUsedDimensions, setLastUsedDimensions] = useState<{
    cost_center?: string
    department?: string
    location?: string
  }>({})
  const [selectedRowIndex, setSelectedRowIndex] = useState<number | null>(null)
  const [currentRow, setCurrentRow] = useState(0)
  const [currentCol, setCurrentCol] = useState(0)
  const { showToast } = useToast()

  // Initialize undo/redo with lines state
  const { canUndo, canRedo, undo, redo, updateCells } = useUndoRedo({})

  // Note: Undo/Redo state is managed internally by the hook
  // We update it on cell changes, but don't reset on external changes
  // to preserve user's undo history

  // Keyboard shortcuts for undo/redo
  const { handleKeyDown } = useUndoRedoKeyboard(undo, redo, canUndo, canRedo)

  useEffect(() => {
    const handler = handleKeyDown as any
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleKeyDown])

  // Fetch accounts and dimensions for dropdowns
  const { data: accountsData } = useGLAccounts({ legal_entity_id: legalEntityId })
  const { data: dimensionsData } = useDimensions({ legal_entity_id: legalEntityId })

  const accounts = useMemo(() => {
    return accountsData || []
  }, [accountsData])

  const dimensions = useMemo(() => {
    return Array.isArray(dimensionsData) ? dimensionsData : []
  }, [dimensionsData])

  // Validation
  const validateLines = useCallback(
    (linesToValidate: JournalLine[]): { isValid: boolean; errors: any[]; totalDebits: number; totalCredits: number; balance: number } => {
      const errors: any[] = []
      let totalDebits = 0
      let totalCredits = 0

      linesToValidate.forEach((line, index) => {
        const lineErrors: Record<string, string> = {}

        if (!line.account_code) {
          lineErrors.account_code = 'Account is required'
        }
        if (!line.description) {
          lineErrors.description = 'Description is required'
        }
        if (line.debit_amount > 0 && line.credit_amount > 0) {
          lineErrors.debit_amount = 'Cannot have both debit and credit'
          lineErrors.credit_amount = 'Cannot have both debit and credit'
        }
        if (line.debit_amount === 0 && line.credit_amount === 0) {
          lineErrors.debit_amount = 'Must have either debit or credit'
        }
        if (!line.cost_center) {
          lineErrors.cost_center = 'Cost center is required'
        }
        if (!line.department) {
          lineErrors.department = 'Department is required'
        }
        if (!line.location) {
          lineErrors.location = 'Location is required'
        }

        if (Object.keys(lineErrors).length > 0) {
          errors.push({ lineIndex: index, errors: lineErrors })
        }

        totalDebits += line.debit_amount || 0
        totalCredits += line.credit_amount || 0
      })

      // Balance check
      const balance = Math.abs(totalDebits - totalCredits)
      const isBalanced = balance < 0.01

      // Update errors in lines
      const linesWithErrors = linesToValidate.map((line, index) => {
        const errorEntry = errors.find((e) => e.lineIndex === index)
        return {
          ...line,
          _errors: errorEntry?.errors || {},
        }
      })

      onLinesChange(linesWithErrors)
      onValidationChange?.(isBalanced && errors.length === 0, errors)

      return { isValid: isBalanced && errors.length === 0, errors, totalDebits, totalCredits, balance }
    },
    [lines, onLinesChange, lastUsedDimensions, onValidationChange]
  )

  // Column definitions - moved before handlePaste to fix declaration order
  const columnDefs = useMemo<ColDef[]>(
    () => [
      {
        headerName: 'Account',
        field: 'account_code',
        width: 150,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
          values: accounts.map((acc) => acc.account_code),
        },
        cellRenderer: (params: any) => {
          if (params.value) {
            const account = accounts.find((acc) => acc.account_code === params.value)
            return account ? `${account.account_code} - ${account.account_name}` : params.value
          }
          return ''
        },
        cellClass: (params: any) => {
          return params.data?._errors?.account_code ? 'ag-cell-error' : ''
        },
        tooltipValueGetter: (params: any) => params.data?._errors?.account_code || '',
      },
      {
        headerName: 'Description',
        field: 'description',
        width: 250,
        editable: true,
        cellClass: (params: any) => {
          return params.data?._errors?.description ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Debit',
        field: 'debit_amount',
        width: 120,
        editable: true,
        type: 'numericColumn',
        valueFormatter: (params: any) => {
          return params.value ? formatCurrency(params.value, defaultCurrency) : ''
        },
        valueParser: (params: any) => {
          const value = parseFloat(params.newValue?.replace(/[^0-9.-]/g, '') || '0')
          return isNaN(value) ? 0 : value
        },
        cellClass: (params: any) => {
          return params.data?._errors?.debit_amount ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Credit',
        field: 'credit_amount',
        width: 120,
        editable: true,
        type: 'numericColumn',
        valueFormatter: (params: any) => {
          return params.value ? formatCurrency(params.value, defaultCurrency) : ''
        },
        valueParser: (params: any) => {
          const value = parseFloat(params.newValue?.replace(/[^0-9.-]/g, '') || '0')
          return isNaN(value) ? 0 : value
        },
        cellClass: (params: any) => {
          return params.data?._errors?.credit_amount ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Cost Center',
        field: 'cost_center',
        width: 130,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
          values: dimensions.filter((d) => d.dimension_name === 'cost_center' || d.dimension_type === 'cost_center').map((d) => d.dimension_name || d.dimension_type),
        },
        cellClass: (params: any) => {
          return params.data?._errors?.cost_center ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Department',
        field: 'department',
        width: 130,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
          values: dimensions.filter((d) => d.dimension_type === 'department').map((d) => d.dimension_name || d.dimension_type),
        },
        cellClass: (params: any) => {
          return params.data?._errors?.department ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Location',
        field: 'location',
        width: 130,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
          values: dimensions.filter((d) => d.dimension_name === 'location' || d.dimension_type === 'location').map((d) => d.dimension_name || d.dimension_type),
        },
        cellClass: (params: any) => {
          return params.data?._errors?.location ? 'ag-cell-error' : ''
        },
      },
    ],
    [accounts, dimensions, defaultCurrency]
  )

  // Handle paste event
  const handlePaste = useCallback((event: ClipboardEvent) => {
    if (!gridApi) return

    const focusedCell = gridApi.getFocusedCell()
    if (!focusedCell) return

    const columnOrder = columnDefs.map(col => col.field || '')
    const parsed = handlePasteEvent(event, columnOrder, focusedCell.rowIndex || 0, focusedCell.column?.getColId() ? columnOrder.indexOf(focusedCell.column.getColId()) : 0)

    if (parsed) {
      event.preventDefault()

      // Map pasted data to grid updates
      const updates: Record<string, any> = {}
      const newLines = [...lines]

      parsed.rows.forEach((row, rowOffset) => {
        const targetRowIndex = (focusedCell.rowIndex || 0) + rowOffset

        // Add new rows if needed
        while (targetRowIndex >= newLines.length) {
          newLines.push({
            client_row_id: `temp-${Date.now()}-${newLines.length + 1}`,
            account_code: '',
            description: '',
            debit_amount: 0,
            credit_amount: 0,
            currency: defaultCurrency,
          })
        }

        row.forEach((cell, colOffset) => {
          const targetColIndex = (focusedCell.column?.getColId() ? columnOrder.indexOf(focusedCell.column.getColId()) : 0) + colOffset
          if (targetColIndex < columnOrder.length) {
            const field = columnOrder[targetColIndex]
            const cellKey = `${targetRowIndex}-${field}`
            updates[cellKey] = cell

            // Update the line
            if (newLines[targetRowIndex]) {
              (newLines[targetRowIndex] as any)[field] = cell
            }
          }
        })
      })

      // Apply updates via undo/redo
      updateCells(updates)
      onLinesChange(newLines)
      validateLines(newLines)
      showPasteNotification(parsed.rowCount, parsed.columnCount, showToast)
    }
  }, [gridApi, columnDefs, lines, onLinesChange, defaultCurrency, showToast, updateCells, validateLines])

  // Handle cell value changes
  const handleCellValueChanged = useCallback(
    (event: CellValueChangedEvent) => {
      const updatedLines = lines.map((line, index) => {
        if (index === event.rowIndex) {
          const updated = { ...line, ...event.data }
          // Remember last used values
          if (event.colDef.field === 'account_code') {
            setLastUsedAccount(updated.account_code)
          }
          if (event.colDef.field === 'cost_center' || event.colDef.field === 'department' || event.colDef.field === 'location') {
            setLastUsedDimensions({
              ...lastUsedDimensions,
              [event.colDef.field]: updated[event.colDef.field as keyof JournalLine] as string,
            })
          }
          // Auto-clear opposite amount if one is entered
          if (event.colDef.field === 'debit_amount' && updated.debit_amount > 0) {
            updated.credit_amount = 0
          }
          if (event.colDef.field === 'credit_amount' && updated.credit_amount > 0) {
            updated.debit_amount = 0
          }

          // Update undo/redo state
          const updates: Record<string, any> = {}
          Object.keys(updated).forEach(key => {
            updates[`${index}-${key}`] = (updated as any)[key]
          })
          updateCells(updates)

          return updated
        }
        return line
      })
      onLinesChange(updatedLines)
      validateLines(updatedLines)
    },
    [lines, onLinesChange, lastUsedDimensions, updateCells, validateLines]
  )

  // Default row data
  const defaultColDef = useMemo(
    () => ({
      resizable: true,
      sortable: false,
      filter: false,
    }),
    []
  )

  // Add new row
  const addRow = useCallback(() => {
    const newLine: JournalLine = {
      client_row_id: `temp-${Date.now()}-${Math.random()}`,
      account_code: lastUsedAccount,
      description: '',
      debit_amount: 0,
      credit_amount: 0,
      currency: defaultCurrency,
      cost_center: lastUsedDimensions.cost_center,
      department: lastUsedDimensions.department,
      location: lastUsedDimensions.location,
    }
    onLinesChange([...lines, newLine])
    setTimeout(() => {
      gridApi?.setFocusedCell(lines.length, 'account_code')
      gridApi?.startEditingCell({ rowIndex: lines.length, colKey: 'account_code' })
    }, 100)
  }, [lines, onLinesChange, lastUsedAccount, lastUsedDimensions, defaultCurrency, gridApi])

  // Delete selected rows
  const deleteSelectedRows = useCallback(() => {
    if (!gridApi) return
    const selectedRows = gridApi.getSelectedRows()
    if (selectedRows.length === 0) return

    const selectedIndices = new Set(selectedRows.map((row: JournalLine) => lines.indexOf(row)))
    const newLines = lines.filter((_, index) => !selectedIndices.has(index))
    onLinesChange(newLines)
  }, [gridApi, lines, onLinesChange])

  // Fill down (Ctrl+D)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'd' && gridApi) {
        event.preventDefault()
        const focusedCell = gridApi.getFocusedCell()
        if (focusedCell) {
          const rowIndex = focusedCell.rowIndex
          const colKey = focusedCell.column?.getColId()
          if (rowIndex > 0 && colKey) {
            const value = lines[rowIndex - 1]?.[colKey as keyof JournalLine]
            if (value !== undefined) {
              const updated = [...lines]
              updated[rowIndex] = { ...updated[rowIndex], [colKey]: value }
              onLinesChange(updated)
            }
          }
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [gridApi, lines, onLinesChange])

  // Grid ready callback
  const onGridReady = useCallback((params: any) => {
    setGridApi(params.api)
    setColumnApi(params.columnApi)
  }, [])

  // Calculate totals
  const totals = useMemo(() => {
    const totalDebits = lines.reduce((sum, line) => sum + (line.debit_amount || 0), 0)
    const totalCredits = lines.reduce((sum, line) => sum + (line.credit_amount || 0), 0)
    const balance = totalDebits - totalCredits
    return { totalDebits, totalCredits, balance }
  }, [lines])

  // Add error cell styling
  useEffect(() => {
    const style = document.createElement('style')
    style.textContent = `
      .ag-cell-error {
        background-color: #fee2e2 !important;
        border: 1px solid #ef4444 !important;
      }
    `
    document.head.appendChild(style)
    return () => {
      if (document.head.contains(style)) {
        document.head.removeChild(style)
      }
    }
  }, [])

  // Validate on mount and when lines change
  useEffect(() => {
    if (lines.length > 0) {
      validateLines(lines)
    }
  }, [lines, validateLines]) // Add lines and validateLines to the dependency array

  // Bulk apply dimension
  const handleBulkApplyDimension = useCallback(
    (dimension: 'cost_center' | 'department' | 'location', value: string) => {
      if (!gridApi) return
      const selectedRows = gridApi.getSelectedRows()
      if (selectedRows.length === 0) return

      const selectedIndices = new Set(selectedRows.map((row: JournalLine) => lines.indexOf(row)))
      const updated = lines.map((line, index) => {
        if (selectedIndices.has(index)) {
          return { ...line, [dimension]: value }
        }
        return line
      })
      onLinesChange(updated)
    },
    [gridApi, lines, onLinesChange]
  )

  // Bulk apply account
  const handleBulkApplyAccount = useCallback(
    (accountCode: string) => {
      if (!gridApi) return
      const selectedRows = gridApi.getSelectedRows()
      if (selectedRows.length === 0) return

      const selectedIndices = new Set(selectedRows.map((row: JournalLine) => lines.indexOf(row)))
      const updated = lines.map((line, index) => {
        if (selectedIndices.has(index)) {
          return { ...line, account_code: accountCode }
        }
        return line
      })
      onLinesChange(updated)
    },
    [gridApi, lines, onLinesChange]
  )

  // Prepare dimensions for bulk actions
  const dimensionOptions = useMemo(() => {
    return dimensions.map((dim) => ({
      type: dim.dimension_name || dim.dimension_type,
      value: dim.dimension_name || dim.dimension_type,
    }))
  }, [dimensions])

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={addRow} className="btn-secondary text-sm">
            Add Row
          </button>
          <button onClick={deleteSelectedRows} className="btn-secondary text-sm">
            Delete Selected
          </button>
          <div className="h-6 w-px bg-gray-300 mx-2" />
          <button 
            onClick={undo} 
            disabled={!canUndo}
            className="btn-secondary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            title="Undo (Ctrl+Z)"
          >
            Undo
          </button>
          <button 
            onClick={redo} 
            disabled={!canRedo}
            className="btn-secondary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            title="Redo (Ctrl+Y)"
          >
            Redo
          </button>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-600">
            Total Debits: <strong>{formatCurrency(totals.totalDebits, defaultCurrency)}</strong>
          </span>
          <span className="text-gray-600">
            Total Credits: <strong>{formatCurrency(totals.totalCredits, defaultCurrency)}</strong>
          </span>
          <span className={totals.balance === 0 ? 'text-green-600' : 'text-red-600'}>
            Balance: <strong>{formatCurrency(totals.balance, defaultCurrency)}</strong>
          </span>
        </div>
      </div>

      {/* Bulk Actions */}
      <GridBulkActions
        selectedCount={gridApi?.getSelectedRows().length || 0}
        onApplyDimension={handleBulkApplyDimension}
        onApplyAccount={handleBulkApplyAccount}
        dimensions={dimensionOptions}
        accounts={accounts.map((acc) => ({ code: acc.account_code, name: acc.account_name }))}
      />

      {/* Grid */}
      <div 
        className="ag-theme-alpine" 
        style={{ height: '600px', width: '100%' }}
        onPaste={handlePaste as any}
      >
        <AgGridReact
          ref={gridRef}
          rowData={lines}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onGridReady={onGridReady}
          onCellValueChanged={handleCellValueChanged}
          onRowClicked={(event: { node: { rowIndex: number | null } }) => {
            setSelectedRowIndex(event.node.rowIndex ?? null)
          }}
          onCellFocused={(event: { rowIndex: number | null; column?: { getColId: () => string } }) => {
            if (event.rowIndex !== null) setCurrentRow(event.rowIndex)
            if (event.column) {
              const colIndex = columnDefs.findIndex(col => col.field === event.column?.getColId())
              if (colIndex >= 0) setCurrentCol(colIndex)
            }
          }}
          rowSelection="multiple"
          suppressRowClickSelection={false}
          enableRangeSelection={true}
          enableFillHandle={true}
          enableRangeHandle={true}
          copyHeadersToClipboard={true}
          copyGroupHeadersToClipboard={true}
          animateRows={false}
          getRowId={(params: { data: JournalLine; node: { rowIndex: number | null } }) => params.data.client_row_id || params.data.line_id || `row-${params.node.rowIndex}`}
        />
      </div>

      {/* Right-side Row Detail Panel (Airtable style) */}
      {selectedRowIndex !== null && lines[selectedRowIndex] && (
        <ContextualSidebar
          isOpen={selectedRowIndex !== null}
          onClose={() => setSelectedRowIndex(null)}
          title={`Line ${selectedRowIndex + 1} Details`}
          width="w-96"
        >
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Line Information</h3>
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-xs text-gray-500">Account</dt>
                  <dd className="text-gray-900">{lines[selectedRowIndex].account_code || '-'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Description</dt>
                  <dd className="text-gray-900">{lines[selectedRowIndex].description || '-'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Debit</dt>
                  <dd className="text-gray-900">
                    {lines[selectedRowIndex].debit_amount
                      ? formatCurrency(lines[selectedRowIndex].debit_amount, defaultCurrency)
                      : '-'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Credit</dt>
                  <dd className="text-gray-900">
                    {lines[selectedRowIndex].credit_amount
                      ? formatCurrency(lines[selectedRowIndex].credit_amount, defaultCurrency)
                      : '-'}
                  </dd>
                </div>
              </dl>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Dimensions</h3>
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-xs text-gray-500">Cost Center</dt>
                  <dd className="text-gray-900">{lines[selectedRowIndex].cost_center || '-'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Department</dt>
                  <dd className="text-gray-900">{lines[selectedRowIndex].department || '-'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Location</dt>
                  <dd className="text-gray-900">{lines[selectedRowIndex].location || '-'}</dd>
                </div>
                {lines[selectedRowIndex].project && (
                  <div>
                    <dt className="text-xs text-gray-500">Project</dt>
                    <dd className="text-gray-900">{lines[selectedRowIndex].project}</dd>
                  </div>
                )}
              </dl>
            </div>

            {lines[selectedRowIndex]._errors && Object.keys(lines[selectedRowIndex]._errors || {}).length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <h4 className="text-xs font-semibold text-red-800 mb-2">Validation Errors</h4>
                <ul className="text-xs text-red-700 space-y-1">
                  {Object.entries(lines[selectedRowIndex]._errors || {}).map(([field, message]) => (
                    <li key={field}>
                      <strong>{field}:</strong> {message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </ContextualSidebar>
      )}

      {/* Footer with totals */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 py-2 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">
            {lines.length} line{lines.length !== 1 ? 's' : ''}
          </span>
          <div className="flex gap-4">
            <span>
              Debits: <strong>{formatCurrency(totals.totalDebits, defaultCurrency)}</strong>
            </span>
            <span>
              Credits: <strong>{formatCurrency(totals.totalCredits, defaultCurrency)}</strong>
            </span>
            <span className={totals.balance === 0 ? 'text-green-600' : 'text-red-600'}>
              Balance: <strong>{formatCurrency(totals.balance, defaultCurrency)}</strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}