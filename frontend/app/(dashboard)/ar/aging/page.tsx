'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { ARAgingPage } from '@/components/pages/ar/ARAgingPage'

export default function ARAging() {
  useClerkToken()
  return <ARAgingPage />
}
