'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { arApi } from '@/lib/api/arApi'
import { useEntityBook } from '@/contexts/EntityBookContext'
import { formatCurrency } from '@/lib/utils/format'

export function ARAgingPage() {
  const { selectedEntityId } = useEntityBook()
  const legalEntityId = selectedEntityId || ''
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0])

  const { data, isLoading, error } = useQuery({
    queryKey: ['ar-aging', legalEntityId, asOfDate],
    queryFn: () => arApi.getARAging({ legal_entity_id: legalEntityId, as_of_date: asOfDate }),
    enabled: !!legalEntityId,
  })

  if (!legalEntityId) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg">
        Select an entity to view AR aging.
      </div>
    )
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
        Error loading AR aging. Please try again.
      </div>
    )
  }

  const rows = data || []
  const sum = (key: 'current' | 'days_30' | 'days_60' | 'days_90' | 'days_90_plus' | 'total') =>
    rows.reduce((s, r) => s + (r[key] || 0), 0)
  const totalOutstanding = sum('total')
  const overdue = sum('days_30') + sum('days_60') + sum('days_90') + sum('days_90_plus')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AR Aging</h1>
          <p className="text-gray-600 mt-1">Outstanding receivables by age</p>
        </div>
        <input
          type="date"
          value={asOfDate}
          onChange={(e) => setAsOfDate(e.target.value)}
          className="input"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Total Outstanding</h3>
          <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalOutstanding)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Overdue</h3>
          <p className="text-2xl font-bold text-red-600">{formatCurrency(overdue)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Customers</h3>
          <p className="text-2xl font-bold text-gray-900">{rows.length}</p>
        </div>
      </div>

      <div className="card">
        {rows.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No outstanding receivables</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Current</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">1–30</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">31–60</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">61–90</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">90+</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {rows.map((r) => (
                  <tr key={r.customer_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{r.customer_name}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(r.current)}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(r.days_30)}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(r.days_60)}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(r.days_90)}</td>
                    <td className="px-4 py-3 text-sm text-right text-red-600">{formatCurrency(r.days_90_plus)}</td>
                    <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">{formatCurrency(r.total)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50 font-bold">
                  <td className="px-4 py-3 text-sm text-gray-900">Total</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(sum('current'))}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(sum('days_30'))}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(sum('days_60'))}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(sum('days_90'))}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(sum('days_90_plus'))}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">{formatCurrency(sum('total'))}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
