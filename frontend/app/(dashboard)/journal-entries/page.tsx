'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { JournalEntryListPage } from '@/components/pages/journal-entries/JournalEntryListPage'

export default function JournalEntries() {
  useClerkToken()
  return <JournalEntryListPage />
}
