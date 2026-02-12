'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { BankAccountListPage } from '@/components/pages/treasury/BankAccountListPage'

export default function BankAccounts() {
  useClerkToken()
  return <BankAccountListPage />
}
