'use client'

import { useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'

interface VirtualizedTableProps<T> {
  data: T[]
  renderRow: (item: T, index: number) => React.ReactNode
  estimateSize?: (index: number) => number
  overscan?: number
  className?: string
  height?: string | number
}

export function VirtualizedTable<T>({
  data,
  renderRow,
  estimateSize = () => 50,
  overscan = 5,
  className = '',
  height = 600,
}: VirtualizedTableProps<T>) {
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
      role="table"
      aria-label="Virtualized table"
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
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
          </div>
        ))}
      </div>
    </div>
  )
}
