"use client"

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { FileText, Receipt, Users, Banknote, TrendingUp, CheckCircle2, AlertCircle, Clock, Send, Download } from 'lucide-react'
import { Button } from '../../ui/button'
import { Badge } from '../../common/Badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../common/Tabs'
import { VirtualizedTableWrapper } from '../../common/VirtualizedTableWrapper'

type DraftType = 'journal_entries' | 'ap_bills' | 'payroll_runs' | 'rec_adjustments' | 'royalty_runs'

interface DraftItem {
  id: string
  type: DraftType
  createdAt: Date
  createdBy: string
  entityName: string
  bookName: string
  periodName: string
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED'
  errorCount: number
  amount?: number
  total?: number
  nextAction: 'validate' | 'submit' | 'approve' | 'post'
}

export function DraftInboxPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<DraftType>('journal_entries')
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  
  const drafts: Record<DraftType, DraftItem[]> = {
    journal_entries: [],
    ap_bills: [],
    payroll_runs: [],
    rec_adjustments: [],
    royalty_runs: [],
  }
  
  const currentDrafts = drafts[activeTab] || []
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT': return 'bg-gray-100 text-gray-800'
      case 'PENDING_APPROVAL': return 'bg-yellow-100 text-yellow-800'
      case 'APPROVED': return 'bg-blue-100 text-blue-800'
      case 'REJECTED': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }
  
  const getNextActionLabel = (action: string) => {
    switch (action) {
      case 'validate': return 'Validate'
      case 'submit': return 'Submit'
      case 'approve': return 'Approve'
      case 'post': return 'Post'
      default: return action
    }
  }
  
  const handleValidate = (itemIds: string[]) => {
    console.log('Validate:', itemIds)
  }
  
  const handleSubmit = (itemIds: string[]) => {
    console.log('Submit:', itemIds)
  }
  
  const handleExportErrors = (itemIds: string[]) => {
    console.log('Export errors:', itemIds)
  }
  
  const handleRowClick = (item: DraftItem) => {
    switch (item.type) {
      case 'journal_entries':
        router.push(`/journal-entries/${item.id}`)
        break
      case 'ap_bills':
        router.push(`/ap/invoices/${item.id}`)
        break
      case 'payroll_runs':
        router.push(`/payroll/runs/${item.id}`)
        break
      case 'rec_adjustments':
        router.push(`/reconciliations/${item.id}`)
        break
      case 'royalty_runs':
        router.push(`/intercompany/royalties/${item.id}`)
        break
    }
  }
  
  const renderHeader = () => (
    <tr className="bg-gray-50 border-b">
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
        <input
          type="checkbox"
          checked={selectedItems.size === currentDrafts.length && currentDrafts.length > 0}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedItems(new Set(currentDrafts.map(d => d.id)))
            } else {
              setSelectedItems(new Set())
            }
          }}
          className="rounded border-gray-300"
        />
      </th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created By</th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entity / Book / Period</th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Errors</th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Next Action</th>
    </tr>
  )
  
  const renderRow = (item: DraftItem) => (
    <tr key={item.id} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => handleRowClick(item)}>
      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
        <input
          type="checkbox"
          checked={selectedItems.has(item.id)}
          onChange={(e) => {
            const newSelected = new Set(selectedItems)
            if (e.target.checked) {
              newSelected.add(item.id)
            } else {
              newSelected.delete(item.id)
            }
            setSelectedItems(newSelected)
          }}
          className="rounded border-gray-300"
        />
      </td>
      <td className="px-4 py-3 text-sm text-gray-900">{item.createdAt.toLocaleString()}</td>
      <td className="px-4 py-3 text-sm text-gray-900">{item.createdBy}</td>
      <td className="px-4 py-3 text-sm text-gray-900">
        <div className="flex flex-col">
          <span>{item.entityName}</span>
          <span className="text-xs text-gray-500">{item.bookName} / {item.periodName}</span>
        </div>
      </td>
      <td className="px-4 py-3">
        <Badge className={getStatusColor(item.status)}>{item.status.replace('_', ' ')}</Badge>
      </td>
      <td className="px-4 py-3 text-sm">
        {item.errorCount > 0 ? (
          <span className="flex items-center gap-1 text-red-600">
            <AlertCircle className="w-4 h-4" />
            {item.errorCount}
          </span>
        ) : (
          <span className="flex items-center gap-1 text-green-600">
            <CheckCircle2 className="w-4 h-4" />
            0
          </span>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-gray-900">
        {item.amount !== undefined
          ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.amount)
          : item.total !== undefined
          ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.total)
          : '-'}
      </td>
      <td className="px-4 py-3">
        <Badge className="bg-blue-100 text-blue-800">{getNextActionLabel(item.nextAction)}</Badge>
      </td>
    </tr>
  )
  
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Draft Inbox</h1>
        <p className="text-sm text-gray-600 mt-1">Manage and review all draft entries before posting</p>
      </div>
      {selectedItems.size > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
          <span className="text-sm text-blue-800">{selectedItems.size} item(s) selected</span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => handleValidate(Array.from(selectedItems))}>
              <CheckCircle2 className="w-4 h-4 mr-1" />
              Validate Selected
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleExportErrors(Array.from(selectedItems))}>
              <Download className="w-4 h-4 mr-1" />
              Export Errors CSV
            </Button>
            <Button variant="default" size="sm" onClick={() => handleSubmit(Array.from(selectedItems))}>
              <Send className="w-4 h-4 mr-1" />
              Submit Selected
            </Button>
          </div>
        </div>
      )}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as DraftType)}>
        <TabsList>
          <TabsTrigger value="journal_entries">
            <FileText className="w-4 h-4 mr-2" />
            Journal Entries
          </TabsTrigger>
          <TabsTrigger value="ap_bills">
            <Receipt className="w-4 h-4 mr-2" />
            AP Bills
          </TabsTrigger>
          <TabsTrigger value="payroll_runs">
            <Users className="w-4 h-4 mr-2" />
            Payroll Runs
          </TabsTrigger>
          <TabsTrigger value="rec_adjustments">
            <Banknote className="w-4 h-4 mr-2" />
            Rec Adjustments
          </TabsTrigger>
          <TabsTrigger value="royalty_runs">
            <TrendingUp className="w-4 h-4 mr-2" />
            Royalty Runs
          </TabsTrigger>
        </TabsList>
        <TabsContent value={activeTab} className="mt-4">
          {currentDrafts.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No drafts found for {activeTab.replace('_', ' ')}</p>
            </div>
          ) : (
            <VirtualizedTableWrapper data={currentDrafts} renderHeader={renderHeader} renderRow={renderRow} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
