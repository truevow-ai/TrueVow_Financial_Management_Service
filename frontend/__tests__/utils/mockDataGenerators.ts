/**
 * Comprehensive Mock Data Generators for Financial Reports
 * Covers all edge cases, use cases, and accounting scenarios
 */

import {
  TrialBalanceResponse,
  PLBalanceSheetResponse,
  CashFlowResponse,
  GLDetailResponse,
  TrialBalanceRow,
  GLDetailRow,
} from '@/lib/api/reportingApi'

// Accounting precision tolerance: 0.002% (0.00002)
export const ACCOUNTING_PRECISION = 0.00002

/**
 * Check if two numbers are within accounting precision tolerance
 */
export function isWithinPrecision(a: number, b: number): boolean {
  if (a === 0 && b === 0) return true
  const max = Math.max(Math.abs(a), Math.abs(b))
  const diff = Math.abs(a - b)
  return diff / max <= ACCOUNTING_PRECISION
}

// Self-validation tests for mock data generators
describe('Mock Data Generator Utilities', () => {
  test('isWithinPrecision returns true for identical values', () => {
    expect(isWithinPrecision(100, 100)).toBe(true)
    expect(isWithinPrecision(0, 0)).toBe(true)
  })

  test('isWithinPrecision returns true for values within tolerance', () => {
    expect(isWithinPrecision(100000, 100001)).toBe(true)
  })

  test('isWithinPrecision returns false for values outside tolerance', () => {
    expect(isWithinPrecision(100, 200)).toBe(false)
  })
})

/**
 * Generate mock Trial Balance data with various scenarios
 */
export function generateTrialBalanceData(scenario: string = 'balanced'): TrialBalanceResponse {
  const baseDate = new Date().toISOString().split('T')[0]
  
  const scenarios: Record<string, TrialBalanceRow[]> = {
    // Perfectly balanced
    balanced: [
      { account_code: '1000', account_name: 'Cash', debit_balance: 100000.00, credit_balance: 0 },
      { account_code: '2000', account_name: 'Accounts Receivable', debit_balance: 50000.00, credit_balance: 0 },
      { account_code: '3000', account_name: 'Inventory', debit_balance: 75000.00, credit_balance: 0 },
      { account_code: '4000', account_name: 'Accounts Payable', debit_balance: 0, credit_balance: 45000.00 },
      { account_code: '5000', account_name: 'Revenue', debit_balance: 0, credit_balance: 150000.00 },
      { account_code: '6000', account_name: 'Expenses', debit_balance: 30000.00, credit_balance: 0 },
    ],
    
    // Balanced with rounding (within 0.002% tolerance)
    // Total debits: 255000.007, so credits must also be 255000.007
    balancedWithRounding: [
      { account_code: '1000', account_name: 'Cash', debit_balance: 100000.001, credit_balance: 0 },
      { account_code: '2000', account_name: 'Accounts Receivable', debit_balance: 50000.002, credit_balance: 0 },
      { account_code: '3000', account_name: 'Inventory', debit_balance: 75000.003, credit_balance: 0 },
      { account_code: '4000', account_name: 'Accounts Payable', debit_balance: 0, credit_balance: 45000.004 },
      { account_code: '5000', account_name: 'Revenue', debit_balance: 0, credit_balance: 210000.003 },
      { account_code: '6000', account_name: 'Expenses', debit_balance: 30000.001, credit_balance: 0 },
    ],
    
    // Unbalanced (should show error)
    unbalanced: [
      { account_code: '1000', account_name: 'Cash', debit_balance: 100000.00, credit_balance: 0 },
      { account_code: '2000', account_name: 'Accounts Receivable', debit_balance: 50000.00, credit_balance: 0 },
      { account_code: '4000', account_name: 'Accounts Payable', debit_balance: 0, credit_balance: 45000.00 },
      { account_code: '5000', account_name: 'Revenue', debit_balance: 0, credit_balance: 150000.00 },
    ],
    
    // Empty data
    empty: [],
    
    // Single account
    singleAccount: [
      { account_code: '1000', account_name: 'Cash', debit_balance: 100000.00, credit_balance: 0 },
    ],
    
    // Very large numbers
    largeNumbers: [
      { account_code: '1000', account_name: 'Cash', debit_balance: 999999999999.99, credit_balance: 0 },
      { account_code: '2000', account_name: 'Accounts Receivable', debit_balance: 500000000000.00, credit_balance: 0 },
      { account_code: '4000', account_name: 'Accounts Payable', debit_balance: 0, credit_balance: 750000000000.00 },
      { account_code: '5000', account_name: 'Revenue', debit_balance: 0, credit_balance: 999999999999.99 },
    ],
    
    // Very small numbers (cents)
    smallNumbers: [
      { account_code: '1000', account_name: 'Cash', debit_balance: 0.01, credit_balance: 0 },
      { account_code: '2000', account_name: 'Accounts Receivable', debit_balance: 0.02, credit_balance: 0 },
      { account_code: '4000', account_name: 'Accounts Payable', debit_balance: 0, credit_balance: 0.01 },
      { account_code: '5000', account_name: 'Revenue', debit_balance: 0, credit_balance: 0.02 },
    ],
    
    // Zero balances
    zeroBalances: [
      { account_code: '1000', account_name: 'Cash', debit_balance: 0, credit_balance: 0 },
      { account_code: '2000', account_name: 'Accounts Receivable', debit_balance: 0, credit_balance: 0 },
      { account_code: '3000', account_name: 'Inventory', debit_balance: 0, credit_balance: 0 },
    ],
    
    // Many accounts (for pagination/chart testing)
    manyAccounts: Array.from({ length: 50 }, (_, i) => ({
      account_code: `${1000 + i}`,
      account_name: `Account ${i + 1}`,
      debit_balance: (i + 1) * 1000.00,
      credit_balance: i % 2 === 0 ? (i + 1) * 500.00 : 0,
    })),
  }
  
  const rows = scenarios[scenario] || scenarios.balanced
  
  return {
    legal_entity_id: 'entity-1',
    book_id: 'book-1',
    period_id: 'period-1',
    as_of_date: baseDate,
    rows,
  }
}

