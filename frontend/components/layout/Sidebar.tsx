'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

type NavItem = {
  name: string
  href: string
  icon: string
  comingSoon?: boolean
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊' },
  { name: 'Journal Entries', href: '/journal-entries', icon: '📝' },
  { name: 'Chart of Accounts', href: '/chart-of-accounts', icon: '📋' },
  { name: 'Accounting Periods', href: '/periods', icon: '📅' },
  { name: 'Treasury', href: '/treasury/bank-accounts', icon: '💰' },
  { name: 'AR Invoices', href: '/ar/invoices', icon: '💳' },
  { name: 'AR Aging', href: '/ar/aging', icon: '📊' },
  { name: 'Deferred Revenue', href: '/ar/revenue-schedules', icon: '💰' },
  { name: 'AP Vendors', href: '/ap/vendors', icon: '🏢' },
  { name: 'AP Aging', href: '/ap/aging', icon: '📈' },
  { name: 'Employees', href: '/payroll/employees', icon: '👥' },
  { name: 'Payroll Runs', href: '/payroll/runs', icon: '💰', comingSoon: true },
  { name: 'Bank Accounts', href: '/treasury/bank-accounts', icon: '🏦' },
  { name: 'Cash Position', href: '/treasury/cash-position', icon: '💵', comingSoon: true },
  { name: 'Intercompany', href: '/intercompany', icon: '🔗' },
  { name: 'Reports', href: '/reports', icon: '📈' },
  { name: 'Trial Balance', href: '/reports/trial-balance', icon: '📊' },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 bg-purple-900 border-r border-purple-800 flex flex-col">
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navigation.map((item) => {
          if (item.comingSoon) {
            return (
              <div
                key={item.name}
                className="flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium text-purple-400 cursor-not-allowed select-none"
                aria-disabled="true"
                title="Coming soon"
              >
                <span className="text-lg opacity-60" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="opacity-70">{item.name}</span>
                <span className="ml-auto rounded bg-purple-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-purple-300">
                  Soon
                </span>
              </div>
            )
          }

          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-purple-800 text-white'
                  : 'text-purple-200 hover:bg-purple-800 hover:text-white'
              )}
              aria-current={isActive ? 'page' : undefined}
            >
              <span className="text-lg" aria-hidden="true">
                {item.icon}
              </span>
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
