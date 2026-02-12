'use client'

import { useRef, ReactNode } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'

interface VirtualizedTableWrapperProps<T> {
  data: T[]
  renderHeader: () => ReactNode
  renderRow: (item: T, index: number) => ReactNode
  estimateSize?: (index: number) => number
  overscan?: number
  className?: string
  height?: string | number
  emptyMessage?: ReactNode
}

/**
 * Complete virtualized table component with sticky header
 * Use this to replace entire table structures for large lists
 */
export function VirtualizedTableWrapper<T>({
  data,
  renderHeader,
  renderRow,
  estimateSize = () => 50,
  overscan = 5,
  className = '',
  height = 600,
  emptyMessage,
}: VirtualizedTableWrapperProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize,
    overscan,
  })

  if (data.length === 0 && emptyMessage) {
    return <div className={className}>{emptyMessage}</div>
  }

  return (
    <div className={`overflow-hidden border border-gray-200 rounded-lg ${className}`}>
      {/* Sticky Header */}
      <div className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>{renderHeader()}</thead>
        </table>
      </div>

      {/* Virtualized Body */}
      <div
        ref={parentRef}
        className="overflow-auto"
        style={{ height: typeof height === 'number' ? `${height}px` : height }}
      >
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          <table className="min-w-full divide-y divide-gray-200">
            <tbody className="bg-white divide-y divide-gray-200">
              {virtualizer.getVirtualItems().map((virtualItem) => {
                const item = data[virtualItem.index]
                return (
                  <tr
                    key={virtualItem.key}
                    data-index={virtualItem.index}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: `${virtualItem.size}px`,
                      transform: `translateY(${virtualItem.start}px)`,
                    }}
                    className="hover:bg-gray-50"
                  >
                    {renderRow(item, virtualItem.index)}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
