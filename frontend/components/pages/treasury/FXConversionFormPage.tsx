'use client'

import { useState, useEffect } from 'react'
import { treasuryApi, BankAccount, FXConversion } from '@/lib/api/treasuryApi'

interface FXConversionFormPageProps {
  onSuccess?: () => void
}

export function FXConversionFormPage({ onSuccess }: FXConversionFormPageProps) {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([])
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    legal_entity_id: '',
    bank_account_id: '',
    conversion_date: new Date().toISOString().split('T')[0],
    from_currency: 'USD',
    to_currency: '',
    from_amount: '',
    to_amount: '',
    exchange_rate: '',
    description: ''
  })

  useEffect(() => {
    loadBankAccounts()
  }, [])

  const loadBankAccounts = async () => {
    try {
      setLoading(true)
      const response = await treasuryApi.getBankAccounts({ is_active: true })
      setBankAccounts(response || [])
      if (response && response.length > 0) {
        setFormData(prev => ({
          ...prev,
          legal_entity_id: response[0].legal_entity_id
        }))
      }
    } catch (err) {
      console.error('Failed to load bank accounts:', err)
      setError('Failed to load bank accounts')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    
    // Auto-calculate exchange rate if from and to amounts are provided
    if (name === 'from_amount' || name === 'to_amount') {
      const fromAmount = name === 'from_amount' ? parseFloat(value) : parseFloat(formData.from_amount)
      const toAmount = name === 'to_amount' ? parseFloat(value) : parseFloat(formData.to_amount)
      
      if (fromAmount && toAmount) {
        const rate = toAmount / fromAmount
        setFormData(prev => ({ ...prev, exchange_rate: rate.toFixed(6) }))
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    if (!formData.bank_account_id || !formData.to_currency || !formData.from_amount || !formData.exchange_rate) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setSaving(true)
      await treasuryApi.createFXConversion({
        legal_entity_id: formData.legal_entity_id,
        bank_account_id: formData.bank_account_id,
        conversion_date: formData.conversion_date,
        from_currency: formData.from_currency,
        to_currency: formData.to_currency,
        from_amount: parseFloat(formData.from_amount),
        to_amount: formData.to_amount ? parseFloat(formData.to_amount) : undefined,
        exchange_rate: parseFloat(formData.exchange_rate),
        description: formData.description || undefined
      })
      
      // Reset form
      setFormData({
        legal_entity_id: formData.legal_entity_id,
        bank_account_id: '',
        conversion_date: new Date().toISOString().split('T')[0],
        from_currency: 'USD',
        to_currency: '',
        from_amount: '',
        to_amount: '',
        exchange_rate: '',
        description: ''
      })
      
      onSuccess?.()
    } catch (err) {
      console.error('Failed to create FX conversion:', err)
      setError('Failed to create FX conversion. Please try again.')
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
      <h1 className="text-2xl font-bold text-gray-900 mb-6">FX Conversion</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
        {/* Bank Account */}
        <div>
          <label htmlFor="bank_account_id" className="block text-sm font-medium text-gray-700 mb-1">
            Bank Account *
          </label>
          <select
            id="bank_account_id"
            name="bank_account_id"
            value={formData.bank_account_id}
            onChange={handleInputChange}
            required
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select bank account</option>
            {bankAccounts.map(account => (
              <option key={account.id} value={account.id}>
                {account.account_name} - {account.currency}
              </option>
            ))}
          </select>
        </div>

        {/* Conversion Date */}
        <div>
          <label htmlFor="conversion_date" className="block text-sm font-medium text-gray-700 mb-1">
            Conversion Date *
          </label>
          <input
            type="date"
            id="conversion_date"
            name="conversion_date"
            value={formData.conversion_date}
            onChange={handleInputChange}
            required
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Currency Pair */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="from_currency" className="block text-sm font-medium text-gray-700 mb-1">
              From Currency *
            </label>
            <select
              id="from_currency"
              name="from_currency"
              value={formData.from_currency}
              onChange={handleInputChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
              <option value="AED">AED</option>
              <option value="PKR">PKR</option>
            </select>
          </div>

          <div>
            <label htmlFor="to_currency" className="block text-sm font-medium text-gray-700 mb-1">
              To Currency *
            </label>
            <select
              id="to_currency"
              name="to_currency"
              value={formData.to_currency}
              onChange={handleInputChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select currency</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
              <option value="AED">AED</option>
              <option value="PKR">PKR</option>
            </select>
          </div>
        </div>

        {/* Amounts */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label htmlFor="from_amount" className="block text-sm font-medium text-gray-700 mb-1">
              From Amount *
            </label>
            <input
              type="number"
              id="from_amount"
              name="from_amount"
              value={formData.from_amount}
              onChange={handleInputChange}
              step="0.01"
              min="0"
              placeholder="0.00"
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="exchange_rate" className="block text-sm font-medium text-gray-700 mb-1">
              Exchange Rate *
            </label>
            <input
              type="number"
              id="exchange_rate"
              name="exchange_rate"
              value={formData.exchange_rate}
              onChange={handleInputChange}
              step="0.000001"
              min="0"
              placeholder="0.000000"
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="to_amount" className="block text-sm font-medium text-gray-700 mb-1">
              To Amount
            </label>
            <input
              type="number"
              id="to_amount"
              name="to_amount"
              value={formData.to_amount}
              onChange={handleInputChange}
              step="0.01"
              min="0"
              placeholder="Auto-calculated"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
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

        {/* Submit Button */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Creating...' : 'Create FX Conversion'}
          </button>
          
          <button
            type="button"
            onClick={() => setFormData({
              legal_entity_id: formData.legal_entity_id,
              bank_account_id: '',
              conversion_date: new Date().toISOString().split('T')[0],
              from_currency: 'USD',
              to_currency: '',
              from_amount: '',
              to_amount: '',
              exchange_rate: '',
              description: ''
            })}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
          >
            Clear
          </button>
        </div>
      </form>
    </div>
  )
}