/**
 * Generate mock P&L / Balance Sheet data
 */
export function generatePLBalanceSheetData(scenario: string = 'normal'): PLBalanceSheetResponse {
  const baseDate = new Date().toISOString().split('T')[0]
  
  const scenarios: Record<string, PLBalanceSheetResponse> = {
    normal: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      revenue: 150000.00,
      expenses: 120000.00,
      net_income: 30000.00,
      assets: 500000.00,
      liabilities: 200000.00,
      equity: 300000.00,
    },
    
    loss: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      revenue: 100000.00,
      expenses: 150000.00,
      net_income: -50000.00,
      assets: 400000.00,
      liabilities: 250000.00,
      equity: 150000.00,
    },
    
    balanced: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      revenue: 200000.00,
      expenses: 200000.00,
      net_income: 0.00,
      assets: 500000.00,
      liabilities: 200000.00,
      equity: 300000.00,
    },
    
    zero: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      revenue: 0,
      expenses: 0,
      net_income: 0,
      assets: 0,
      liabilities: 0,
      equity: 0,
    },
    
    largeNumbers: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      revenue: 999999999999.99,
      expenses: 750000000000.00,
      net_income: 249999999999.99,
      assets: 5000000000000.00,
      liabilities: 2000000000000.00,
      equity: 3000000000000.00,
    },
    
    precisionTest: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      revenue: 150000.001,
      expenses: 120000.002,
      net_income: 30000.001,
      assets: 500000.003,
      liabilities: 200000.004,
      equity: 300000.005,
    },
  }
  
  return scenarios[scenario] || scenarios.normal
}

/**
 * Generate mock Cash Flow data
 */
export function generateCashFlowData(scenario: string = 'normal'): CashFlowResponse {
  const baseDate = new Date().toISOString().split('T')[0]
  
  const scenarios: Record<string, CashFlowResponse> = {
    normal: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      operating_activities: 50000.00,
      investing_activities: -20000.00,
      financing_activities: 10000.00,
      net_change: 40000.00,
      beginning_cash: 100000.00,
      ending_cash: 140000.00,
    },
    
    negative: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      operating_activities: -30000.00,
      investing_activities: -50000.00,
      financing_activities: -10000.00,
      net_change: -90000.00,
      beginning_cash: 200000.00,
      ending_cash: 110000.00,
    },
    
    zero: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      operating_activities: 0,
      investing_activities: 0,
      financing_activities: 0,
      net_change: 0,
      beginning_cash: 100000.00,
      ending_cash: 100000.00,
    },
    
    precisionTest: {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      operating_activities: 50000.001,
      investing_activities: -20000.002,
      financing_activities: 10000.003,
      net_change: 40000.002,
      beginning_cash: 100000.004,
      ending_cash: 140000.006,
    },
  }
  
  return scenarios[scenario] || scenarios.normal
}

/**
 * Generate mock GL Detail data
 */
