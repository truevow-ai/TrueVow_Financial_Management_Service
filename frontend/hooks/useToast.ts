'use client'

import { useCallback, useContext } from 'react'
import { ToastStateContext, ToastType, Toast } from '@/contexts/ToastContext'

export const useToast = () => {
  const context = useContext(ToastStateContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  const { toasts, setToasts } = context

  const showToast = useCallback(
    (message: string, type: ToastType = 'info', duration: number = 5000) => {
      const id = `toast-${Date.now()}-${Math.random()}`
      const toast: Toast = { id, message, type, duration }

      setToasts((prev) => [...prev, toast])

      if (duration > 0) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id))
        }, duration)
      }

      return id
    },
    [setToasts]
  )

  const removeToast = useCallback(
    (id: string) => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    },
    [setToasts]
  )

  const success = useCallback(
    (message: string, duration?: number) => {
      return showToast(message, 'success', duration)
    },
    [showToast]
  )

  const error = useCallback(
    (message: string, duration?: number) => {
      return showToast(message, 'error', duration)
    },
    [showToast]
  )

  const warning = useCallback(
    (message: string, duration?: number) => {
      return showToast(message, 'warning', duration)
    },
    [showToast]
  )

  const info = useCallback(
    (message: string, duration?: number) => {
      return showToast(message, 'info', duration)
    },
    [showToast]
  )

  return {
    toasts,
    showToast,
    removeToast,
    success,
    error,
    warning,
    info,
  }
}
