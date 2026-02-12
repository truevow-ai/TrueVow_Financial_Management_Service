'use client'

import { ReactNode, useState } from 'react'
import { LayoutGrid, FileText } from 'lucide-react'

interface DualModeEditorProps {
  formMode: ReactNode
  gridMode: ReactNode
  defaultMode?: 'form' | 'grid'
  onModeChange?: (mode: 'form' | 'grid') => void
  className?: string
}

/**
 * Dual-Mode Editor Component
 * Toggles between Form Mode (guided) and Grid Mode (spreadsheet-style)
 * Used for: Journal Entries, AP Bills, Payroll Adjustments
 */
export function DualModeEditor({
  formMode,
  gridMode,
  defaultMode = 'form',
  onModeChange,
  className,
}: DualModeEditorProps) {
  const [mode, setMode] = useState<'form' | 'grid'>(defaultMode)

  const handleModeChange = (newMode: 'form' | 'grid') => {
    setMode(newMode)
    onModeChange?.(newMode)
  }

  return (
    <div className={className}>
      {/* Mode Toggle */}
      <div className="flex items-center justify-end gap-2 mb-4 p-2 bg-gray-50 rounded-lg border border-gray-200">
        <span className="text-sm text-gray-600 mr-2">Entry Mode:</span>
        <button
          onClick={() => handleModeChange('form')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === 'form'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
          aria-label="Form mode"
        >
          <FileText className="w-4 h-4" />
          Form
        </button>
        <button
          onClick={() => handleModeChange('grid')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === 'grid'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
          aria-label="Grid mode"
        >
          <LayoutGrid className="w-4 h-4" />
          Grid
        </button>
      </div>

      {/* Content */}
      <div className="mt-4">{mode === 'form' ? formMode : gridMode}</div>
    </div>
  )
}
