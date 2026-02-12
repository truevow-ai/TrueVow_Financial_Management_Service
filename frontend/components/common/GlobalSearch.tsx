'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SearchResult {
  id: string
  type: 'page' | 'journal-entry' | 'invoice' | 'vendor' | 'customer' | 'account' | 'employee'
  title: string
  subtitle?: string
  url: string
  keywords: string[]
}

interface GlobalSearchProps {
  isOpen: boolean
  onClose: () => void
  placeholder?: string
  className?: string
}

/**
 * Search-First Navigation
 * Used by: Slack, Linear, Notion
 * Pattern: Global search with filters and suggestions
 * Benefit: Faster navigation for power users
 */
export function GlobalSearch({
  isOpen,
  onClose,
  placeholder = 'Search everything...',
  className,
}: GlobalSearchProps) {
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const router = useRouter()

  // Mock search results - in production, this would call an API
  const performSearch = useCallback((query: string) => {
    if (!query.trim()) {
      setResults([])
      return
    }

    const queryLower = query.toLowerCase()
    const baseResults: SearchResult[] = [
      // Pages
      { id: 'dashboard', type: 'page', title: 'Dashboard', url: '/dashboard', keywords: ['dashboard', 'home', 'main'] },
      { id: 'journal-entries', type: 'page', title: 'Journal Entries', url: '/journal-entries', keywords: ['journal', 'entries', 'je'] },
      { id: 'chart-of-accounts', type: 'page', title: 'Chart of Accounts', url: '/chart-of-accounts', keywords: ['chart', 'accounts', 'coa'] },
      { id: 'ar-invoices', type: 'page', title: 'AR Invoices', url: '/ar/invoices', keywords: ['ar', 'invoices', 'receivable'] },
      { id: 'ap-vendors', type: 'page', title: 'AP Vendors', url: '/ap/vendors', keywords: ['ap', 'vendors', 'payable'] },
      { id: 'treasury', type: 'page', title: 'Treasury', url: '/treasury/bank-accounts', keywords: ['treasury', 'bank'] },
      { id: 'payroll', type: 'page', title: 'Payroll', url: '/payroll/employees', keywords: ['payroll', 'employees'] },
      { id: 'reports', type: 'page', title: 'Reports', url: '/reports', keywords: ['reports', 'analytics'] },
    ]
    const mockResults = baseResults.filter(
      (result) =>
        result.title.toLowerCase().includes(queryLower) ||
        result.keywords.some((kw) => kw.includes(queryLower))
    )

    setResults(mockResults)
    setSelectedIndex(0)
  }, [])

  useEffect(() => {
    performSearch(search)
  }, [search, performSearch])

  // Keyboard navigation
  const handleSelect = useCallback(
    (result: SearchResult) => {
      router.push(result.url)
      setSearch('')
      onClose()
    },
    [router, onClose]
  )

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev + 1) % results.length)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev - 1 + results.length) % results.length)
      } else if (e.key === 'Enter' && results[selectedIndex]) {
        e.preventDefault()
        handleSelect(results[selectedIndex])
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, results, selectedIndex, onClose, handleSelect])

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Search Modal */}
      <div
        className={cn(
          'fixed top-20 left-1/2 transform -translate-x-1/2',
          'w-full max-w-2xl bg-white rounded-lg shadow-xl z-50',
          className
        )}
        role="dialog"
        aria-label="Global search"
        aria-modal="true"
      >
        {/* Search Input */}
        <div className="flex items-center px-4 py-3 border-b border-gray-200">
          <Search className="w-5 h-5 text-gray-400 mr-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={placeholder}
            className="flex-1 outline-none text-gray-900 placeholder-gray-400"
            autoFocus
            aria-label="Search input"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="ml-3 p-1 hover:bg-gray-100 rounded"
              aria-label="Clear search"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="max-h-96 overflow-y-auto">
            {results.map((result, index) => (
              <button
                key={result.id}
                onClick={() => handleSelect(result)}
                className={cn(
                  'w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors',
                  'flex items-center justify-between',
                  index === selectedIndex && 'bg-gray-50'
                )}
                aria-selected={index === selectedIndex}
                role="option"
              >
                <div>
                  <div className="font-medium text-gray-900">{result.title}</div>
                  {result.subtitle && (
                    <div className="text-sm text-gray-500">{result.subtitle}</div>
                  )}
                </div>
                <span className="text-xs text-gray-400 capitalize">{result.type}</span>
              </button>
            ))}
          </div>
        )}

        {/* No Results */}
        {search && results.length === 0 && (
          <div className="px-4 py-8 text-center text-gray-500">
            No results found for &quot;{search}&quot;
          </div>
        )}

        {/* Empty State */}
        {!search && (
          <div className="px-4 py-8 text-center text-gray-500">
            Start typing to search...
          </div>
        )}
      </div>
    </>
  )
}
