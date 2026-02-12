'use client'

import Link from 'next/link'

export function ReportsPage() {
  const reports = [
    {
      name: 'Trial Balance',
      description: 'Account balances and totals',
      href: '/reports/trial-balance',
      icon: '📊',
    },
    {
      name: 'Profit & Loss',
      description: 'Revenue, expenses, and net income',
      href: '/reports/pl-balance-sheet',
      icon: '📈',
    },
    {
      name: 'Balance Sheet',
      description: 'Assets, liabilities, and equity',
      href: '/reports/pl-balance-sheet',
      icon: '📋',
    },
    {
      name: 'Cash Flow Statement',
      description: 'Operating, investing, and financing activities',
      href: '/reports/cash-flow',
      icon: '💰',
    },
    {
      name: 'GL Detail',
      description: 'Detailed journal entry transactions',
      href: '/reports/gl-detail',
      icon: '🔍',
    },
    {
      name: 'AR Aging',
      description: 'Accounts receivable aging analysis',
      href: '/ar/invoices',
      icon: '💳',
    },
    {
      name: 'AP Aging',
      description: 'Accounts payable aging analysis',
      href: '/ap/vendors',
      icon: '📄',
    },
    {
      name: 'Cash Position',
      description: 'Real-time cash across all accounts',
      href: '/treasury/bank-accounts',
      icon: '💵',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Financial Reports</h1>
        <p className="text-gray-600 mt-1">View and export financial reports</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((report, index) => (
          <Link
            key={`${report.href}-${index}`}
            href={report.href}
            className="card hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-4">
              <span className="text-3xl" aria-hidden="true">
                {report.icon}
              </span>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">{report.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{report.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
