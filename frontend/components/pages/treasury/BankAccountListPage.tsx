'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useBankAccounts, useDeleteBankAccount } from '@/hooks/useTreasury'
import { formatCurrency } from '@/lib/utils/format'
import { VirtualizedTableWrapper } from '@/components/common/VirtualizedTableWrapper'

export function BankAccountListPage() {
  const [activeFilter, setActiveFilter] = useState<string>('')
  const { data: accounts, isLoading, error } = useBankAccounts({
    is_active: activeFilter ? activeFilter === 'true' : undefined,
  })
  const deleteMutation = useDeleteBankAccount()

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this bank account?')) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        console.error('Failed to delete bank account:', error)
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        Error loading bank accounts. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bank Accounts</h1>
          <p className="text-gray-600 mt-1">Manage bank accounts and balances</p>
        </div>
        <Link href="/treasury/bank-accounts/new" className="btn-primary">
          Add Bank Account
        </Link>
      </div>

      <div className="card">
        <div className="flex items-center gap-4 mb-4">
          <label htmlFor="active-filter" className="text-sm font-medium text-gray-700">
            Filter by Status:
          </label>
          <select
            id="active-filter"
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
            className="input"
          >
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        {accounts && accounts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No bank accounts found</p>
            <Link href="/treasury/bank-accounts/new" className="btn-primary mt-4 inline-block">
              Add First Bank Account
            </Link>
          </div>
        ) : (
          <VirtualizedTableWrapper
            data={accounts || []}
            height={600}
            renderHeader={() => (
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bank</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Balance</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Currency</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            )}
            renderRow={(account) => (
              <>
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{account.account_name}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{account.bank_name}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{account.account_number}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{account.account_type}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-gray-900">
                  {formatCurrency(account.current_balance, account.currency)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{account.currency}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      account.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {account.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                  <Link
                    href={`/treasury/bank-accounts/${account.id}`}
                    className="text-primary-600 hover:text-primary-900"
                  >
                    View
                  </Link>
                  <Link
                    href={`/treasury/bank-accounts/${account.id}/edit`}
                    className="text-primary-600 hover:text-primary-900"
                  >
                    Edit
                  </Link>
                  <Link
                    href={`/treasury/bank-accounts/${account.id}/transactions`}
                    className="text-primary-600 hover:text-primary-900"
                  >
                    Transactions
                  </Link>
                  <button
                    onClick={() => handleDelete(account.id)}
                    className="text-red-600 hover:text-red-900"
                    disabled={deleteMutation.isPending}
                  >
                    Delete
                  </button>
                </td>
              </>
            )}
            estimateSize={() => 60}
          />
        )}
      </div>
    </div>
  )
}
