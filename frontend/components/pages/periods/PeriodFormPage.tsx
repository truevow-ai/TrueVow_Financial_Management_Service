'use client'

import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCreatePeriod } from '@/hooks/usePeriods'

const periodSchema = z.object({
  legal_entity_id: z.string().min(1, 'Legal entity is required'),
  book_id: z.string().min(1, 'Book is required'),
  period_name: z.string().min(1, 'Period name is required'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
}).refine(
  (data) => new Date(data.end_date) >= new Date(data.start_date),
  { message: 'End date must be after start date', path: ['end_date'] }
)

type PeriodFormData = z.infer<typeof periodSchema>

export function PeriodFormPage() {
  const router = useRouter()
  const createMutation = useCreatePeriod()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PeriodFormData>({
    resolver: zodResolver(periodSchema),
    defaultValues: {
      legal_entity_id: '',
      book_id: '',
      period_name: '',
      start_date: '',
      end_date: '',
    },
  })

  const onSubmit = async (data: PeriodFormData) => {
    try {
      await createMutation.mutateAsync(data)
      router.push('/periods')
    } catch (error) {
      console.error('Failed to create period:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create Accounting Period</h1>
        <p className="text-gray-600 mt-1">Create a new accounting period</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="legal_entity_id" className="block text-sm font-medium text-gray-700 mb-1">
              Legal Entity *
            </label>
            <input
              id="legal_entity_id"
              {...register('legal_entity_id')}
              className={errors.legal_entity_id ? 'input-error' : 'input'}
              placeholder="Enter legal entity ID"
            />
            {errors.legal_entity_id && (
              <p className="mt-1 text-sm text-red-600">{errors.legal_entity_id.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="book_id" className="block text-sm font-medium text-gray-700 mb-1">
              Book *
            </label>
            <input
              id="book_id"
              {...register('book_id')}
              className={errors.book_id ? 'input-error' : 'input'}
              placeholder="Enter book ID"
            />
            {errors.book_id && (
              <p className="mt-1 text-sm text-red-600">{errors.book_id.message}</p>
            )}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="period_name" className="block text-sm font-medium text-gray-700 mb-1">
              Period Name *
            </label>
            <input
              id="period_name"
              {...register('period_name')}
              className={errors.period_name ? 'input-error' : 'input'}
              placeholder="e.g., January 2025"
            />
            {errors.period_name && (
              <p className="mt-1 text-sm text-red-600">{errors.period_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-1">
              Start Date *
            </label>
            <input
              id="start_date"
              type="date"
              {...register('start_date')}
              className={errors.start_date ? 'input-error' : 'input'}
            />
            {errors.start_date && (
              <p className="mt-1 text-sm text-red-600">{errors.start_date.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 mb-1">
              End Date *
            </label>
            <input
              id="end_date"
              type="date"
              {...register('end_date')}
              className={errors.end_date ? 'input-error' : 'input'}
            />
            {errors.end_date && (
              <p className="mt-1 text-sm text-red-600">{errors.end_date.message}</p>
            )}
          </div>
        </div>

        <div className="flex gap-2 justify-end">
          <button
            type="button"
            onClick={() => router.push('/periods')}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create Period'}
          </button>
        </div>
      </form>
    </div>
  )
}
