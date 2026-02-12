'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { EmployeeListPage } from '@/components/pages/payroll/EmployeeListPage'

export default function Employees() {
  useClerkToken()
  return <EmployeeListPage />
}
