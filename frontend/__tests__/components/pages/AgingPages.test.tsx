/**
 * Render tests for AR and AP aging pages (drill-down off the GL reports).
 * Exercises the real query path against mocked ar/ap APIs.
 */
import React from 'react'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ARAgingPage } from '@/components/pages/ar/ARAgingPage'
import { APAgingPage } from '@/components/pages/ap/APAgingPage'
import { arApi } from '@/lib/api/arApi'
import { apApi } from '@/lib/api/apApi'

jest.mock('@/lib/api/arApi', () => ({ arApi: { getARAging: jest.fn() } }))
jest.mock('@/lib/api/apApi', () => ({ apApi: { getAPAging: jest.fn() } }))
jest.mock('@/contexts/EntityBookContext', () => ({ useEntityBook: jest.fn() }))

const { useEntityBook } = require('@/contexts/EntityBookContext')
const mockedAr = arApi as jest.Mocked<typeof arApi>
const mockedAp = apApi as jest.Mocked<typeof apApi>

const createWrapper = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('Aging pages', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useEntityBook as jest.Mock).mockReturnValue({ selectedEntityId: 'entity-1' })
    mockedAr.getARAging.mockResolvedValue([
      {
        customer_id: 'c1',
        customer_name: 'Acme Corp',
        current: 100,
        days_30: 50,
        days_60: 0,
        days_90: 0,
        days_90_plus: 25,
        total: 175,
      },
    ])
    mockedAp.getAPAging.mockResolvedValue([
      {
        vendor_id: 'v1',
        vendor_name: 'Globex',
        current: 200,
        days_30: 0,
        days_60: 0,
        days_90: 0,
        days_90_plus: 0,
        total: 200,
      },
    ])
  })

  afterEach(() => cleanup())

  it('AR aging renders customer rows', async () => {
    await act(async () => {
      render(<ARAgingPage />, { wrapper: createWrapper() })
    })
    await waitFor(() => expect(screen.getByText('Acme Corp')).toBeInTheDocument())
    expect(screen.getByText('Total Outstanding')).toBeInTheDocument()
    expect(mockedAr.getARAging).toHaveBeenCalledWith(
      expect.objectContaining({ legal_entity_id: 'entity-1' })
    )
  })

  it('AR aging prompts when no entity selected', async () => {
    ;(useEntityBook as jest.Mock).mockReturnValue({ selectedEntityId: '' })
    await act(async () => {
      render(<ARAgingPage />, { wrapper: createWrapper() })
    })
    expect(screen.getByText('Select an entity to view AR aging.')).toBeInTheDocument()
  })

  it('AP aging renders vendor rows', async () => {
    await act(async () => {
      render(<APAgingPage />, { wrapper: createWrapper() })
    })
    await waitFor(() => expect(screen.getByText('Globex')).toBeInTheDocument())
    expect(screen.getByText('Vendors')).toBeInTheDocument()
  })
})
