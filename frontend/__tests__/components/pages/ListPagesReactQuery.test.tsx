/**
 * Render tests for list pages migrated from useState/useEffect to React Query.
 * Confirms both response shapes ({items} and plain array) render via useQuery.
 */
import React from 'react'
import { render, screen, waitFor, act, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ARInvoiceListPage } from '@/components/pages/ar/ARInvoiceListPage'
import { APVendorListPage } from '@/components/pages/ap/APVendorListPage'
import { arApi } from '@/lib/api/arApi'
import { apApi } from '@/lib/api/apApi'

jest.mock('@/lib/api/arApi', () => ({ arApi: { getARInvoices: jest.fn() } }))
jest.mock('@/lib/api/apApi', () => ({ apApi: { getAPVendors: jest.fn() } }))

const mockedAr = arApi as jest.Mocked<typeof arApi>
const mockedAp = apApi as jest.Mocked<typeof apApi>

const createWrapper = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('Migrated list pages (React Query)', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedAr.getARInvoices.mockResolvedValue({
      items: [
        {
          id: 'inv-1',
          invoice_number: 'INV-1',
          legal_entity_id: 'e1',
          customer_id: 'c1',
          customer_name: 'Acme Corp',
          invoice_date: '2026-01-01',
          due_date: '2026-01-31',
          total_amount: 100,
          paid_amount: 0,
          outstanding_amount: 100,
          status: 'posted',
          currency: 'USD',
          lines: [],
          created_at: '',
          updated_at: '',
        },
      ],
      total: 1,
    } as any)
    mockedAp.getAPVendors.mockResolvedValue([
      {
        id: 'v1',
        legal_entity_id: 'e1',
        vendor_code: 'V1',
        vendor_name: 'Globex',
        is_active: true,
        created_at: '',
        updated_at: '',
      },
    ] as any)
  })

  afterEach(() => cleanup())

  it('AR invoices list renders via useQuery (items shape)', async () => {
    await act(async () => {
      render(<ARInvoiceListPage />, { wrapper: createWrapper() })
    })
    await waitFor(() => expect(screen.getByText('INV-1')).toBeInTheDocument())
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('AP vendors list renders via useQuery (array shape)', async () => {
    await act(async () => {
      render(<APVendorListPage />, { wrapper: createWrapper() })
    })
    await waitFor(() => expect(screen.getByText('Globex')).toBeInTheDocument())
    expect(screen.getByText('V1')).toBeInTheDocument()
  })
})
