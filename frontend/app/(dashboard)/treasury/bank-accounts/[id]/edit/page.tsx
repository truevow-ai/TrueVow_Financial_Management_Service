'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { BankAccountFormPage } from '@/components/pages/treasury/BankAccountFormPage'

export default function EditBankAccount() {
  useClerkToken()
  return <BankAccountFormPage />
}
