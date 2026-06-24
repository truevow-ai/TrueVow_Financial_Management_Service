'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { DeferredRevenuePage } from '@/components/pages/ar/DeferredRevenuePage'

export default function RevenueSchedules() {
  useClerkToken()
  return <DeferredRevenuePage />
}
