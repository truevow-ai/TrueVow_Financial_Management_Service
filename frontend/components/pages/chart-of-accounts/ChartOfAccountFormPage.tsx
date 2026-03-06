'use client'

import { useState, useEffect } from 'react'
import { glApi, GLAccount } from '@/lib/api/glApi'

interface ChartOfAccountFormPageProps {
  accountId?: string
  onSuccess?: () => void
}

export function ChartOfAccountFormPage({ accountId, onSuccess }: ChartOfAccountFormPageProps) {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState<{
    legal_entity_id: string
    account_code: string
    account_name: string
    account_type: string
    is_active: boolean
    description: string
  }>({
    legal_entity_id: '',
    account_code: '',
    account_name: '',
    account_type: 'ASSET',
    is_active: true,
    description: ''
  })

  useEffect(() => {
    if (accountId) {
      loadAccount()
    }
  }, [accountId])

  const loadAccount = async () => {
    try {
      setLoading(true)
      const account = await glApi.getGLAccount(accountId!)
      setFormData({
        legal_entity_id: account.legal_entity_id || '',
        account_code: account.account_code,
        account_name: account.account_name,
        account_type: account.account_type,
        is_active: account.is_active ?? true,
        description: account.description || ''
      })
    } catch (err) {
      console.error('Failed to load account:', err)
      setError('Failed to load account details')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    if (!formData.legal_entity_id || !formData.account_code || !formData.account_name) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setSaving(true)
      
      if (accountId) {
        // Update existing account
        await glApi.updateGLAccount(accountId, formData)
      } else {
        // Create new account
        await glApi.createGLAccount(formData)
      }
      
      // Reset form for new accounts
      if (!accountId) {
        setFormData({
          legal_entity_id: '',
          account_code: '',
          account_name: '',
          account_type: 'ASSET',
          is_active: true,
          description: ''
        })
      }
      
      onSuccess?.()
    } catch (err) {
      console.error('Failed to save account:', err)
      setError('Failed to save account. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {accountId ? 'Edit Account' : 'New Account'}
      </h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
        {/* Account Code */}
        <div>
          <label htmlFor="account_code" className="block text-sm font-medium text-gray-700 mb-1">
            Account Code *
          </label>
          <input
            type="text"
            id="account_code"
            name="account_code"
            value={formData.account_code}
            onChange={handleInputChange}
            required
            placeholder="e.g., 1010"
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Account Name */}
        <div>
          <label htmlFor="account_name" className="block text-sm font-medium text-gray-700 mb-1">
            Account Name *
          </label>
          <input
            type="text"
            id="account_name"
            name="account_name"
            value={formData.account_name}
            onChange={handleInputChange}
            required
            placeholder="e.g., Cash - Operating Account"
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Account Type */}
        <div>
          <label htmlFor="account_type" className="block text-sm font-medium text-gray-700 mb-1">
            Account Type *
          </label>
          <select
            id="account_type"
            name="account_type"
            value={formData.account_type}
            onChange={handleInputChange}
            required
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ASSET">Asset</option>
            <option value="LIABILITY">Liability</option>
            <option value="EQUITY">Equity</option>
            <option value="REVENUE">Revenue</option>
            <option value="EXPENSE">Expense</option>
          </select>
        </div>

        {/* Active Status */}
        <div>
          <label htmlFor="is_active" className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            id="is_active"
            name="is_active"
            value={formData.is_active.toString()}
            onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.value === 'true' }))}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            rows={3}
            placeholder="Optional description"
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Submit Buttons */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : (accountId ? 'Update Account' : 'Create Account')}
          </button>
          
          {!accountId && (
            <button
              type="button"
              onClick={() => setFormData({
                legal_entity_id: '',
                account_code: '',
                account_name: '',
                account_type: 'ASSET',
                is_active: true,
                description: ''
              })}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              Clear
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
