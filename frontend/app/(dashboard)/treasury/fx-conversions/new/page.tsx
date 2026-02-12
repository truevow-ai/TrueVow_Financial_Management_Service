'use client'

import { useClerkToken } from '@/hooks/useClerkToken'
import { FXConversionFormPage } from '@/components/pages/treasury/FXConversionFormPage'

export default function NewFXConversion() {
  useClerkToken()
  return <FXConversionFormPage />
}
