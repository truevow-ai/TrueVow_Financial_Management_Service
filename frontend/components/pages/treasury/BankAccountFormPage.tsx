'use client'

import { useParams, useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useBankAccount, useCreateBankAccount, useUpdateBankAccount } from '@/hooks/useTreasury'

const bankAccountSchema = z.object({
  legal_entity_id: z.string().min(1, 'Legal entity is required'),
  account_name: z.string().min(1, 'Account name is required'),
  account_number: z.string().min(1, 'Account number is required'),
  bank_name: z.string().min(1, 'Bank name is required'),
  bank_code: z.string().optional(),
  currency: z.string().min(1, 'Currency is required'),
  account_type: z.enum(['checking', 'savings', 'money_market', 'other']),
  is_active: z.boolean().default(true),
  opening_balance: z.number().default(0),
})

type BankAccountFormData = z.infer<typeof bankAccountSchema>

export function BankAccountFormPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string | undefined
  const isEdit = !!id
  const { data: account, isLoading: isLoadingAccount } = useBankAccount(id || '')
  const createMutation = useCreateBankAccount()
  const updateMutation = useUpdateBankAccount()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BankAccountFormData>({
    resolver: zodResolver(bankAccountSchema),
    defaultValues: isEdit && account
      ? {
          legal_entity_id: account.legal_entity_id,
          account_name: account.account_name,
          account_number: account.account_number,
          bank_name: account.bank_name,
          bank_code: account.bank_code || '',
          currency: account.currency,
          account_type: account.account_type,
          is_active: account.is_active,
          opening_balance: account.opening_balance,
        }
      : {
          legal_entity_id: '',
          account_name: '',
          account_number: '',
          bank_name: '',
          bank_code: '',
          currency: 'USD',
          account_type: 'checking',
          is_active: true,
          opening_balance: 0,
        },
  })

  if (isEdit && isLoadingAccount) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const onSubmit = async (data: BankAccountFormData) => {
    try {
      if (isEdit && id) {
        await updateMutation.mutateAsync({ id, data })
      } else {
        await createMutation.mutateAsync(data)
      }
      router.push('/treasury/bank-accounts')
    } catch (error) {
      console.error('Failed to save bank account:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {isEdit ? 'Edit Bank Account' : 'Add Bank Account'}
        </h1>
        <p className="text-gray-600 mt-1">
          {isEdit ? 'Update bank account information' : 'Add a new bank account to the system'}
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
            <label htmlFor="account_name" className="block text-sm font-medium text-gray-700 mb-1">
              Account Name *
            </label>
            <input
              id="account_name"
              {...register('account_name')}
              className={errors.account_name ? 'input-error' : 'input'}
              placeholder="e.g., Main Operating Account"
            />
            {errors.account_name && (
              <p className="mt-1 text-sm text-red-600">{errors.account_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="bank_name" className="block text-sm font-medium text-gray-700 mb-1">
              Bank Name *
            </label>
            <input
              id="bank_name"
              {...register('bank_name')}
              className={errors.bank_name ? 'input-error' : 'input'}
              placeholder="e.g., Chase Bank"
            />
            {errors.bank_name && (
              <p className="mt-1 text-sm text-red-600">{errors.bank_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="account_number" className="block text-sm font-medium text-gray-700 mb-1">
              Account Number *
            </label>
            <input
              id="account_number"
              {...register('account_number')}
              className={errors.account_number ? 'input-error' : 'input'}
              placeholder="Account number"
            />
            {errors.account_number && (
              <p className="mt-1 text-sm text-red-600">{errors.account_number.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="bank_code" className="block text-sm font-medium text-gray-700 mb-1">
              Bank Code
            </label>
            <input
              id="bank_code"
              {...register('bank_code')}
              className="input"
              placeholder="Optional bank code"
            />
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

          <div>
            <label htmlFor="account_type" className="block text-sm font-medium text-gray-700 mb-1">
              Account Type *
            </label>
            <select
              id="account_type"
              {...register('account_type')}
              className={errors.account_type ? 'input-error' : 'input'}
            >
              <option value="checking">Checking</option>
              <option value="savings">Savings</option>
              <option value="money_market">Money Market</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label htmlFor="opening_balance" className="block text-sm font-medium text-gray-700 mb-1">
              Opening Balance
            </label>
            <input
              id="opening_balance"
              type="number"
              step="0.01"
              {...register('opening_balance', { valueAsNumber: true })}
              className="input"
              placeholder="0.00"
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
          <button type="button" onClick={() => router.push('/treasury/bank-accounts')} className="btn-secondary">
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
              ? 'Update Account'
              : 'Add Account'}
          </button>
        </div>
      </form>
    </div>
  )
}
