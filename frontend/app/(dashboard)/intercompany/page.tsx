'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { IntercompanyTransferListPage } from '@/components/pages/intercompany/IntercompanyTransferListPage'

export default function Intercompany() {
  useClerkToken()
  return <IntercompanyTransferListPage />
}
