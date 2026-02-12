'use client'

import { UserButton } from '@clerk/nextjs'
import { useUser } from '@clerk/nextjs'
import { Search } from 'lucide-react'
import { EntityBookSelector } from '@/components/common/EntityBookSelector'

interface HeaderProps {
  onSearchClick?: () => void
}

export default function Header({ onSearchClick }: HeaderProps) {
  const { user } = useUser()

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-secondary-200 px-6 py-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-secondary-900">TrueVow Financial Management</h1>
        <div className="flex items-center gap-4">
          {/* Search Button (Search-First Navigation) */}
          {onSearchClick && (
            <button
              onClick={onSearchClick}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Open search"
              title="Search (Ctrl+K or /)"
            >
              <Search className="w-5 h-5 text-gray-600" />
            </button>
          )}
          {user?.emailAddresses[0]?.emailAddress && (
            <span className="text-sm text-secondary-600">{user.emailAddresses[0].emailAddress}</span>
          )}
          <UserButton afterSignOutUrl="/sign-in" />
        </div>
      </div>
      <div className="mt-3">
        <EntityBookSelector />
      </div>
    </header>
  )
}
