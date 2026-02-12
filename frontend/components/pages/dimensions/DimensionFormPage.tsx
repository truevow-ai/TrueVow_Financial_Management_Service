'use client'

import { useParams, useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useDimension, useCreateDimension, useUpdateDimension } from '@/hooks/useDimensions'

const dimensionSchema = z.object({
  legal_entity_id: z.string().min(1, 'Legal entity is required'),
  dimension_name: z.string().min(1, 'Dimension name is required'),
  dimension_type: z.string().min(1, 'Dimension type is required'),
  is_active: z.boolean().default(true),
  description: z.string().optional(),
})

type DimensionFormData = z.infer<typeof dimensionSchema>

export function DimensionFormPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string | undefined
  const isEdit = !!id
  const { data: dimension, isLoading: isLoadingDimension } = useDimension(id || '')
  const createMutation = useCreateDimension()
  const updateMutation = useUpdateDimension()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DimensionFormData>({
    resolver: zodResolver(dimensionSchema),
    defaultValues: isEdit && dimension
      ? {
          legal_entity_id: dimension.legal_entity_id,
          dimension_name: dimension.dimension_name,
          dimension_type: dimension.dimension_type,
          is_active: dimension.is_active,
          description: dimension.description,
        }
      : {
          legal_entity_id: '',
          dimension_name: '',
          dimension_type: '',
          is_active: true,
          description: '',
        },
  })

  if (isEdit && isLoadingDimension) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const onSubmit = async (data: DimensionFormData) => {
    try {
      if (isEdit && id) {
        await updateMutation.mutateAsync({ id, data })
      } else {
        await createMutation.mutateAsync(data)
      }
      router.push('/dimensions')
    } catch (error) {
      console.error('Failed to save dimension:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {isEdit ? 'Edit Dimension' : 'Create Dimension'}
        </h1>
        <p className="text-gray-600 mt-1">
          {isEdit ? 'Update dimension details' : 'Add a new accounting dimension'}
        </p>
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
            <label htmlFor="dimension_name" className="block text-sm font-medium text-gray-700 mb-1">
              Dimension Name *
            </label>
            <input
              id="dimension_name"
              {...register('dimension_name')}
              className={errors.dimension_name ? 'input-error' : 'input'}
              placeholder="e.g., Department"
            />
            {errors.dimension_name && (
              <p className="mt-1 text-sm text-red-600">{errors.dimension_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="dimension_type" className="block text-sm font-medium text-gray-700 mb-1">
              Dimension Type *
            </label>
            <input
              id="dimension_type"
              {...register('dimension_type')}
              className={errors.dimension_type ? 'input-error' : 'input'}
              placeholder="e.g., department, project, cost_center"
            />
            {errors.dimension_type && (
              <p className="mt-1 text-sm text-red-600">{errors.dimension_type.message}</p>
            )}
          </div>

          <div className="md:col-span-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              {...register('description')}
              className="input"
              rows={3}
              placeholder="Optional description"
            />
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                {...register('is_active')}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">Active</span>
            </label>
          </div>
        </div>

        <div className="flex gap-2 justify-end">
          <button
            type="button"
            onClick={() => router.push('/dimensions')}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending
              ? 'Saving...'
              : isEdit
              ? 'Update Dimension'
              : 'Create Dimension'}
          </button>
        </div>
      </form>
    </div>
  )
}
