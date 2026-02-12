'use client'

import { useAuth } from '@clerk/nextjs'
import { useEffect } from 'react'

export function useClerkToken() {
  const { getToken } = useAuth()

  useEffect(() => {
    // Store token in localStorage for API client interceptor
    const updateToken = async () => {
      const token = await getToken()
      if (token) {
        localStorage.setItem('clerk_token', token)
      } else {
        localStorage.removeItem('clerk_token')
      }
    }
    updateToken()
  }, [getToken])

  return { getToken }
}
