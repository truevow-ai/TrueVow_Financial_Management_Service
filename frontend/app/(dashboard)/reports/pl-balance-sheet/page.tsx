'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { PLBalanceSheetPage } from '@/components/pages/reports/PLBalanceSheetPage'

export default function PLBalanceSheet() {
  useClerkToken()
  return <PLBalanceSheetPage />
}
