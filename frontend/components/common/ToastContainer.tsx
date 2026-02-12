'use client'

import { useContext } from 'react'
import { ToastStateContext } from '@/contexts/ToastContext'

export default function ToastContainer() {
  const context = useContext(ToastStateContext)
  if (!context) return null
  
  const { toasts, setToasts } = context

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed top-4 right-4 z-50 space-y-2"
      role="region"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`min-w-[300px] max-w-md rounded-lg shadow-lg p-4 flex items-start gap-3 ${
            toast.type === 'success'
              ? 'bg-green-50 border border-green-200'
              : toast.type === 'error'
              ? 'bg-red-50 border border-red-200'
              : toast.type === 'warning'
              ? 'bg-yellow-50 border border-yellow-200'
              : 'bg-blue-50 border border-blue-200'
          }`}
          role="alert"
        >
          <div
            className={`flex-shrink-0 ${
              toast.type === 'success'
                ? 'text-green-600'
                : toast.type === 'error'
                ? 'text-red-600'
                : toast.type === 'warning'
                ? 'text-yellow-600'
                : 'text-blue-600'
            }`}
          >
            {toast.type === 'success' && '✓'}
            {toast.type === 'error' && '✕'}
            {toast.type === 'warning' && '⚠'}
            {toast.type === 'info' && 'ℹ'}
          </div>
          <div className="flex-1">
            <p
              className={`text-sm font-medium ${
                toast.type === 'success'
                  ? 'text-green-800'
                  : toast.type === 'error'
                  ? 'text-red-800'
                  : toast.type === 'warning'
                  ? 'text-yellow-800'
                  : 'text-blue-800'
              }`}
            >
              {toast.message}
            </p>
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600"
            aria-label="Close notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
