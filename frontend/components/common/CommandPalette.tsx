'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'

interface Command {
  id: string
  label: string
  category: string
  icon?: string
  action: () => void
  keywords: string[]
}

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const router = useRouter()

  // Define commands
  const commands: Command[] = [
    // Navigation
    { id: 'dashboard', label: 'Go to Dashboard', category: 'Navigation', icon: '📊', action: () => router.push('/dashboard'), keywords: ['dashboard', 'home', 'main'] },
    { id: 'journal-entries', label: 'Journal Entries', category: 'Navigation', icon: '📝', action: () => router.push('/journal-entries'), keywords: ['journal', 'entries', 'je'] },
    { id: 'chart-of-accounts', label: 'Chart of Accounts', category: 'Navigation', icon: '📋', action: () => router.push('/chart-of-accounts'), keywords: ['chart', 'accounts', 'coa'] },
    { id: 'periods', label: 'Accounting Periods', category: 'Navigation', icon: '📅', action: () => router.push('/periods'), keywords: ['periods', 'accounting'] },
    { id: 'ar-invoices', label: 'AR Invoices', category: 'Navigation', icon: '💳', action: () => router.push('/ar/invoices'), keywords: ['ar', 'invoices', 'receivable'] },
    { id: 'ap-vendors', label: 'AP Vendors', category: 'Navigation', icon: '🏢', action: () => router.push('/ap/vendors'), keywords: ['ap', 'vendors', 'payable'] },
    { id: 'treasury', label: 'Treasury', category: 'Navigation', icon: '💰', action: () => router.push('/treasury/bank-accounts'), keywords: ['treasury', 'bank'] },
    { id: 'payroll', label: 'Payroll', category: 'Navigation', icon: '👥', action: () => router.push('/payroll/employees'), keywords: ['payroll', 'employees'] },
    { id: 'reports', label: 'Reports', category: 'Navigation', icon: '📈', action: () => router.push('/reports'), keywords: ['reports', 'analytics'] },
    
    // Actions
    { id: 'new-journal-entry', label: 'New Journal Entry', category: 'Actions', icon: '➕', action: () => router.push('/journal-entries/new'), keywords: ['new', 'create', 'journal'] },
    { id: 'new-account', label: 'New Account', category: 'Actions', icon: '➕', action: () => router.push('/chart-of-accounts/new'), keywords: ['new', 'create', 'account'] },
    { id: 'new-bank-account', label: 'New Bank Account', category: 'Actions', icon: '➕', action: () => router.push('/treasury/bank-accounts/new'), keywords: ['new', 'create', 'bank'] },
  ]

  // Filter commands based on search
  const filteredCommands = commands.filter(cmd => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      cmd.label.toLowerCase().includes(searchLower) ||
      cmd.category.toLowerCase().includes(searchLower) ||
      cmd.keywords.some(kw => kw.toLowerCase().includes(searchLower))
    )
  })

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K or Ctrl+K to open
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(true)
      }
      
      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
        setSearch('')
        setSelectedIndex(0)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  // Handle command selection
  const handleSelect = useCallback((command: Command) => {
    command.action()
    setIsOpen(false)
    setSearch('')
    setSelectedIndex(0)
  }, [])

  // Keyboard navigation within palette
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % filteredCommands.length)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length)
      } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
        e.preventDefault()
        handleSelect(filteredCommands[selectedIndex])
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filteredCommands, selectedIndex, handleSelect])

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={() => {
          setIsOpen(false)
          setSearch('')
          setSelectedIndex(0)
        }}
      />
      
      {/* Command Palette */}
      <div className="fixed inset-0 flex items-start justify-center pt-[20vh] z-50 pointer-events-none">
        <div
          className="bg-white rounded-lg shadow-2xl w-full max-w-2xl mx-4 pointer-events-auto"
          role="dialog"
          aria-label="Command Palette"
          aria-modal="true"
        >
          {/* Search Input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200">
            <span className="text-gray-400" aria-hidden="true">🔍</span>
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setSelectedIndex(0)
              }}
              placeholder="Type a command or search..."
              className="flex-1 outline-none text-gray-900 placeholder-gray-400"
              autoFocus
              aria-label="Search commands"
            />
            <kbd className="hidden sm:inline-flex items-center px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100 border border-gray-200 rounded">
              ESC
            </kbd>
          </div>

          {/* Commands List */}
          <div className="max-h-96 overflow-y-auto">
            {filteredCommands.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                No commands found
              </div>
            ) : (
              <div className="py-2">
                {filteredCommands.map((command, index) => (
                  <button
                    key={command.id}
                    onClick={() => handleSelect(command)}
                    className={cn(
                      'w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors',
                      index === selectedIndex && 'bg-gray-50'
                    )}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    {command.icon && (
                      <span className="text-lg" aria-hidden="true">
                        {command.icon}
                      </span>
                    )}
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {command.label}
                      </div>
                      <div className="text-xs text-gray-500">
                        {command.category}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded">↑</kbd>
                <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded">↓</kbd>
                <span>Navigate</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded">Enter</kbd>
                <span>Select</span>
              </span>
            </div>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded">Esc</kbd>
              <span>Close</span>
            </span>
          </div>
        </div>
      </div>
    </>
  )
}
