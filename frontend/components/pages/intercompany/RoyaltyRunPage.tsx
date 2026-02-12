"use client"

import React, { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { TrendingUp, Play, Send, Check, X, FileText, Download } from 'lucide-react'
import { Button } from '../../common/Button'
import { Badge } from '../../common/Badge'
import { GlobalToolbar, ApprovalStatus } from '../../common/GlobalToolbar'
import { ApprovalStatusBanner } from '../../common/ApprovalStatusBanner'
import { ApprovalActionButtons } from '../../common/ApprovalActionButtons'
import { VirtualizedTableWrapper } from '../../common/VirtualizedTableWrapper'

interface RoyaltyRunDetail {
  id: string
  periodId: string
  periodName: string
  fromEntityId: string
  fromEntityName: string
  toEntityId: string
  toEntityName: string
  basis: 'REVENUE' | 'RECOGNIZED_REVENUE' | 'COLLECTED_REVENUE' | 'FIXED'
  rate: number
  computedBase: number
  computedRoyalty: number
  currency: string
  status: ApprovalStatus
  submittedBy?: string
  submittedAt?: Date
  approvedBy?: string
  approvedAt?: Date
  rejectedBy?: string
  rejectedAt?: Date
  decisionReason?: string
  postedBy?: string
  postedAt?: Date
}

interface RoyaltyDetailLine {
  id: string
  revenueAccountGroup: string
  recognizedRevenueAmount: number
  exclusions: number
  royaltyAmount: number
  currency: string
}

export function RoyaltyRunPage() {
  const params = useParams()
  const router = useRouter()
  const runId = params?.id as string
  
  const [run, setRun] = useState<RoyaltyRunDetail | null>(null)
  const [detailLines, setDetailLines] = useState<RoyaltyDetailLine[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  
  // Mock data - replace with actual API calls
  // const { data: run } = useRoyaltyRun(runId)
  // const { data: lines } = useRoyaltyRunDetails(runId)
  
  const handleGenerate = async () => {
    setIsGenerating(true)
    // TODO: Call API to generate draft
    setTimeout(() => {
      setIsGenerating(false)
      // Refresh data
    }, 2000)
  }
  
  const handleSubmit = async (reason?: string) => {
    // TODO: Call API to submit for approval
    console.log('Submit:', reason)
  }
  
  const handleApprove = async (reason?: string) => {
    // TODO: Call API to approve
    console.log('Approve:', reason)
  }
  
  const handleReject = async (reason: string) => {
    // TODO: Call API to reject
    console.log('Reject:', reason)
  }
  
  const handlePost = async (reason?: string) => {
    // TODO: Call API to post
    console.log('Post:', reason)
  }
  
  if (!run) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-gray-500">Loading royalty run...</p>
        </div>
      </div>
    )
  }
  
  const isReadOnly = run.status === 'POSTED' || run.status === 'PENDING_APPROVAL'
  
  return (
    <div className="flex flex-col h-screen">
      {/* Global Toolbar */}
      <GlobalToolbar
        entityId={run.fromEntityId}
        entityName={run.fromEntityName}
        periodId={run.periodId}
        periodName={run.periodName}
        status={run.status}
        isPosted={run.status === 'POSTED'}
        lastSavedAt={run.postedAt}
        canSubmit={run.status === 'DRAFT'}
        canApprove={run.status === 'PENDING_APPROVAL'}
        canReject={run.status === 'PENDING_APPROVAL'}
        canPost={run.status === 'APPROVED' || run.status === 'DRAFT'}
        onSubmitApproval={handleSubmit}
        onApprove={handleApprove}
        onReject={handleReject}
        onPost={handlePost}
        isLocked={isReadOnly}
      />
      
      <div className="flex-1 overflow-auto p-6">
        {/* Approval Status Banner */}
        <ApprovalStatusBanner
          status={run.status}
          submittedBy={run.submittedBy}
          submittedAt={run.submittedAt}
          approvedBy={run.approvedBy}
          approvedAt={run.approvedAt}
          rejectedBy={run.rejectedBy}
          rejectedAt={run.rejectedAt}
          decisionReason={run.decisionReason}
          postedBy={run.postedBy}
          postedAt={run.postedAt}
          className="mb-6"
        />
        
        {/* Summary Section */}
        <div className="bg-white border rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Royalty Run Summary</h2>
            {run.status === 'DRAFT' && !detailLines.length && (
              <Button
                onClick={handleGenerate}
                disabled={isGenerating}
              >
                <Play className="w-4 h-4 mr-2" />
                {isGenerating ? 'Generating...' : 'Generate Draft'}
              </Button>
            )}
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Period</label>
              <p className="text-lg font-semibold text-gray-900">{run.periodName}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">From Entity</label>
              <p className="text-lg font-semibold text-gray-900">{run.fromEntityName}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">To Entity</label>
              <p className="text-lg font-semibold text-gray-900">{run.toEntityName}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Basis</label>
              <p className="text-lg font-semibold text-gray-900">
                {run.basis.replace('_', ' ')}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Rate</label>
              <p className="text-lg font-semibold text-gray-900">
                {(run.rate * 100).toFixed(2)}%
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Computed Base</label>
              <p className="text-lg font-semibold text-gray-900">
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: run.currency,
                }).format(run.computedBase)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Computed Royalty</label>
              <p className="text-lg font-semibold text-green-600">
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: run.currency,
                }).format(run.computedRoyalty)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Currency</label>
              <p className="text-lg font-semibold text-gray-900">{run.currency}</p>
            </div>
          </div>
        </div>
        
        {/* Detail Grid */}
        {detailLines.length > 0 && (
          <div className="bg-white border rounded-lg">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Royalty Details</h3>
              {run.status === 'POSTED' && (
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              )}
            </div>
            
            <VirtualizedTableWrapper
              data={detailLines}
              renderHeader={() => (
                <tr className="bg-gray-50 border-b">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Revenue Account Group
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Recognized Revenue
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Exclusions
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Royalty Amount
                  </th>
                </tr>
              )}
              renderRow={(line: RoyaltyDetailLine) => (
                <tr key={line.id} className="border-b">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {line.revenueAccountGroup}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: line.currency,
                    }).format(line.recognizedRevenueAmount)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: line.currency,
                    }).format(line.exclusions)}
                  </td>
                  <td className="px-4 py-3 text-sm font-semibold text-green-600">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: line.currency,
                    }).format(line.royaltyAmount)}
                  </td>
                </tr>
              )}
            />
          </div>
        )}
        
        {detailLines.length === 0 && run.status !== 'DRAFT' && (
          <div className="text-center py-12 text-gray-500">
            <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No detail lines available</p>
          </div>
        )}
      </div>
    </div>
  )
}
