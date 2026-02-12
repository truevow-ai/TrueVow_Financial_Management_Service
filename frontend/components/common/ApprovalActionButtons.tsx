"use client"

import React, { useState } from 'react'
import { Send, Check, X, FileText, RotateCcw } from 'lucide-react'
import { Button } from '../ui/button'
import { Dialog } from './Dialog'
import { Textarea } from './Textarea'

export type ApprovalStatus = 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'POSTED' | 'REJECTED'

export interface ApprovalActionButtonsProps {
  status: ApprovalStatus
  canSubmit?: boolean
  canApprove?: boolean
  canReject?: boolean
  canPost?: boolean
  canReverse?: boolean
  onSubmit?: (reason?: string) => void
  onApprove?: (reason?: string) => void
  onReject?: (reason: string) => void
  onPost?: (reason?: string) => void
  onReverse?: () => void
  className?: string
}

export function ApprovalActionButtons({
  status,
  canSubmit = false,
  canApprove = false,
  canReject = false,
  canPost = false,
  canReverse = false,
  onSubmit,
  onApprove,
  onReject,
  onPost,
  onReverse,
  className = '',
}: ApprovalActionButtonsProps) {
  const [showSubmitDialog, setShowSubmitDialog] = useState(false)
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [showRejectDialog, setShowRejectDialog] = useState(false)
  const [showPostDialog, setShowPostDialog] = useState(false)
  const [reason, setReason] = useState('')
  
  const handleSubmit = () => {
    if (onSubmit) {
      onSubmit(reason || undefined)
      setReason('')
      setShowSubmitDialog(false)
    }
  }
  
  const handleApprove = () => {
    if (onApprove) {
      onApprove(reason || undefined)
      setReason('')
      setShowApproveDialog(false)
    }
  }
  
  const handleReject = () => {
    if (reason.trim()) {
      if (onReject) {
        onReject(reason)
        setReason('')
        setShowRejectDialog(false)
      }
    }
  }
  
  const handlePost = () => {
    if (onPost) {
      onPost(reason || undefined)
      setReason('')
      setShowPostDialog(false)
    }
  }
  
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Submit for Approval */}
      {canSubmit && status === 'DRAFT' && onSubmit && (
        <>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSubmitDialog(true)}
          >
            <Send className="w-4 h-4 mr-1" />
            Submit for Approval
          </Button>
          <Dialog
            open={showSubmitDialog}
            onClose={() => {
              setShowSubmitDialog(false)
              setReason('')
            }}
            title="Submit for Approval"
          >
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Are you ready to submit this for approval? Once submitted, you won&apos;t be able to edit it until it&apos;s approved or rejected.
              </p>
              <Textarea
                label="Reason (optional)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Add any notes for the approver..."
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowSubmitDialog(false)
                    setReason('')
                  }}
                >
                  Cancel
                </Button>
                <Button onClick={handleSubmit}>
                  Submit
                </Button>
              </div>
            </div>
          </Dialog>
        </>
      )}
      
      {/* Approve */}
      {canApprove && status === 'PENDING_APPROVAL' && onApprove && (
        <>
          <Button
            variant="default"
            size="sm"
            onClick={() => setShowApproveDialog(true)}
          >
            <Check className="w-4 h-4 mr-1" />
            Approve
          </Button>
          <Dialog
            open={showApproveDialog}
            onClose={() => {
              setShowApproveDialog(false)
              setReason('')
            }}
            title="Approve"
          >
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Approve this submission? It will be ready for posting.
              </p>
              <Textarea
                label="Reason (optional)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Add any notes..."
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowApproveDialog(false)
                    setReason('')
                  }}
                >
                  Cancel
                </Button>
                <Button onClick={handleApprove}>
                  Approve
                </Button>
              </div>
            </div>
          </Dialog>
        </>
      )}
      
      {/* Reject */}
      {canReject && status === 'PENDING_APPROVAL' && onReject && (
        <>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowRejectDialog(true)}
          >
            <X className="w-4 h-4 mr-1" />
            Reject
          </Button>
          <Dialog
            open={showRejectDialog}
            onClose={() => {
              setShowRejectDialog(false)
              setReason('')
            }}
            title="Reject"
          >
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Reject this submission? The submitter will need to make changes and resubmit.
              </p>
              <Textarea
                label="Reason (required)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Explain why this is being rejected..."
                rows={3}
                required
              />
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowRejectDialog(false)
                    setReason('')
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleReject}
                  disabled={!reason.trim()}
                >
                  Reject
                </Button>
              </div>
            </div>
          </Dialog>
        </>
      )}
      
      {/* Post */}
      {canPost && (status === 'APPROVED' || status === 'DRAFT') && onPost && (
        <>
          <Button
            variant="default"
            size="sm"
            onClick={() => setShowPostDialog(true)}
          >
            <FileText className="w-4 h-4 mr-1" />
            Post
          </Button>
          <Dialog
            open={showPostDialog}
            onClose={() => {
              setShowPostDialog(false)
              setReason('')
            }}
            title="Post"
          >
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Post this entry? Once posted, it will be immutable and cannot be edited.
              </p>
              <Textarea
                label="Reason (optional)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Add any notes..."
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowPostDialog(false)
                    setReason('')
                  }}
                >
                  Cancel
                </Button>
                <Button onClick={handlePost}>
                  Post
                </Button>
              </div>
            </div>
          </Dialog>
        </>
      )}
      
      {/* Reverse & Copy */}
      {canReverse && status === 'POSTED' && onReverse && (
        <Button
          variant="outline"
          size="sm"
          onClick={onReverse}
        >
          <RotateCcw className="w-4 h-4 mr-1" />
          Reverse & Copy
        </Button>
      )}
    </div>
  )
}