export function generateGLDetailData(scenario: string = 'normal', count: number = 10): GLDetailResponse {
  const baseDate = new Date().toISOString().split('T')[0]
  
  const rows: GLDetailRow[] = []
  
  if (scenario === 'empty') {
    return {
      legal_entity_id: 'entity-1',
      book_id: 'book-1',
      period_id: 'period-1',
      as_of_date: baseDate,
      rows: [],
      total_debits: 0,
      total_credits: 0,
    }
  }
  
  let totalDebits = 0
  let totalCredits = 0
  
  for (let i = 0; i < count; i++) {
    const date = new Date(baseDate)
    date.setDate(date.getDate() - i)
    
    const debitAmount = scenario === 'allDebits' ? 1000.00 : scenario === 'allCredits' ? 0 : (i % 2 === 0 ? 1000.00 : 0)
    const creditAmount = scenario === 'allCredits' ? 1000.00 : scenario === 'allDebits' ? 0 : (i % 2 === 1 ? 1000.00 : 0)
    
    totalDebits += debitAmount
    totalCredits += creditAmount
    
    rows.push({
      entry_id: `entry-${i + 1}`,
      entry_number: `JE-${String(i + 1).padStart(4, '0')}`,
      entry_date: date.toISOString(),
      line_number: i + 1,
      account_code: `${1000 + (i % 10)}`,
      account_name: `Account ${1000 + (i % 10)}`,
      description: `Transaction ${i + 1}${scenario === 'withSearch' ? ' special keyword' : ''}`,
      debit_amount: debitAmount,
      credit_amount: creditAmount,
      balance: (i + 1) * 100.00,
      dimension_values: i % 3 === 0 ? { department: 'Sales', project: 'Project A' } : undefined,
    })
  }
  
  // Add precision test rows
  if (scenario === 'precisionTest') {
    rows.push({
      entry_id: 'entry-precision',
      entry_number: 'JE-PREC',
      entry_date: baseDate,
      line_number: count + 1,
      account_code: '9999',
      account_name: 'Precision Test',
      description: 'Precision test transaction',
      debit_amount: 100000.001,
      credit_amount: 100000.002,
      balance: -0.001,
      dimension_values: undefined,
    })
    totalDebits += 100000.001
    totalCredits += 100000.002
  }
  
  return {
    legal_entity_id: 'entity-1',
    book_id: 'book-1',
    period_id: 'period-1',
    as_of_date: baseDate,
    rows,
    total_debits: totalDebits,
    total_credits: totalCredits,
  }
}

/**
 * Calculate expected totals for validation
 */
export function calculateTrialBalanceTotals(rows: TrialBalanceRow[]): {
  totalDebits: number
  totalCredits: number
  balance: number
  isBalanced: boolean
} {
  const totalDebits = rows.reduce((sum, row) => sum + row.debit_balance, 0)
  const totalCredits = rows.reduce((sum, row) => sum + row.credit_balance, 0)
  const balance = totalDebits - totalCredits
  const isBalanced = isWithinPrecision(totalDebits, totalCredits)
  
  return { totalDebits, totalCredits, balance, isBalanced }
}

/**
 * Calculate expected cash flow validation
 */
export function calculateCashFlowValidation(data: CashFlowResponse): {
  calculatedNetChange: number
  calculatedEndingCash: number
  isNetChangeValid: boolean
  isEndingCashValid: boolean
} {
  const calculatedNetChange = data.operating_activities + data.investing_activities + data.financing_activities
  const calculatedEndingCash = data.beginning_cash + calculatedNetChange
  
  const isNetChangeValid = isWithinPrecision(calculatedNetChange, data.net_change)
  const isEndingCashValid = isWithinPrecision(calculatedEndingCash, data.ending_cash)
  
  return {
    calculatedNetChange,
    calculatedEndingCash,
    isNetChangeValid,
    isEndingCashValid,
  }
}

/**
 * Calculate expected balance sheet validation
 */
export function calculateBalanceSheetValidation(data: PLBalanceSheetResponse): {
  calculatedEquity: number
  calculatedBalance: number
  isEquityValid: boolean
  isBalanceValid: boolean
} {
  // Equity should equal Assets - Liabilities
  const calculatedEquity = data.assets - data.liabilities
  const calculatedBalance = data.assets - data.liabilities - data.equity
  
  const isEquityValid = isWithinPrecision(calculatedEquity, data.equity)
  const isBalanceValid = Math.abs(calculatedBalance) < 0.01 || isWithinPrecision(calculatedBalance, 0)
  
  return {
    calculatedEquity,
    calculatedBalance,
    isEquityValid,
    isBalanceValid,
  }
}

/**
 * Generate mock GLAccount data with various scenarios
 */
