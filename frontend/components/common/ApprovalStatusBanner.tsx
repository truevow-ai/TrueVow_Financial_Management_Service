"use client"

import React from 'react'
import { CheckCircle, XCircle, Clock, User, Calendar } from 'lucide-react'
import { ApprovalStatus } from './GlobalToolbar'
import { formatDateTime } from '@/lib/utils/format'

export interface ApprovalStatusBannerProps {
  status: ApprovalStatus
  submittedBy?: string
  submittedAt?: Date | string
  approvedBy?: string
  approvedAt?: Date | string
  rejectedBy?: string
  rejectedAt?: Date | string
  decisionReason?: string
  postedBy?: string
  postedAt?: Date | string
  className?: string
}

export function ApprovalStatusBanner({
  status,
  submittedBy,
  submittedAt,
  approvedBy,
  approvedAt,
  rejectedBy,
  rejectedAt,
  decisionReason,
  postedBy,
  postedAt,
  className = '',
}: ApprovalStatusBannerProps) {
  const getBannerColor = () => {
    switch (status) {
      case 'DRAFT':
        return 'bg-gray-50 border-gray-200'
      case 'PENDING_APPROVAL':
        return 'bg-yellow-50 border-yellow-200'
      case 'APPROVED':
        return 'bg-blue-50 border-blue-200'
      case 'POSTED':
        return 'bg-green-50 border-green-200'
      case 'REJECTED':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const getIcon = () => {
    switch (status) {
      case 'PENDING_APPROVAL':
        return <Clock className="w-5 h-5 text-yellow-600" />
      case 'APPROVED':
        return <CheckCircle className="w-5 h-5 text-blue-600" />
      case 'POSTED':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'REJECTED':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return null
    }
  }

  const formatDateDisplay = (date?: Date | string) => {
    if (!date) return null
    return formatDateTime(date)
  }

  if (status === 'DRAFT') {
    return null // Don't show banner for drafts
  }

  return (
    <div className={`border rounded-lg p-4 ${getBannerColor()} ${className}`}>
      <div className="flex items-start gap-3">
        {getIcon()}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold text-gray-900">
              {status === 'PENDING_APPROVAL' && 'Pending Approval'}
              {status === 'APPROVED' && 'Approved'}
              {status === 'POSTED' && 'Posted'}
              {status === 'REJECTED' && 'Rejected'}
            </h3>
          </div>

          <div className="space-y-1 text-sm text-gray-700">
            {/* Submitted Info */}
            {submittedBy && submittedAt && (
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-500" />
                <span>Submitted by {submittedBy}</span>
                <Calendar className="w-4 h-4 text-gray-500 ml-2" />
                <span>{formatDateDisplay(submittedAt)}</span>
              </div>
            )}

            {/* Approved Info */}
            {approvedBy && approvedAt && (
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span>Approved by {approvedBy}</span>
                <Calendar className="w-4 h-4 text-gray-500 ml-2" />
                <span>{formatDateDisplay(approvedAt)}</span>
              </div>
            )}

            {/* Rejected Info */}
            {rejectedBy && rejectedAt && (
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-600" />
                <span>Rejected by {rejectedBy}</span>
                <Calendar className="w-4 h-4 text-gray-500 ml-2" />
                <span>{formatDateTime(rejectedAt)}</span>
              </div>
            )}

            {/* Posted Info */}
            {postedBy && postedAt && (
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span>Posted by {postedBy}</span>
                <Calendar className="w-4 h-4 text-gray-500 ml-2" />
                <span>{formatDateDisplay(postedAt)}</span>
              </div>
            )}

            {/* Decision Reason */}
            {decisionReason && (
              <div className="mt-2 pt-2 border-t border-gray-300">
                <p className="text-sm font-medium text-gray-900 mb-1">Reason:</p>
                <p className="text-sm text-gray-700">{decisionReason}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
