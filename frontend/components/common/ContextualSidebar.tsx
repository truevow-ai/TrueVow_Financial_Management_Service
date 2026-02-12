'use client'

import { ReactNode } from 'react'
import { X } from 'lucide-react'

function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

interface ContextualSidebarProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  width?: string
  className?: string
}

/**
 * Contextual Sidebar (Right Panel)
 * Used by: Slack, Linear, GitHub Issues
 * Pattern: Right-side panel for details/actions
 * Use case: Detail views, metadata, quick actions
 */
export function ContextualSidebar({
  isOpen,
  onClose,
  title,
  children,
  width = 'w-96',
  className,
}: ContextualSidebarProps) {
  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40 lg:hidden"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed right-0 top-0 h-full bg-white border-l border-gray-200 shadow-xl z-50',
          'flex flex-col',
          width,
          className
        )}
        role="complementary"
        aria-label={title || 'Contextual sidebar'}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">{children}</div>
      </aside>
    </>
  )
}
