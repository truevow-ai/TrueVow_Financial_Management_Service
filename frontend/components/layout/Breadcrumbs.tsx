'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'

// Define breadcrumb mappings
const breadcrumbMap: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/journal-entries': 'Journal Entries',
  '/chart-of-accounts': 'Chart of Accounts',
  '/periods': 'Accounting Periods',
  '/treasury': 'Treasury',
  '/ar/invoices': 'AR Invoices',
  '/ar/aging': 'AR Aging',
  '/ar/revenue-schedules': 'Deferred Revenue',
  '/ap/vendors': 'AP Vendors',
  '/ap/aging': 'AP Aging',
  '/payroll/employees': 'Employees',
  '/payroll/runs': 'Payroll Runs',
  '/treasury/bank-accounts': 'Bank Accounts',
  '/treasury/cash-position': 'Cash Position',
  '/intercompany': 'Intercompany',
  '/reports': 'Reports',
  '/reports/trial-balance': 'Trial Balance',
}

// Function to generate breadcrumbs from path
function generateBreadcrumbs(pathname: string) {
  const pathSegments = pathname.split('/').filter(segment => segment)
  const breadcrumbs = [{ href: '/', label: 'Home' }]
  
  let currentPath = ''
  
  pathSegments.forEach((segment, index) => {
    currentPath += `/${segment}`
    const fullPath = currentPath
    
    // Check if we have a direct mapping
    if (breadcrumbMap[fullPath]) {
      breadcrumbs.push({
        href: fullPath,
        label: breadcrumbMap[fullPath]
      })
    } else {
      // Create a human-readable label from the segment
      const label = segment
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
      
      breadcrumbs.push({
        href: fullPath,
        label
      })
    }
  })
  
  return breadcrumbs
}

export function Breadcrumbs() {
  const pathname = usePathname()
  const breadcrumbs = generateBreadcrumbs(pathname)
  
  if (breadcrumbs.length <= 1) {
    return (
      <nav className="text-sm text-gray-500" aria-label="Breadcrumb">
        <span>Dashboard</span>
      </nav>
    )
  }
  
  return (
    <nav className="flex text-sm" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        {breadcrumbs.map((crumb, index) => (
          <li key={crumb.href} className="flex items-center">
            {index > 0 && (
              <svg
                className="mx-2 h-4 w-4 text-gray-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {index === breadcrumbs.length - 1 ? (
              <span className="text-gray-900 font-medium truncate max-w-xs">
                {crumb.label}
              </span>
            ) : (
              <Link
                href={crumb.href}
                className="text-gray-500 hover:text-gray-700 transition-colors truncate max-w-xs"
              >
                {crumb.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
