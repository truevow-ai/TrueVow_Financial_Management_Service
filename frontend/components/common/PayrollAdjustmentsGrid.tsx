'use client'

import { useMemo, useCallback, useRef, useState, useEffect } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, CellValueChangedEvent } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { formatCurrency } from '@/lib/utils/format'

export interface PayrollAdjustment {
  client_row_id?: string
  adjustment_id?: string
  employee_id: string
  employee_name?: string
  component_type: 'BONUS' | 'COMMISSION' | 'ADJUSTMENT' | 'DEDUCTION'
  amount: number
  currency?: string
  memo?: string
  cost_center?: string
  department?: string
  location?: string
  _errors?: Record<string, string>
}

interface PayrollAdjustmentsGridProps {
  adjustments: PayrollAdjustment[]
  onAdjustmentsChange: (adjustments: PayrollAdjustment[]) => void
  onValidationChange?: (isValid: boolean, errors: any[]) => void
  employees?: Array<{ id: string; employee_name: string; employee_number: string }>
  defaultCurrency?: string
  className?: string
}

/**
 * Payroll Adjustments Grid Component
 * Excel-like grid for payroll run adjustments (bonuses, commissions, one-offs)
 * Supports: keyboard nav, copy/paste, bulk operations
 */
export function PayrollAdjustmentsGrid({
  adjustments,
  onAdjustmentsChange,
  onValidationChange,
  employees = [],
  defaultCurrency = 'USD',
  className,
}: PayrollAdjustmentsGridProps) {
  const gridRef = useRef<typeof AgGridReact>(null)
  const [gridApi, setGridApi] = useState<GridApi | null>(null)
  const [lastUsedEmployee, setLastUsedEmployee] = useState<string>('')
  const [lastUsedComponent, setLastUsedComponent] = useState<'BONUS' | 'COMMISSION' | 'ADJUSTMENT' | 'DEDUCTION'>('BONUS')

  // Column definitions
  const columnDefs = useMemo<ColDef[]>(
    () => [
      {
        headerName: 'Employee',
        field: 'employee_id',
        width: 200,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
          values: employees.map((emp) => emp.id),
        },
        cellRenderer: (params: any) => {
          if (params.value) {
            const employee = employees.find((emp) => emp.id === params.value)
            return employee ? `${employee.employee_number} - ${employee.employee_name}` : params.value
          }
          return ''
        },
        cellClass: (params: any) => {
          return params.data?._errors?.employee_id ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Component Type',
        field: 'component_type',
        width: 150,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
          values: ['BONUS', 'COMMISSION', 'ADJUSTMENT', 'DEDUCTION'],
        },
        cellRenderer: (params: any) => {
          const type = params.value
          const colors: Record<string, string> = {
            BONUS: 'bg-green-100 text-green-800',
            COMMISSION: 'bg-blue-100 text-blue-800',
            ADJUSTMENT: 'bg-yellow-100 text-yellow-800',
            DEDUCTION: 'bg-red-100 text-red-800',
          }
          return (
            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${colors[type] || ''}`}>{type}</span>
          )
        },
        cellClass: (params: any) => {
          return params.data?._errors?.component_type ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Amount',
        field: 'amount',
        width: 120,
        editable: true,
        type: 'numericColumn',
        valueFormatter: (params: any) => {
          return params.value ? formatCurrency(params.value, params.data?.currency || defaultCurrency) : ''
        },
        valueParser: (params: any) => {
          const value = parseFloat(params.newValue?.replace(/[^0-9.-]/g, '') || '0')
          return isNaN(value) ? 0 : value
        },
        cellClass: (params: any) => {
          return params.data?._errors?.amount ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Currency',
        field: 'currency',
        width: 100,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
          values: ['USD', 'EUR', 'GBP', 'AED'],
        },
      },
      {
        headerName: 'Memo',
        field: 'memo',
        width: 250,
        editable: true,
      },
      {
        headerName: 'Cost Center',
        field: 'cost_center',
        width: 130,
        editable: true,
        cellClass: (params: any) => {
          return params.data?._errors?.cost_center ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Department',
        field: 'department',
        width: 130,
        editable: true,
        cellClass: (params: any) => {
          return params.data?._errors?.department ? 'ag-cell-error' : ''
        },
      },
      {
        headerName: 'Location',
        field: 'location',
        width: 130,
        editable: true,
        cellClass: (params: any) => {
          return params.data?._errors?.location ? 'ag-cell-error' : ''
        },
      },
    ],
    [employees, defaultCurrency]
  )

  const defaultColDef = useMemo(
    () => ({
      resizable: true,
      sortable: false,
      filter: false,
    }),
    []
  )

  // Validation
  const validateAdjustments = useCallback(
    (adjustmentsToValidate: PayrollAdjustment[]): { isValid: boolean; errors: any[] } => {
      const errors: any[] = []

      adjustmentsToValidate.forEach((adj, index) => {
        const adjErrors: Record<string, string> = {}

        if (!adj.employee_id) {
          adjErrors.employee_id = 'Employee is required'
        }
        if (!adj.component_type) {
          adjErrors.component_type = 'Component type is required'
        }
        if (!adj.amount || adj.amount === 0) {
          adjErrors.amount = 'Amount must be greater than 0'
        }
        if (!adj.cost_center) {
          adjErrors.cost_center = 'Cost center is required'
        }
        if (!adj.department) {
          adjErrors.department = 'Department is required'
        }
        if (!adj.location) {
          adjErrors.location = 'Location is required'
        }

        if (Object.keys(adjErrors).length > 0) {
          errors.push({ adjustmentIndex: index, errors: adjErrors })
        }
      })

      const adjustmentsWithErrors = adjustmentsToValidate.map((adj, index) => {
        const errorEntry = errors.find((e) => e.adjustmentIndex === index)
        return {
          ...adj,
          _errors: errorEntry?.errors || {},
        }
      })

      onAdjustmentsChange(adjustmentsWithErrors)
      onValidationChange?.(errors.length === 0, errors)

      return { isValid: errors.length === 0, errors }
    },
    [adjustments, onAdjustmentsChange, onValidationChange]
  )

  // Handle cell value changes
  const handleCellValueChanged = useCallback(
    (event: CellValueChangedEvent) => {
      const updated = adjustments.map((adj, index) => {
        if (index === event.rowIndex) {
          const updatedAdj = { ...adj, ...event.data }
          // Remember last used values
          if (event.colDef.field === 'employee_id') {
            setLastUsedEmployee(updatedAdj.employee_id)
          }
          if (event.colDef.field === 'component_type') {
            setLastUsedComponent(updatedAdj.component_type)
          }
          return updatedAdj
        }
        return adj
      })
      onAdjustmentsChange(updated)
      validateAdjustments(updated)
    },
    [adjustments, onAdjustmentsChange, validateAdjustments]
  )

  // Add new row
  const addRow = useCallback(() => {
    const newAdjustment: PayrollAdjustment = {
      client_row_id: `temp-${Date.now()}-${Math.random()}`,
      employee_id: lastUsedEmployee,
      component_type: lastUsedComponent,
      amount: 0,
      currency: defaultCurrency,
      memo: '',
    }
    onAdjustmentsChange([...adjustments, newAdjustment])
    setTimeout(() => {
      gridApi?.setFocusedCell(adjustments.length, 'employee_id')
      gridApi?.startEditingCell({ rowIndex: adjustments.length, colKey: 'employee_id' })
    }, 100)
  }, [adjustments, onAdjustmentsChange, lastUsedEmployee, lastUsedComponent, defaultCurrency, gridApi])

  // Delete selected rows
  const deleteSelectedRows = useCallback(() => {
    if (!gridApi) return
    const selectedRows = gridApi.getSelectedRows()
    if (selectedRows.length === 0) return

    const selectedIndices = new Set(selectedRows.map((row: PayrollAdjustment) => adjustments.indexOf(row)))
    const newAdjustments = adjustments.filter((_, index) => !selectedIndices.has(index))
    onAdjustmentsChange(newAdjustments)
  }, [gridApi, adjustments, onAdjustmentsChange])

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
            const value = adjustments[rowIndex - 1]?.[colKey as keyof PayrollAdjustment]
            if (value !== undefined) {
              const updated = [...adjustments]
              updated[rowIndex] = { ...updated[rowIndex], [colKey]: value }
              onAdjustmentsChange(updated)
            }
          }
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [gridApi, adjustments, onAdjustmentsChange])

  // Grid ready callback
  const onGridReady = useCallback((params: any) => {
    setGridApi(params.api)
  }, [])

  // Calculate totals
  const totals = useMemo(() => {
    const total = adjustments.reduce((sum, adj) => sum + (adj.amount || 0), 0)
    const byType = adjustments.reduce(
      (acc, adj) => {
        const type = adj.component_type || 'ADJUSTMENT'
        acc[type] = (acc[type] || 0) + (adj.amount || 0)
        return acc
      },
      {} as Record<string, number>
    )
    return { total, byType }
  }, [adjustments])

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

  // Validate on mount
  useEffect(() => {
    if (adjustments.length > 0) {
      validateAdjustments(adjustments)
    }
  }, [adjustments, validateAdjustments]) // Add adjustments and validateAdjustments to the dependency array

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
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-600">
            Total: <strong>{formatCurrency(totals.total, defaultCurrency)}</strong>
          </span>
        </div>
      </div>

      {/* Grid */}
      <div className="ag-theme-alpine" style={{ height: '600px', width: '100%' }}>
        <AgGridReact
          ref={gridRef}
          rowData={adjustments}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onGridReady={onGridReady}
          onCellValueChanged={handleCellValueChanged}
          rowSelection="multiple"
          suppressRowClickSelection={true}
          enableRangeSelection={true}
          enableFillHandle={true}
          enableRangeHandle={true}
          copyHeadersToClipboard={true}
          animateRows={false}
          getRowId={(params: { data: PayrollAdjustment; node: { rowIndex: number | null } }) => params.data.client_row_id || params.data.adjustment_id || `row-${params.node.rowIndex}`}
        />
      </div>

      {/* Footer with totals */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 py-2 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">
            {adjustments.length} adjustment{adjustments.length !== 1 ? 's' : ''}
          </span>
          <div className="flex gap-4">
            {Object.entries(totals.byType).map(([type, amount]) => (
              <span key={type}>
                {type}: <strong>{formatCurrency(amount, defaultCurrency)}</strong>
              </span>
            ))}
            <span className="font-semibold text-gray-900">
              Total: {formatCurrency(totals.total, defaultCurrency)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}