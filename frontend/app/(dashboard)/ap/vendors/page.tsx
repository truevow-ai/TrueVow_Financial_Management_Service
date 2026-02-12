'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { APVendorListPage } from '@/components/pages/ap/APVendorListPage'

export default function APVendors() {
  useClerkToken()
  return <APVendorListPage />
}
