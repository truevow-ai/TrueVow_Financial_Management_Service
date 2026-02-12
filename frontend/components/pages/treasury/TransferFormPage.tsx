'use client'

import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCreateTransfer } from '@/hooks/useTreasury'
import { useBankAccounts } from '@/hooks/useTreasury'

const transferSchema = z.object({
  legal_entity_id: z.string().min(1, 'Legal entity is required'),
  from_account_id: z.string().min(1, 'From account is required'),
  to_account_id: z.string().min(1, 'To account is required'),
  transfer_date: z.string().min(1, 'Transfer date is required'),
  amount: z.number().min(0.01, 'Amount must be greater than 0'),
  currency: z.string().min(1, 'Currency is required'),
  description: z.string().optional(),
}).refine((data) => data.from_account_id !== data.to_account_id, {
  message: 'From and to accounts must be different',
  path: ['to_account_id'],
})

type TransferFormData = z.infer<typeof transferSchema>

export function TransferFormPage() {
  const router = useRouter()
  const createMutation = useCreateTransfer()
  const { data: accounts } = useBankAccounts()

  const {
    register,
    watch,
    handleSubmit,
    formState: { errors },
  } = useForm<TransferFormData>({
    resolver: zodResolver(transferSchema),
    defaultValues: {
      legal_entity_id: '',
      from_account_id: '',
      to_account_id: '',
      transfer_date: new Date().toISOString().split('T')[0],
      amount: 0,
      currency: 'USD',
      description: '',
    },
  })

  const fromAccountId = watch('from_account_id')
  const fromAccount = accounts?.find((a) => a.id === fromAccountId)
  const availableToAccounts = accounts?.filter((a) => a.id !== fromAccountId)

  const onSubmit = async (data: TransferFormData) => {
    try {
      const transfer = await createMutation.mutateAsync(data)
      router.push(`/treasury/transfers/${transfer.id}`)
    } catch (error) {
      console.error('Failed to create transfer:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create Transfer</h1>
        <p className="text-gray-600 mt-1">Transfer funds between bank accounts</p>
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
            <label htmlFor="transfer_date" className="block text-sm font-medium text-gray-700 mb-1">
              Transfer Date *
            </label>
            <input
              id="transfer_date"
              type="date"
              {...register('transfer_date')}
              className={errors.transfer_date ? 'input-error' : 'input'}
            />
            {errors.transfer_date && (
              <p className="mt-1 text-sm text-red-600">{errors.transfer_date.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="from_account_id" className="block text-sm font-medium text-gray-700 mb-1">
              From Account *
            </label>
            <select
              id="from_account_id"
              {...register('from_account_id')}
              className={errors.from_account_id ? 'input-error' : 'input'}
            >
              <option value="">Select account</option>
              {accounts?.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.account_name} ({account.account_number}) - {account.currency}
                </option>
              ))}
            </select>
            {errors.from_account_id && (
              <p className="mt-1 text-sm text-red-600">{errors.from_account_id.message}</p>
            )}
            {fromAccount && (
              <p className="mt-1 text-xs text-gray-500">
                Current balance: {fromAccount.current_balance} {fromAccount.currency}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="to_account_id" className="block text-sm font-medium text-gray-700 mb-1">
              To Account *
            </label>
            <select
              id="to_account_id"
              {...register('to_account_id')}
              className={errors.to_account_id ? 'input-error' : 'input'}
              disabled={!fromAccountId}
            >
              <option value="">Select account</option>
              {availableToAccounts?.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.account_name} ({account.account_number}) - {account.currency}
                </option>
              ))}
            </select>
            {errors.to_account_id && (
              <p className="mt-1 text-sm text-red-600">{errors.to_account_id.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-1">
              Amount *
            </label>
            <input
              id="amount"
              type="number"
              step="0.01"
              min="0"
              {...register('amount', { valueAsNumber: true })}
              className={errors.amount ? 'input-error' : 'input'}
              placeholder="0.00"
            />
            {errors.amount && <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>}
          </div>

          <div>
            <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-1">
              Currency *
            </label>
            <select
              id="currency"
              {...register('currency')}
              className={errors.currency ? 'input-error' : 'input'}
            >
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
              <option value="AED">AED</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <input
              id="description"
              {...register('description')}
              className="input"
              placeholder="Optional description"
            />
          </div>
        </div>

        <div className="flex gap-2 justify-end">
          <button type="button" onClick={() => router.push('/treasury/transfers')} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? 'Creating...' : 'Create Transfer'}
          </button>
        </div>
      </form>
    </div>
  )
}
