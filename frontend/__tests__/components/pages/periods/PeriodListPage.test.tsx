/**
 * Render + interaction tests for the period-close UX.
 */
import React from 'react'
import { render, screen, act, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PeriodListPage } from '@/components/pages/periods/PeriodListPage'

jest.mock('@/hooks/usePeriods', () => ({
  usePeriods: jest.fn(),
  useClosePeriod: jest.fn(),
  useLockPeriod: jest.fn(),
}))
jest.mock('@/contexts/EntityBookContext', () => ({ useEntityBook: jest.fn() }))

const { usePeriods, useClosePeriod, useLockPeriod } = require('@/hooks/usePeriods')
const { useEntityBook } = require('@/contexts/EntityBookContext')

const closeMutate = jest.fn()
const lockMutate = jest.fn()

const periods = [
  { id: 'p-open', period_name: '2026-01', start_date: '2026-01-01', end_date: '2026-01-31', status: 'open', legal_entity_id: 'e1', book_id: 'b1', created_at: '', updated_at: '' },
  { id: 'p-closed', period_name: '2025-12', start_date: '2025-12-01', end_date: '2025-12-31', status: 'closed', legal_entity_id: 'e1', book_id: 'b1', created_at: '', updated_at: '' },
  { id: 'p-locked', period_name: '2025-11', start_date: '2025-11-01', end_date: '2025-11-30', status: 'locked', legal_entity_id: 'e1', book_id: 'b1', created_at: '', updated_at: '' },
]

describe('PeriodListPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useEntityBook as jest.Mock).mockReturnValue({ selectedEntityId: 'e1', selectedBookId: 'b1' })
    ;(usePeriods as jest.Mock).mockReturnValue({ data: periods, isLoading: false, error: null })
    ;(useClosePeriod as jest.Mock).mockReturnValue({ mutate: closeMutate, isPending: false, variables: undefined })
    ;(useLockPeriod as jest.Mock).mockReturnValue({ mutate: lockMutate, isPending: false, variables: undefined })
    global.confirm = jest.fn(() => true)
  })

  afterEach(() => cleanup())

  it('renders periods with status-appropriate actions', async () => {
    await act(async () => {
      render(<PeriodListPage />)
    })
    expect(screen.getByText('2026-01')).toBeInTheDocument()
    expect(screen.getByText('Close')).toBeInTheDocument()
    expect(screen.getByText('Lock')).toBeInTheDocument()
  })

  it('closes an open period after confirmation', async () => {
    const user = userEvent.setup()
    await act(async () => {
      render(<PeriodListPage />)
    })
    await act(async () => {
      await user.click(screen.getByText('Close'))
    })
    expect(global.confirm).toHaveBeenCalled()
    expect(closeMutate).toHaveBeenCalledWith('p-open')
  })

  it('prompts to select entity/book when none chosen', async () => {
    ;(useEntityBook as jest.Mock).mockReturnValue({ selectedEntityId: '', selectedBookId: '' })
    await act(async () => {
      render(<PeriodListPage />)
    })
    expect(screen.getByText('Select an entity and book to view periods.')).toBeInTheDocument()
  })
})
