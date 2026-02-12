'use client'

import { ReactNode } from 'react'

function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

interface SplitViewProps {
  left: ReactNode
  right: ReactNode
  leftWidth?: string
  rightWidth?: string
  className?: string
  showRight?: boolean
  onCloseRight?: () => void
}

/**
 * Split View / Multi-Pane Layouts
 * Used by: Gmail, Linear, Notion
 * Pattern: List + detail side-by-side
 * Use case: Inbox, ticket views, data tables
 */
export function SplitView({
  left,
  right,
  leftWidth = 'w-1/2',
  rightWidth = 'w-1/2',
  className,
  showRight = true,
  onCloseRight,
}: SplitViewProps) {
  return (
    <div className={cn('flex h-full overflow-hidden', className)}>
      {/* Left Panel - List */}
      <div className={cn('flex-shrink-0 border-r border-gray-200 overflow-y-auto', leftWidth)}>
        {left}
      </div>

      {/* Right Panel - Detail */}
      {showRight && (
        <div className={cn('flex-shrink-0 overflow-y-auto', rightWidth)}>
          {right}
        </div>
      )}
    </div>
  )
}

/**
 * Responsive Split View - collapses to single view on mobile
 */
export function ResponsiveSplitView({
  left,
  right,
  showRight = true,
  onCloseRight,
  className,
}: Omit<SplitViewProps, 'leftWidth' | 'rightWidth'>) {
  return (
    <div className={cn('flex h-full overflow-hidden', className)}>
      {/* Left Panel - List */}
      <div
        className={cn(
          'flex-shrink-0 overflow-y-auto',
          'w-full lg:w-1/2',
          showRight && 'lg:border-r border-gray-200'
        )}
      >
        {left}
      </div>

      {/* Right Panel - Detail */}
      {showRight && (
        <div className="hidden lg:flex flex-shrink-0 w-1/2 overflow-y-auto">
          {right}
        </div>
      )}

      {/* Mobile: Right panel as overlay */}
      {showRight && (
        <div className="lg:hidden fixed inset-0 z-50 bg-white">
          {onCloseRight && (
            <div className="p-4 border-b border-gray-200">
              <button
                onClick={onCloseRight}
                className="text-gray-600 hover:text-gray-900"
                aria-label="Close detail view"
              >
                ← Back
              </button>
            </div>
          )}
          <div className="overflow-y-auto h-full">{right}</div>
        </div>
      )}
    </div>
  )
}
