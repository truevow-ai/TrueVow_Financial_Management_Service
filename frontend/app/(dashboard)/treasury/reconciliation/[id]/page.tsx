'use client'

import { useParams } from 'next/navigation'
import { useClerkToken } from '@/hooks/useClerkToken'
import { ReconciliationSessionPage } from '@/components/pages/treasury/ReconciliationSessionPage'

export default function ReconciliationSession() {
  useClerkToken()
  const params = useParams()
  const id = (Array.isArray(params?.id) ? params.id[0] : params?.id) || ''
  return <ReconciliationSessionPage sessionId={id} />
}
