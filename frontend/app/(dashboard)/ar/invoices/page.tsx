'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { ARInvoiceListPage } from '@/components/pages/ar/ARInvoiceListPage'

export default function ARInvoices() {
  useClerkToken()
  return <ARInvoiceListPage />
}
