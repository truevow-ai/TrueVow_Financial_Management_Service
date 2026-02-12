'use client'

import { useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'

interface VirtualizedTableBodyProps<T> {
  data: T[]
  renderRow: (item: T, index: number) => React.ReactNode
  estimateSize?: (index: number) => number
  overscan?: number
  className?: string
  height?: string | number
}

/**
 * Virtualized table body for large lists
 * Use this inside a <table> element, replacing <tbody>
 * 
 * Example:
 * <table>
 *   <thead>...</thead>
 *   <VirtualizedTableBody data={items} renderRow={...} />
 * </table>
 */
export function VirtualizedTableBody<T>({
  data,
  renderRow,
  estimateSize = () => 50,
  overscan = 5,
  className = '',
  height = 600,
}: VirtualizedTableBodyProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize,
    overscan,
  })

  return (
    <div
      ref={parentRef}
      className={`overflow-auto ${className}`}
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
      role="presentation"
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        <table className="min-w-full divide-y divide-gray-200" style={{ width: '100%' }}>
          <tbody className="bg-white divide-y divide-gray-200">
            {virtualizer.getVirtualItems().map((virtualItem) => (
              <tr
                key={virtualItem.key}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualItem.size}px`,
                  transform: `translateY(${virtualItem.start}px)`,
                }}
                role="row"
                aria-rowindex={virtualItem.index + 1}
              >
                {renderRow(data[virtualItem.index], virtualItem.index)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
