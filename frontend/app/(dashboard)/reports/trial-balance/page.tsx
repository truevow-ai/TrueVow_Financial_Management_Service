'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { TrialBalancePage } from '@/components/pages/reports/TrialBalancePage'

export default function TrialBalance() {
  useClerkToken()
  return <TrialBalancePage />
}
