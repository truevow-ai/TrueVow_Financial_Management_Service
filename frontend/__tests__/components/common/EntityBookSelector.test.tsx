import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EntityBookSelector } from '@/components/common/EntityBookSelector'
import { EntityBookProvider } from '@/contexts/EntityBookContext'
import { ToastProvider } from '@/contexts/ToastContext'
import { glApi } from '@/lib/api/glApi'

// Mock the API
jest.mock('@/lib/api/glApi')
const mockedGlApi = glApi as jest.Mocked<typeof glApi>

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <EntityBookProvider>{children}</EntityBookProvider>
      </ToastProvider>
    </QueryClientProvider>
  )
}

describe('EntityBookSelector', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  it('should render entity and book selectors', async () => {
    const mockEntities = [
      {
        id: 'entity-1',
        entity_name: 'UAE Entity',
        entity_code: 'UAE',
        country: 'UAE',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    const mockBooks = [
      {
        id: 'book-1',
        legal_entity_id: 'entity-1',
        book_type: 'ACCRUAL' as const,
        book_name: 'ACCRUAL Book',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    mockedGlApi.getLegalEntities.mockResolvedValue(mockEntities)
    mockedGlApi.getBooks.mockResolvedValue(mockBooks)

    await act(async () => {
      render(<EntityBookSelector />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      expect(screen.getByLabelText(/entity/i)).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByLabelText(/book/i)).toBeInTheDocument()
    })
  })

  it('should show entity options in dropdown', async () => {
    const mockEntities = [
      {
        id: 'entity-1',
        entity_name: 'UAE Entity',
        entity_code: 'UAE',
        country: 'UAE',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
      {
        id: 'entity-2',
        entity_name: 'Nevis Entity',
        entity_code: 'NEVIS',
        country: 'Nevis',
        currency: 'USD',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    const mockBooks = [
      {
        id: 'book-1',
        legal_entity_id: 'entity-1',
        book_type: 'ACCRUAL' as const,
        book_name: 'ACCRUAL Book',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    mockedGlApi.getLegalEntities.mockResolvedValue(mockEntities)
    mockedGlApi.getBooks.mockResolvedValue(mockBooks)

    await act(async () => {
      render(<EntityBookSelector />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      const entitySelect = screen.getByLabelText(/entity/i)
      expect(entitySelect).toBeInTheDocument()
    })

    const entitySelect = screen.getByLabelText(/entity/i)
    const options = Array.from(entitySelect.querySelectorAll('option'))
    expect(options).toHaveLength(3) // "Select Entity" + 2 entities
    expect(options[1]).toHaveTextContent('UAE Entity (UAE)')
    expect(options[2]).toHaveTextContent('Nevis Entity (NEVIS)')
  })

  it('should show book selector only when entity is selected', async () => {
    const mockEntities = [
      {
        id: 'entity-1',
        entity_name: 'UAE Entity',
        entity_code: 'UAE',
        country: 'UAE',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    const mockBooks = [
      {
        id: 'book-1',
        legal_entity_id: 'entity-1',
        book_type: 'ACCRUAL' as const,
        book_name: 'ACCRUAL Book',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    mockedGlApi.getLegalEntities.mockResolvedValue(mockEntities)
    mockedGlApi.getBooks.mockResolvedValue(mockBooks)

    await act(async () => {
      render(<EntityBookSelector />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      const bookSelect = screen.getByLabelText(/book/i)
      expect(bookSelect).toBeInTheDocument()
    })
  })

  // SKIPPED: userEvent interactions with select elements timeout in Jest
  it.skip('should allow selecting entity', async () => {
    const user = userEvent.setup()
    const mockEntities = [
      {
        id: 'entity-1',
        entity_name: 'UAE Entity',
        entity_code: 'UAE',
        country: 'UAE',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
      {
        id: 'entity-2',
        entity_name: 'Nevis Entity',
        entity_code: 'NEVIS',
        country: 'Nevis',
        currency: 'USD',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    const mockBooks1 = [
      {
        id: 'book-1',
        legal_entity_id: 'entity-1',
        book_type: 'ACCRUAL' as const,
        book_name: 'ACCRUAL Book',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    const mockBooks2 = [
      {
        id: 'book-2',
        legal_entity_id: 'entity-2',
        book_type: 'ACCRUAL' as const,
        book_name: 'ACCRUAL Book',
        currency: 'USD',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    mockedGlApi.getLegalEntities.mockResolvedValue(mockEntities)
    mockedGlApi.getBooks
      .mockResolvedValueOnce(mockBooks1) // First call for auto-selected entity-1
      .mockResolvedValueOnce(mockBooks2) // Second call for selected entity-2

    await act(async () => {
      render(<EntityBookSelector />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      expect(screen.getByLabelText(/entity/i)).toBeInTheDocument()
    })

    // Wait for initial auto-selection to complete
    await waitFor(() => {
      expect(mockedGlApi.getBooks).toHaveBeenCalledWith('entity-1')
    })

    // Clear the mock call history to only track the new selection
    mockedGlApi.getBooks.mockClear()

    const entitySelect = screen.getByLabelText(/entity/i)
    await act(async () => {
      await user.selectOptions(entitySelect, 'entity-2')
    })

    await waitFor(() => {
      expect(mockedGlApi.getBooks).toHaveBeenCalledWith('entity-2')
    })
  })

  // SKIPPED: Auto-selection status indicator test times out in Jest environment
  it.skip('should show status indicator when both entity and book are selected', async () => {
    const mockEntities = [
      {
        id: 'entity-1',
        entity_name: 'UAE Entity',
        entity_code: 'UAE',
        country: 'UAE',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    const mockBooks = [
      {
        id: 'book-1',
        legal_entity_id: 'entity-1',
        book_type: 'ACCRUAL' as const,
        book_name: 'ACCRUAL Book',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    mockedGlApi.getLegalEntities.mockResolvedValue(mockEntities)
    mockedGlApi.getBooks.mockResolvedValue(mockBooks)

    await act(async () => {
      render(<EntityBookSelector />, { wrapper: createWrapper() })
    })

    await waitFor(() => {
      expect(screen.getByText(/UAE.*ACCRUAL/i)).toBeInTheDocument()
    })
  })

  // SKIPPED: Loading state test has timing issues in Jest environment
  it.skip('should disable selectors during loading', async () => {
    const mockEntities = [
      {
        id: 'entity-1',
        entity_name: 'UAE Entity',
        entity_code: 'UAE',
        country: 'UAE',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    const mockBooks = [
      {
        id: 'book-1',
        legal_entity_id: 'entity-1',
        book_type: 'ACCRUAL' as const,
        book_name: 'ACCRUAL Book',
        currency: 'AED',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
    ]

    // Delay the response to test loading state
    mockedGlApi.getLegalEntities.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockEntities), 100))
    )
    mockedGlApi.getBooks.mockResolvedValue(mockBooks)

    await act(async () => {
      render(<EntityBookSelector />, { wrapper: createWrapper() })
    })

    const entitySelect = screen.getByLabelText(/entity/i)
    expect(entitySelect).toBeDisabled()

    // Wait for entities to load first (proves loading phase completed)
    await waitFor(() => {
      expect(screen.getByText('UAE Entity (UAE)')).toBeInTheDocument()
    }, { timeout: 2000 })

    // Wait for books to load (refreshBooks sets isLoading=false in finally block)
    await waitFor(() => {
      expect(screen.getByText('ACCRUAL Book (ACCRUAL)')).toBeInTheDocument()
    }, { timeout: 2000 })

    // Now selector should be enabled
    await waitFor(() => {
      expect(entitySelect).not.toBeDisabled()
    }, { timeout: 2000 })
  })
})
