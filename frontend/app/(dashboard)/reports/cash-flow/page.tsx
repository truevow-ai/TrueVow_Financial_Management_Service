'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { CashFlowPage } from '@/components/pages/reports/CashFlowPage'

export default function CashFlow() {
  useClerkToken()
  return <CashFlowPage />
}
