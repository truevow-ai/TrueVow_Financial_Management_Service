'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { JournalEntryCreatePage } from '@/components/pages/journal-entries/JournalEntryCreatePage'

export default function NewJournalEntry() {
  useClerkToken()
  return <JournalEntryCreatePage />
}
