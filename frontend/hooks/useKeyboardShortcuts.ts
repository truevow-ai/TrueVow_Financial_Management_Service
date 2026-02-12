'use client'

import { useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'

interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  metaKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  action: () => void
  description?: string
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[]
  enabled?: boolean
}

/**
 * Enhanced Keyboard Navigation Hook
 * Provides comprehensive keyboard shortcuts for power users
 * 
 * Common shortcuts:
 * - Cmd/Ctrl + K: Command palette (global)
 * - Cmd/Ctrl + N: New item
 * - Cmd/Ctrl + S: Save
 * - Escape: Close/Cancel
 * - Enter: Submit/View
 * - Arrow keys: Navigate
 */
export function useKeyboardShortcuts({ shortcuts, enabled = true }: UseKeyboardShortcutsOptions) {
  const router = useRouter()

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return

      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Allow Escape and Cmd/Ctrl shortcuts even in inputs
        if (event.key !== 'Escape' && !event.metaKey && !event.ctrlKey) {
          return
        }
      }

      for (const shortcut of shortcuts) {
        const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase()
        const ctrlMatches = shortcut.ctrlKey ? event.ctrlKey : !event.ctrlKey
        const metaMatches = shortcut.metaKey ? event.metaKey : !event.metaKey
        const shiftMatches = shortcut.shiftKey ? event.shiftKey : !event.shiftKey
        const altMatches = shortcut.altKey ? event.altKey : !event.altKey

        if (keyMatches && ctrlMatches && metaMatches && shiftMatches && altMatches) {
          event.preventDefault()
          shortcut.action()
          break
        }
      }
    },
    [shortcuts, enabled]
  )

  useEffect(() => {
    if (!enabled) return

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown, enabled])
}

/**
 * Common keyboard shortcuts for list pages
 */
export function useListPageShortcuts({
  onNew,
  onSearch,
  onRefresh,
  enabled = true,
}: {
  onNew?: () => void
  onSearch?: () => void
  onRefresh?: () => void
  enabled?: boolean
}) {
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 'n',
        metaKey: true,
        action: () => onNew?.(),
        description: 'Create new item',
      },
      {
        key: 'k',
        metaKey: true,
        action: () => onSearch?.(),
        description: 'Open search',
      },
      {
        key: 'r',
        metaKey: true,
        action: () => onRefresh?.(),
        description: 'Refresh',
      },
      {
        key: 'Enter',
        action: () => {
          // Navigate to first item if available
          const firstLink = document.querySelector('tbody tr:first-child a')
          if (firstLink instanceof HTMLAnchorElement) {
            firstLink.click()
          }
        },
        description: 'View first item',
      },
    ],
    enabled,
  })
}

/**
 * Common keyboard shortcuts for form pages
 */
export function useFormPageShortcuts({
  onSave,
  onCancel,
  enabled = true,
}: {
  onSave?: () => void
  onCancel?: () => void
  enabled?: boolean
}) {
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 's',
        metaKey: true,
        action: () => onSave?.(),
        description: 'Save',
      },
      {
        key: 'Escape',
        action: () => onCancel?.(),
        description: 'Cancel',
      },
    ],
    enabled,
  })
}
