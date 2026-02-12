'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useClerkToken } from '@/hooks/useClerkToken'
import { ChartOfAccountsPage } from '@/components/pages/chart-of-accounts/ChartOfAccountsPage'

export default function ChartOfAccounts() {
  useClerkToken()
  return <ChartOfAccountsPage />
}
