'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { JournalEntryDetailPage } from '@/components/pages/journal-entries/JournalEntryDetailPage'

export default function JournalEntryDetail() {
  useClerkToken()
  return <JournalEntryDetailPage />
}
