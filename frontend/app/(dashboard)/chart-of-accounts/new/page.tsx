'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { ChartOfAccountFormPage } from '@/components/pages/chart-of-accounts/ChartOfAccountFormPage'

export default function NewChartOfAccount() {
  useClerkToken()
  return <ChartOfAccountFormPage />
}
