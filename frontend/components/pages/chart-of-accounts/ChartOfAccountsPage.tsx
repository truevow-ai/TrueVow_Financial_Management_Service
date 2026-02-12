'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useGLAccounts, useDeleteGLAccount } from '@/hooks/useGLAccounts'
import { VirtualizedTableWrapper } from '@/components/common/VirtualizedTableWrapper'

export function ChartOfAccountsPage() {
  const [accountTypeFilter, setAccountTypeFilter] = useState<string>('')
  const { data: accounts, isLoading, error } = useGLAccounts({
    account_type: accountTypeFilter || undefined,
  })
  const deleteMutation = useDeleteGLAccount()

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this account?')) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        console.error('Failed to delete account:', error)
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
        Error loading chart of accounts. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chart of Accounts</h1>
          <p className="text-gray-600 mt-1">Manage your chart of accounts</p>
        </div>
        <Link href="/chart-of-accounts/new" className="btn-primary">
          Create Account
        </Link>
      </div>

      <div className="card">
        <div className="flex items-center gap-4 mb-4">
          <label htmlFor="account-type-filter" className="text-sm font-medium text-gray-700">
            Filter by Type:
          </label>
          <select
            id="account-type-filter"
            value={accountTypeFilter}
            onChange={(e) => setAccountTypeFilter(e.target.value)}
            className="input"
          >
            <option value="">All Types</option>
            <option value="asset">Asset</option>
            <option value="liability">Liability</option>
            <option value="equity">Equity</option>
            <option value="revenue">Revenue</option>
            <option value="expense">Expense</option>
          </select>
        </div>

        {accounts && accounts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No accounts found</p>
            <Link href="/chart-of-accounts/new" className="btn-primary mt-4 inline-block">
              Create First Account
            </Link>
          </div>
        ) : (
          <VirtualizedTableWrapper
            data={accounts || []}
            height={600}
            renderHeader={() => (
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            )}
            renderRow={(account) => (
              <>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {account.account_code}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">{account.account_name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{account.account_type}</td>
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
                    href={`/chart-of-accounts/${account.id}`}
                    className="text-primary-600 hover:text-primary-900"
                  >
                    View
                  </Link>
                  <Link
                    href={`/chart-of-accounts/${account.id}/edit`}
                    className="text-primary-600 hover:text-primary-900"
                  >
                    Edit
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
