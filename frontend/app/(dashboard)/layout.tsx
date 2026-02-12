import { auth } from '@clerk/nextjs'
import { redirect } from 'next/navigation'
import { Layout } from '@/components/layout/Layout'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { userId } = await auth()

  if (!userId) {
    redirect('/sign-in')
  }

  return <Layout>{children}</Layout>
}
