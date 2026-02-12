'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { ReportsPage } from '@/components/pages/reports/ReportsPage'

export default function Reports() {
  useClerkToken()
  return <ReportsPage />
}
