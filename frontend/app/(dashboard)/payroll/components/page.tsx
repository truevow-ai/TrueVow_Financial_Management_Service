'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { PayComponentListPage } from '@/components/pages/payroll/PayComponentListPage'

export default function PayComponents() {
  useClerkToken()
  return <PayComponentListPage />
}
