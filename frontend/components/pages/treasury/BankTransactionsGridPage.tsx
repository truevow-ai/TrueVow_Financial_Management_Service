import React, { useState, useMemo, useCallback } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { useBankTransactions, useBankAccounts } from '@/hooks/useTreasury'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { formatCurrency } from '@/lib/utils/format'
import { useToast } from '@/hooks/useToast'

interface BankTransactionRow {
  id: string
  transaction_date: string
  description: string
  amount: number
  currency: string
  bank_account_id: string
  bank_account_name?: string
  counterparty_name?: string
  transaction_type: 'debit' | 'credit'
  category?: 'Deposit' | 'Withdrawal' | 'Fee' | 'Transfer' | 'FX' | 'Unknown'
  status: 'Unmatched' | 'Matched' | 'Excluded'
  suggested_match?: string
  is_reconciled: boolean
  reference_number?: string
}

export function BankTransactionsGridPage() {
  const { selectedEntityId } = useEntityBook()
  const { showToast } = useToast()
  const [gridApi, setGridApi] = useState<GridApi | null>(null)
  const [columnApi, setColumnApi] = useState<ColumnApi | null>(null)
  
  // Filters
  const [selectedBankAccountId, setSelectedBankAccountId] = useState<string>('')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  const [unmatchedOnly, setUnmatchedOnly] = useState<boolean>(false)
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [searchKeyword, setSearchKeyword] = useState<string>('')
  const [minAmount, setMinAmount] = useState<string>('')
  const [maxAmount, setMaxAmount] = useState<string>('')

  // Fetch data
  const { data: bankAccounts } = useBankAccounts({ legal_entity_id: selectedEntityId || undefined })
  const { data: transactionsData, isLoading } = useBankTransactions({
    bank_account_id: selectedBankAccountId || undefined,
    is_reconciled: unmatchedOnly ? false : undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  })

  // Transform transactions to grid rows
  const transactions = useMemo(() => {
    if (!transactionsData?.items) return []
    
    let filtered = transactionsData.items.map((tx: any) => ({
      id: tx.id,
      transaction_date: tx.transaction_date,
      description: tx.description || '',
      amount: tx.amount,
      currency: tx.currency,
      bank_account_id: tx.bank_account_id,
      bank_account_name: bankAccounts?.find((acc: any) => acc.id === tx.bank_account_id)?.account_name || '',
      counterparty_name: tx.counterparty_name || '',
      transaction_type: tx.transaction_type,
      category: determineCategory(tx),
      status: (tx.is_reconciled ? 'Matched' : 'Unmatched') as BankTransactionRow['status'],
      suggested_match: undefined, // TODO: Fetch from matching service
      is_reconciled: tx.is_reconciled,
      reference_number: tx.reference_number,
    }))

    // Apply filters
    if (categoryFilter) {
      filtered = filtered.filter((tx: BankTransactionRow) => tx.category === categoryFilter)
    }
    if (searchKeyword) {
      const keyword = searchKeyword.toLowerCase()
      filtered = filtered.filter((tx: BankTransactionRow) =>
        tx.description.toLowerCase().includes(keyword) ||
        tx.counterparty_name?.toLowerCase().includes(keyword) ||
        tx.reference_number?.toLowerCase().includes(keyword)
      )
    }
    if (minAmount) {
      const min = parseFloat(minAmount)
      filtered = filtered.filter((tx: BankTransactionRow) => Math.abs(tx.amount) >= min)
    }
    if (maxAmount) {
      const max = parseFloat(maxAmount)
      filtered = filtered.filter((tx: BankTransactionRow) => Math.abs(tx.amount) <= max)
    }

    return filtered
  }, [transactionsData, bankAccounts, categoryFilter, searchKeyword, minAmount, maxAmount])

  function determineCategory(tx: any): 'Deposit' | 'Withdrawal' | 'Fee' | 'Transfer' | 'FX' | 'Unknown' {
    const desc = (tx.description || '').toLowerCase()
    if (desc.includes('fee') || desc.includes('charge')) return 'Fee'
    if (desc.includes('transfer')) return 'Transfer'
    if (desc.includes('fx') || desc.includes('exchange')) return 'FX'
    if (tx.transaction_type === 'credit') return 'Deposit'
    if (tx.transaction_type === 'debit') return 'Withdrawal'
    return 'Unknown'
  }

  const columnDefs = useMemo<ColDef[]>(
    () => [
      {
        field: 'transaction_date',
        headerName: 'Date',
        width: 120,
        sortable: true,
        filter: 'agDateColumnFilter',
      },
      {
        field: 'description',
        headerName: 'Description',
        width: 250,
        sortable: true,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'amount',
        headerName: 'Amount',
        width: 120,
        sortable: true,
        filter: 'agNumberColumnFilter',
        valueFormatter: (params: any) => {
          const amount = params.value || 0
          const sign = params.data?.transaction_type === 'credit' ? '+' : '-'
          return `${sign}${formatCurrency(Math.abs(amount), params.data?.currency || 'USD')}`
        },
        cellStyle: (params: any) => {
          const isCredit = params.data?.transaction_type === 'credit'
          return { color: isCredit ? '#059669' : '#dc2626' }
        },
      },
      {
        field: 'currency',
        headerName: 'Currency',
        width: 100,
        sortable: true,
      },
      {
        field: 'bank_account_name',
        headerName: 'Bank Account',
        width: 180,
        sortable: true,
      },
      {
        field: 'counterparty_name',
        headerName: 'Counterparty',
        width: 150,
        sortable: true,
      },
      {
        field: 'category',
        headerName: 'Category',
        width: 120,
        sortable: true,
        filter: 'agSetColumnFilter',
        cellRenderer: (params: any) => {
          const category = params.value || 'Unknown'
          const colors: Record<string, string> = {
            Deposit: 'bg-green-100 text-green-800',
            Withdrawal: 'bg-red-100 text-red-800',
            Fee: 'bg-yellow-100 text-yellow-800',
            Transfer: 'bg-blue-100 text-blue-800',
            FX: 'bg-purple-100 text-purple-800',
            Unknown: 'bg-gray-100 text-gray-800',
          }
          return `<span class="px-2 py-1 rounded text-xs font-medium ${colors[category] || colors.Unknown}">${category}</span>`
        },
      },
      {
        field: 'status',
        headerName: 'Status',
        width: 120,
        sortable: true,
        filter: 'agSetColumnFilter',
        cellRenderer: (params: any) => {
          const status = params.value || 'Unmatched'
          const colors: Record<string, string> = {
            Matched: 'bg-green-100 text-green-800',
            Unmatched: 'bg-yellow-100 text-yellow-800',
            Excluded: 'bg-gray-100 text-gray-800',
          }
          return `<span class="px-2 py-1 rounded text-xs font-medium ${colors[status] || colors.Unmatched}">${status}</span>`
        },
      },
      {
        field: 'suggested_match',
        headerName: 'Suggested Match',
        width: 200,
        sortable: false,
        cellRenderer: (params: any) => {
          if (!params.value) return '-'
          return `<span class="text-sm text-blue-600">${params.value}</span>`
        },
      },
      {
        field: 'actions',
        headerName: 'Actions',
        width: 200,
        sortable: false,
        filter: false,
        cellRenderer: (params: any) => {
          const tx = params.data
          return `
            <div class="flex gap-2">
              <button class="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600" onclick="window.handleMatch('${tx.id}')">Match</button>
              <button class="text-xs px-2 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600" onclick="window.handleMarkFee('${tx.id}')">Mark Fee</button>
              <button class="text-xs px-2 py-1 bg-gray-500 text-white rounded hover:bg-gray-600" onclick="window.handleExclude('${tx.id}')">Exclude</button>
            </div>
          `
        },
      },
    ],
    []
  )

  const defaultColDef = useMemo(
    () => ({
      resizable: true,
      sortable: true,
      filter: true,
    }),
    []
  )

  const onGridReady = (params: any) => {
    setGridApi(params.api)
    setColumnApi(params.columnApi)
  }

  const handleBulkMarkFee = () => {
    const selected = gridApi?.getSelectedRows() || []
    if (selected.length === 0) {
      showToast('Please select transactions to mark as fees', 'warning')
      return
    }
    // TODO: Open dialog to select account + dimensions
    showToast(`Marking ${selected.length} transactions as fees...`, 'info')
  }

  const handleBulkMarkTransfer = () => {
    const selected = gridApi?.getSelectedRows() || []
    if (selected.length === 0) {
      showToast('Please select transactions to mark as transfers', 'warning')
      return
    }
    // TODO: Open dialog to select entity/from/to
    showToast(`Marking ${selected.length} transactions as transfers...`, 'info')
  }

  const handleBulkExclude = () => {
    const selected = gridApi?.getSelectedRows() || []
    if (selected.length === 0) {
      showToast('Please select transactions to exclude', 'warning')
      return
    }
    // TODO: Open dialog for exclusion reason
    showToast(`Excluding ${selected.length} transactions...`, 'info')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bank Transactions</h1>
          <p className="text-gray-600 mt-1">Review and classify bank transactions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bank Account
            </label>
            <select
              value={selectedBankAccountId}
              onChange={(e) => setSelectedBankAccountId(e.target.value)}
              className="input w-full"
            >
              <option value="">All Accounts</option>
              {bankAccounts?.map((acc: any) => (
                <option key={acc.id} value={acc.id}>
                  {acc.account_name} ({acc.account_number})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="input w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="input w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="input w-full"
            >
              <option value="">All Categories</option>
              <option value="Deposit">Deposit</option>
              <option value="Withdrawal">Withdrawal</option>
              <option value="Fee">Fee</option>
              <option value="Transfer">Transfer</option>
              <option value="FX">FX</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Keyword
            </label>
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="Description, counterparty, reference..."
              className="input w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Min Amount
            </label>
            <input
              type="number"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              placeholder="0.00"
              className="input w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Amount
            </label>
            <input
              type="number"
              value={maxAmount}
              onChange={(e) => setMaxAmount(e.target.value)}
              placeholder="0.00"
              className="input w-full"
            />
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={unmatchedOnly}
                onChange={(e) => setUnmatchedOnly(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-700">Unmatched Only</span>
            </label>
          </div>
        </div>

        {/* Bulk Actions */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm font-medium text-gray-700">
            Selected: {gridApi?.getSelectedRows().length || 0}
          </span>
          <button
            onClick={handleBulkMarkFee}
            className="btn-secondary text-sm"
            disabled={!gridApi?.getSelectedRows().length}
          >
            Mark as Fees
          </button>
          <button
            onClick={handleBulkMarkTransfer}
            className="btn-secondary text-sm"
            disabled={!gridApi?.getSelectedRows().length}
          >
            Mark as Transfers
          </button>
          <button
            onClick={handleBulkExclude}
            className="btn-secondary text-sm"
            disabled={!gridApi?.getSelectedRows().length}
          >
            Exclude Selected
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="ag-theme-alpine" style={{ height: '600px', width: '100%' }}>
            <AgGridReact
              rowData={transactions}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              onGridReady={onGridReady}
              rowSelection="multiple"
              suppressRowClickSelection={false}
              enableRangeSelection={true}
              animateRows={false}
              getRowId={(params: any) => params.data.id}
            />
          </div>
        )}
      </div>
    </div>
  )
}
