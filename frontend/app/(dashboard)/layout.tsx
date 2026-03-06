'use client'

import { redirect } from 'next/navigation'
import { Layout } from '@/components/layout/Layout'
import { EntityBookProvider } from '@/contexts/EntityBookContext'
import { useAuth } from '@clerk/nextjs'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isSignedIn } = useAuth()

  if (!isSignedIn) {
    redirect('/sign-in')
  }

  return (
    <EntityBookProvider>
      <Layout>{children}</Layout>
    </EntityBookProvider>
  )
}
