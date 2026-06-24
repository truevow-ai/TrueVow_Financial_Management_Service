'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { PeriodFormPage } from '@/components/pages/periods/PeriodFormPage'

export default function NewPeriod() {
  useClerkToken()
  return <PeriodFormPage />
}
