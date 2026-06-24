'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { APAgingPage } from '@/components/pages/ap/APAgingPage'

export default function APAging() {
  useClerkToken()
  return <APAgingPage />
}
