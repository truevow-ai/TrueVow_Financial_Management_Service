'use client'

import { useEntityBook } from '@/contexts/EntityBookContext'

export function EntityBookSelector() {
  const {
    entities,
    books,
    selectedEntityId,
    selectedBookId,
    selectedEntity,
    selectedBook,
    isLoading,
    setSelectedEntityId,
    setSelectedBookId,
  } = useEntityBook()

  return (
    <div className="flex items-center gap-3">
      {/* Entity Selector */}
      <div className="flex items-center gap-2">
        <label htmlFor="entity-select" className="text-sm font-medium text-gray-700 whitespace-nowrap">
          Entity:
        </label>
        <select
          id="entity-select"
          value={selectedEntityId || ''}
          onChange={(e) => setSelectedEntityId(e.target.value || null)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          disabled={isLoading || entities.length === 0}
        >
          <option value="">Select Entity</option>
          {entities.map((entity) => (
            <option key={entity.id} value={entity.id}>
              {entity.entity_name} ({entity.entity_code})
            </option>
          ))}
        </select>
      </div>

      {/* Book Selector */}
      {selectedEntityId && (
        <div className="flex items-center gap-2">
          <label htmlFor="book-select" className="text-sm font-medium text-gray-700 whitespace-nowrap">
            Book:
          </label>
          <select
            id="book-select"
            value={selectedBookId || ''}
            onChange={(e) => setSelectedBookId(e.target.value || null)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={isLoading || books.length === 0}
          >
            <option value="">Select Book</option>
            {books.map((book) => (
              <option key={book.id} value={book.id}>
                {book.book_name} ({book.book_type})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Status Indicator */}
      {selectedEntity && selectedBook && (
        <div className="text-xs text-gray-500 whitespace-nowrap">
          {selectedEntity.entity_code} • {selectedBook.book_type}
        </div>
      )}
    </div>
  )
}
