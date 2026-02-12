'use client'

import React, { createContext, useContext, ReactNode, useState, useEffect, useCallback } from 'react'
import { glApi, LegalEntity, Book } from '@/lib/api/glApi'
import { useToastContext } from './ToastContext'

interface EntityBookContextType {
  entities: LegalEntity[]
  books: Book[]
  selectedEntityId: string | null
  selectedBookId: string | null
  selectedEntity: LegalEntity | null
  selectedBook: Book | null
  isLoading: boolean
  setSelectedEntityId: (entityId: string | null) => void
  setSelectedBookId: (bookId: string | null) => void
  refreshEntities: () => Promise<void>
  refreshBooks: () => Promise<void>
}

const EntityBookContext = createContext<EntityBookContextType | undefined>(undefined)

export const useEntityBook = () => {
  const context = useContext(EntityBookContext)
  if (!context) {
    throw new Error('useEntityBook must be used within EntityBookProvider')
  }
  return context
}

interface EntityBookProviderProps {
  children: ReactNode
}

const STORAGE_KEY_ENTITY = 'truevow_selected_entity_id'
const STORAGE_KEY_BOOK = 'truevow_selected_book_id'

export const EntityBookProvider: React.FC<EntityBookProviderProps> = ({ children }) => {
  const [entities, setEntities] = useState<LegalEntity[]>([])
  const [books, setBooks] = useState<Book[]>([])
  const [selectedEntityId, setSelectedEntityIdState] = useState<string | null>(null)
  const [selectedBookId, setSelectedBookIdState] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { error: showError } = useToastContext()

  // Load from localStorage on mount
  useEffect(() => {
    const savedEntityId = localStorage.getItem(STORAGE_KEY_ENTITY)
    const savedBookId = localStorage.getItem(STORAGE_KEY_BOOK)
    if (savedEntityId) setSelectedEntityIdState(savedEntityId)
    if (savedBookId) setSelectedBookIdState(savedBookId)
  }, [])

  // Fetch entities
  const refreshEntities = useCallback(async () => {
    try {
      const data = await glApi.getLegalEntities()
      setEntities(data || [])
      // If no entity selected and entities exist, select first one
      if (!selectedEntityId && data && data.length > 0) {
        setSelectedEntityIdState(data[0].id)
        localStorage.setItem(STORAGE_KEY_ENTITY, data[0].id)
      }
    } catch (err) {
      console.error('Failed to fetch entities:', err)
      showError('Failed to load entities')
    }
  }, [selectedEntityId, showError])

  // Fetch books for selected entity
  const refreshBooks = useCallback(async () => {
    if (!selectedEntityId) {
      setBooks([])
      return
    }
    try {
      setIsLoading(true)
      const data = await glApi.getBooks(selectedEntityId)
      setBooks(data || [])
      // If no book selected and books exist, select first ACCRUAL book, or first book
      if (!selectedBookId && data && data.length > 0) {
        const accrualBook = data.find((b) => b.book_type === 'ACCRUAL')
        const bookToSelect = accrualBook || data[0]
        setSelectedBookIdState(bookToSelect.id)
        localStorage.setItem(STORAGE_KEY_BOOK, bookToSelect.id)
      }
    } catch (err) {
      console.error('Failed to fetch books:', err)
      showError('Failed to load books')
      setBooks([])
    } finally {
      setIsLoading(false)
    }
  }, [selectedEntityId, selectedBookId, showError])

  // Set selected entity
  const setSelectedEntityId = useCallback(
    (entityId: string | null) => {
      setSelectedEntityIdState(entityId)
      if (entityId) {
        localStorage.setItem(STORAGE_KEY_ENTITY, entityId)
      } else {
        localStorage.removeItem(STORAGE_KEY_ENTITY)
      }
      // Reset book selection when entity changes
      setSelectedBookIdState(null)
      localStorage.removeItem(STORAGE_KEY_BOOK)
      setBooks([])
    },
    []
  )

  // Set selected book
  const setSelectedBookId = useCallback((bookId: string | null) => {
    setSelectedBookIdState(bookId)
    if (bookId) {
      localStorage.setItem(STORAGE_KEY_BOOK, bookId)
    } else {
      localStorage.removeItem(STORAGE_KEY_BOOK)
    }
  }, [])

  // Load entities on mount
  useEffect(() => {
    refreshEntities()
  }, [refreshEntities])

  // Load books when entity changes
  useEffect(() => {
    if (selectedEntityId) {
      refreshBooks()
    }
  }, [selectedEntityId, refreshBooks])

  const selectedEntity = entities.find((e) => e.id === selectedEntityId) || null
  const selectedBook = books.find((b) => b.id === selectedBookId) || null

  return (
    <EntityBookContext.Provider
      value={{
        entities,
        books,
        selectedEntityId,
        selectedBookId,
        selectedEntity,
        selectedBook,
        isLoading,
        setSelectedEntityId,
        setSelectedBookId,
        refreshEntities,
        refreshBooks,
      }}
    >
      {children}
    </EntityBookContext.Provider>
  )
}
