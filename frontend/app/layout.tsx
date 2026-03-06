import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import { QueryClientProvider } from './providers/QueryProvider'
import { ToastProvider } from '@/contexts/ToastContext'
import { EntityBookProvider } from '@/contexts/EntityBookContext'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TrueVow Financial Management',
  description: 'Comprehensive financial management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={inter.className}>
          <QueryClientProvider>
            <ToastProvider>
              {children}
            </ToastProvider>
          </QueryClientProvider>
        </body>
      </html>
    </ClerkProvider>
  )
}
