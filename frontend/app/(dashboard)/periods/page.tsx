'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { PeriodListPage } from '@/components/pages/periods/PeriodListPage'

export default function Periods() {
  useClerkToken()
  return <PeriodListPage />
}