export function generateGLAccountData(scenario: string = 'normal'): any[] {
  const baseDate = new Date().toISOString()
  
  const scenarios: Record<string, any[]> = {
    normal: [
      {
        id: 'account-1',
        account_code: '1000',
        account_name: 'Cash',
        account_type: 'asset',
        is_active: true,
        description: 'Cash and cash equivalents',
        created_at: baseDate,
        updated_at: baseDate,
      },
      {
        id: 'account-2',
        account_code: '2000',
        account_name: 'Accounts Receivable',
        account_type: 'asset',
        is_active: true,
        description: 'Amounts owed by customers',
        created_at: baseDate,
        updated_at: baseDate,
      },
      {
        id: 'account-3',
        account_code: '4000',
        account_name: 'Accounts Payable',
        account_type: 'liability',
        is_active: true,
        description: 'Amounts owed to vendors',
        created_at: baseDate,
        updated_at: baseDate,
      },
      {
        id: 'account-4',
        account_code: '5000',
        account_name: 'Revenue',
        account_type: 'revenue',
        is_active: true,
        description: 'Sales revenue',
        created_at: baseDate,
        updated_at: baseDate,
      },
      {
        id: 'account-5',
        account_code: '6000',
        account_name: 'Expenses',
        account_type: 'expense',
        is_active: true,
        description: 'Operating expenses',
        created_at: baseDate,
        updated_at: baseDate,
      },
    ],
    empty: [],
    single: [
      {
        id: 'account-1',
        account_code: '1000',
        account_name: 'Cash',
        account_type: 'asset',
        is_active: true,
        description: 'Cash and cash equivalents',
        created_at: baseDate,
        updated_at: baseDate,
      },
    ],
    large: Array.from({ length: 100 }, (_, i) => ({
      id: `account-${i + 1}`,
      account_code: `${1000 + i}`,
      account_name: `Account ${i + 1}`,
      account_type: ['asset', 'liability', 'equity', 'revenue', 'expense'][i % 5],
      is_active: i % 10 !== 0,
      description: `Description for account ${i + 1}`,
      created_at: baseDate,
      updated_at: baseDate,
    })),
    inactive: [
      {
        id: 'account-1',
        account_code: '1000',
        account_name: 'Cash',
        account_type: 'asset',
        is_active: false,
        description: 'Inactive account',
        created_at: baseDate,
        updated_at: baseDate,
      },
    ],
  }
  
  return scenarios[scenario] || scenarios.normal
}

/**
 * Generate mock JournalEntry data with various scenarios
 */
export function generateJournalEntryData(scenario: string = 'normal'): any {
  const baseDate = new Date().toISOString()
  
  const scenarios: Record<string, any> = {
    normal: {
      items: [
        {
          id: 'entry-1',
          entry_number: 'JE-001',
          entry_date: baseDate,
          description: 'Monthly accrual entry',
          status: 'posted',
          lines: [
            { id: 'line-1', debit_amount: 1000, credit_amount: 0 },
            { id: 'line-2', debit_amount: 0, credit_amount: 1000 },
          ],
          created_at: baseDate,
          updated_at: baseDate,
        },
        {
          id: 'entry-2',
          entry_number: 'JE-002',
          entry_date: baseDate,
          description: 'Adjustment entry',
          status: 'draft',
          lines: [
            { id: 'line-3', debit_amount: 500, credit_amount: 0 },
            { id: 'line-4', debit_amount: 0, credit_amount: 500 },
          ],
          created_at: baseDate,
          updated_at: baseDate,
        },
        {
          id: 'entry-3',
          entry_number: 'JE-003',
          entry_date: baseDate,
          description: 'Reversal entry',
          status: 'reversed',
          lines: [],
          created_at: baseDate,
          updated_at: baseDate,
        },
      ],
      total: 3,
      page: 1,
      page_size: 10,
    },
    empty: {
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    },
    single: {
      items: [
        {
          id: 'entry-1',
          entry_number: 'JE-001',
          entry_date: baseDate,
          description: 'Single entry',
          status: 'posted',
          lines: [],
          created_at: baseDate,
          updated_at: baseDate,
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
    },
    large: {
      items: Array.from({ length: 50 }, (_, i) => ({
        id: `entry-${i + 1}`,
        entry_number: `JE-${String(i + 1).padStart(3, '0')}`,
        entry_date: baseDate,
        description: `Entry ${i + 1}`,
        status: ['draft', 'posted', 'reversed'][i % 3],
        lines: [],
        created_at: baseDate,
        updated_at: baseDate,
      })),
      total: 50,
      page: 1,
      page_size: 10,
    },
  }
  
  return scenarios[scenario] || scenarios.normal
}
