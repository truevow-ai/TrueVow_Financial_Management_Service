'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { useEntityBook } from '@/contexts/EntityBookContext'

// Types for company statistics
interface CompanyStats {
  totalRevenue: number
  totalExpenses: number
  netIncome: number
  cashPosition: number
  accountsReceivable: number
  accountsPayable: number
  totalAssets: number | null
  totalLiabilities: number | null
  equity: number | null
  pendingApprovals: number
  overdueInvoices: number
  upcomingPayments: number
  currency: string
  asOfDate: string
}

// Status definitions (static UI labels only - no hardcoded data)
const statusDefinitions = [
  { 
    status: 'Pending Approval', 
    color: 'yellow', 
    description: 'Awaiting managerial review and authorization' 
  },
  { 
    status: 'Approved', 
    color: 'green', 
    description: 'Authorized and ready for processing' 
  },
  { 
    status: 'Rejected', 
    color: 'red', 
    description: 'Declined and requires revision' 
  },
  { 
    status: 'Posted', 
    color: 'blue', 
    description: 'Successfully recorded in the general ledger' 
  },
  { 
    status: 'Overdue', 
    color: 'red', 
    description: 'Past due date and requires immediate attention' 
  },
  { 
    status: 'Paid', 
    color: 'green', 
    description: 'Fully settled and closed' 
  }
]

export function CompanyStatsWidget() {
  const { selectedEntityId, selectedBookId } = useEntityBook()
  
  // Fetch real stats from API
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats', selectedEntityId, selectedBookId],
    queryFn: async () => {
      if (!selectedEntityId) return null
      
      const params: Record<string, string> = { legal_entity_id: selectedEntityId }
      if (selectedBookId) params.book_id = selectedBookId
      
      const response = await apiClient.get('/fm/dashboard/stats', { params })
      return response.data as CompanyStats
    },
    enabled: !!selectedEntityId,
    refetchInterval: 30000, // Refresh every 30 seconds
  })
  
  // Show loading state
  if (isLoading || !stats) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="space-y-2">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-3 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    )
  }
  
  // Show error state
  if (error) {
    return (
      <div className="text-sm text-purple-200">
        <p>Unable to load statistics</p>
      </div>
    )
  }

  const financialMetrics = [
    { 
      label: 'Total Revenue', 
      value: `$${(Number(stats.totalRevenue) / 100).toFixed(2)}`, 
      change: '+0.0%', 
      positive: true 
    },
    { 
      label: 'Net Income', 
      value: `$${(Number(stats.netIncome) / 100).toFixed(2)}`, 
      change: '+0.0%', 
      positive: Number(stats.netIncome) >= 0 
    },
    { 
      label: 'Cash Position', 
      value: `$${(Number(stats.cashPosition) / 100).toFixed(2)}`, 
      change: '+0.0%', 
      positive: true 
    },
    { 
      label: 'AR Balance', 
      value: `$${(Number(stats.accountsReceivable) / 100).toFixed(2)}`, 
      change: '+0.0%', 
      positive: true 
    },
    { 
      label: 'AP Balance', 
      value: `$${(Number(stats.accountsPayable) / 100).toFixed(2)}`, 
      change: '+0.0%', 
      positive: false 
    },
  ]

  const operationalMetrics = [
    { label: 'Pending Approvals', value: stats.pendingApprovals.toString(), critical: stats.pendingApprovals > 10 },
    { label: 'Overdue Invoices', value: stats.overdueInvoices.toString(), critical: stats.overdueInvoices > 0 },
    { label: 'Upcoming Payments', value: stats.upcomingPayments.toString(), critical: false },
  ]

  return (
    <div className="space-y-6">
      {/* Financial Metrics */}
      <div>
        <h3 className="text-sm font-semibold text-purple-100 mb-3">Financial Overview</h3>
        <div className="space-y-3">
          {financialMetrics.map((metric) => (
            <div key={metric.label} className="flex justify-between items-center">
              <span className="text-sm text-purple-200">{metric.label}</span>
              <div className="text-right">
                <div className="text-sm font-medium text-white">{metric.value}</div>
                <div className={`text-xs ${metric.positive ? 'text-green-300' : 'text-red-300'}`}>
                  {metric.change}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Operational Metrics */}
      <div>
        <h3 className="text-sm font-semibold text-purple-100 mb-3">Operational Alerts</h3>
        <div className="space-y-2">
          {operationalMetrics.map((metric) => (
            <div 
              key={metric.label} 
              className={`flex justify-between items-center p-2 rounded ${
                metric.critical ? 'bg-red-900/30 border border-red-700/50' : 'bg-purple-800/30'
              }`}
            >
              <span className="text-sm text-purple-200">{metric.label}</span>
              <span className={`text-sm font-medium ${
                metric.critical ? 'text-red-300' : 'text-white'
              }`}>
                {metric.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-sm font-semibold text-purple-100 mb-3">Quick Actions</h3>
        <div className="space-y-2">
          <button className="w-full text-left text-sm text-purple-200 hover:text-white hover:bg-purple-800 px-3 py-2 rounded transition-colors">
            Create Journal Entry
          </button>
          <button className="w-full text-left text-sm text-purple-200 hover:text-white hover:bg-purple-800 px-3 py-2 rounded transition-colors">
            Review Pending Approvals
          </button>
          <button className="w-full text-left text-sm text-purple-200 hover:text-white hover:bg-purple-800 px-3 py-2 rounded transition-colors">
            Generate Financial Report
          </button>
        </div>
      </div>
    </div>
  )
}

export function StatusDefinitions() {
  return (
    <div className="pt-4 border-t border-purple-800">
      <h3 className="text-sm font-semibold text-purple-100 mb-3">Status Legend</h3>
      <div className="space-y-2">
        {statusDefinitions.map((status) => (
          <div key={status.status} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              status.color === 'green' ? 'bg-green-500' :
              status.color === 'red' ? 'bg-red-500' :
              status.color === 'yellow' ? 'bg-yellow-500' :
              'bg-blue-500'
            }`}></div>
            <div>
              <div className="text-sm font-medium text-white">{status.status}</div>
              <div className="text-xs text-purple-300">{status.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}