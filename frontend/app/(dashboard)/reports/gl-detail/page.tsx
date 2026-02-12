'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { GLDetailPage } from '@/components/pages/reports/GLDetailPage'

export default function GLDetail() {
  useClerkToken()
  return <GLDetailPage />
}
