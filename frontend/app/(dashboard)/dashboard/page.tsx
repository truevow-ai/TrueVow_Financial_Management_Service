'use client'

import { DashboardPage } from '@/components/pages/dashboard/DashboardPage'
import { useClerkToken } from '@/hooks/useClerkToken'

export default function Dashboard() {
  useClerkToken() // Initialize token for API calls
  return <DashboardPage />
}
