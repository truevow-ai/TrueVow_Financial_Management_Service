"use client"

import React from 'react'
import { Save, CheckCircle, Clock, Lock } from 'lucide-react'
import { Badge } from './Badge'
import { ApprovalActionButtons, ApprovalStatus } from './ApprovalActionButtons'
import { EntityBookSelector } from './EntityBookSelector'
import { usePeriods } from '@/hooks/usePeriods'
import { useEntityBook } from '@/contexts/EntityBookContext'

export type { ApprovalStatus }

export interface GlobalToolbarProps {
  entityId?: string
  entityName?: string
  bookId?: string
  bookName?: string
  periodId?: string
  periodName?: string
  status: ApprovalStatus
  isPosted?: boolean
  lastSavedAt?: Date | string
  canSubmit?: boolean
  canApprove?: boolean
  canReject?: boolean
  canPost?: boolean
  canReverse?: boolean
  onSubmitApproval?: (reason?: string) => void | Promise<void>
  onApprove?: (reason?: string) => void | Promise<void>
  onReject?: (reason: string) => void | Promise<void>
  onPost?: (reason?: string) => void | Promise<void>
  onReverse?: () => void | Promise<void>
  onSave?: () => void | Promise<void>
  isLocked?: boolean
  className?: string
}

export function GlobalToolbar({
  entityId,
  entityName,
  bookId,
  bookName,
  periodId,
  periodName,
  status,
  isPosted = false,
  lastSavedAt,
  canSubmit = false,
  canApprove = false,
  canReject = false,
  canPost = false,
  canReverse = false,
  onSubmitApproval,
  onApprove,
  onReject,
  onPost,
  onReverse,
  onSave,
  isLocked = false,
  className = '',
}: GlobalToolbarProps) {
  const { selectedEntityId, selectedBookId, selectedEntity, selectedBook } = useEntityBook()
  const { data: periodsData } = usePeriods({
    legal_entity_id: selectedEntityId || undefined,
    book_id: selectedBookId || undefined,
    status: 'open',
  })

  // Use provided values or fall back to context
  const displayEntityId = entityId || selectedEntityId || ''
  const displayEntityName = entityName || selectedEntity?.entity_name || ''
  const displayBookId = bookId || selectedBookId || ''
  const displayBookName = bookName || selectedBook?.book_name || ''

  const getStatusColor = (status: ApprovalStatus) => {
    switch (status) {
      case 'DRAFT':
        return 'bg-gray-100 text-gray-800'
      case 'PENDING_APPROVAL':
        return 'bg-yellow-100 text-yellow-800'
      case 'APPROVED':
        return 'bg-blue-100 text-blue-800'
      case 'POSTED':
        return 'bg-green-100 text-green-800'
      case 'REJECTED':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatLastSaved = (date?: Date | string) => {
    if (!date) return null
    const d = typeof date === 'string' ? new Date(date) : date
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className={`bg-white border-b border-gray-200 px-6 py-3 ${className}`}>
      <div className="flex items-center justify-between">
        {/* Left: Entity/Book/Period Selectors */}
        <div className="flex items-center gap-4">
          <EntityBookSelector />
          
          {/* Period Selector */}
          {displayBookId && periodsData && periodsData.length > 0 && (
            <div className="flex items-center gap-2">
              <label htmlFor="period-select" className="text-sm font-medium text-gray-700 whitespace-nowrap">
                Period:
              </label>
              <select
                id="period-select"
                value={periodId || ''}
                disabled={isLocked || isPosted}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">Select Period</option>
                {periodsData.map((period) => (
                  <option key={period.id} value={period.id}>
                    {period.period_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Status Badge */}
          <Badge className={getStatusColor(status)}>
            {status === 'PENDING_APPROVAL' && <Clock className="w-3 h-3 mr-1" />}
            {status === 'POSTED' && <CheckCircle className="w-3 h-3 mr-1" />}
            {status === 'REJECTED' && <Lock className="w-3 h-3 mr-1" />}
            {status.replace('_', ' ')}
          </Badge>

          {/* Lock Indicator */}
          {isLocked && (
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Lock className="w-4 h-4" />
              <span>Locked</span>
            </div>
          )}
        </div>

        {/* Right: Action Buttons */}
        <div className="flex items-center gap-3">
          {/* Save Button */}
          {onSave && !isPosted && !isLocked && (
            <button
              onClick={onSave}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <Save className="w-4 h-4 inline mr-1" />
              Save
            </button>
          )}

          {/* Last Saved Timestamp */}
          {lastSavedAt && (
            <div className="text-xs text-gray-500">
              Last saved: {formatLastSaved(lastSavedAt)}
            </div>
          )}

          {/* Approval Action Buttons */}
          <ApprovalActionButtons
            status={status}
            canSubmit={canSubmit && !isLocked}
            canApprove={canApprove && !isLocked}
            canReject={canReject && !isLocked}
            canPost={canPost && !isLocked}
            canReverse={canReverse && isPosted}
            onSubmit={onSubmitApproval}
            onApprove={onApprove}
            onReject={onReject}
            onPost={onPost}
            onReverse={onReverse}
          />
        </div>
      </div>
    </div>
  )
}
