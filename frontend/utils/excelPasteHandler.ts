/**
 * Excel Paste Handler
 * Handles pasting multi-row, multi-column data from Excel/CSV into grid
 */

export interface PasteResult {
  rows: string[][]
  rowCount: number
  columnCount: number
}

/**
 * Parse pasted clipboard data into rows and columns
 */
export function parsePastedData(data: string): PasteResult {
  const rows: string[][] = []
  const lines = data.split(/\r?\n/)
  
  for (const line of lines) {
    if (!line.trim()) continue // Skip empty lines
    
    // Handle tab-separated (Excel default) and comma-separated
    const cells = line.includes('\t') 
      ? line.split('\t')
      : line.split(',').map(cell => cell.trim())
    
    // Clean up cells (remove quotes if present)
    const cleanedCells = cells.map(cell => {
      // Remove surrounding quotes if present
      if ((cell.startsWith('"') && cell.endsWith('"')) ||
          (cell.startsWith("'") && cell.endsWith("'"))) {
        return cell.slice(1, -1)
      }
      return cell.trim()
    })
    
    rows.push(cleanedCells)
  }
  
  return {
    rows,
    rowCount: rows.length,
    columnCount: rows.length > 0 ? rows[0].length : 0
  }
}

/**
 * Map pasted data to grid cells based on current column order
 */
export function mapPastedDataToGrid(
  pastedData: PasteResult,
  columnOrder: string[],
  startRowIndex: number,
  startColIndex: number
): Map<string, { row: number; col: number; value: string }> {
  const mappedData = new Map<string, { row: number; col: number; value: string }>()
  
  pastedData.rows.forEach((row, rowOffset) => {
    row.forEach((cell, colOffset) => {
      const targetRow = startRowIndex + rowOffset
      const targetColIndex = startColIndex + colOffset
      
      if (targetColIndex < columnOrder.length) {
        const columnKey = columnOrder[targetColIndex]
        const cellKey = `${targetRow}-${columnKey}`
        
        mappedData.set(cellKey, {
          row: targetRow,
          col: targetColIndex,
          value: cell
        })
      }
    })
  })
  
  return mappedData
}

/**
 * Handle paste event and return parsed data
 */
export function handlePasteEvent(
  event: ClipboardEvent,
  columnOrder: string[],
  currentRow: number,
  currentCol: number
): PasteResult | null {
  const clipboardData = event.clipboardData?.getData('text')
  
  if (!clipboardData) {
    return null
  }
  
  const parsed = parsePastedData(clipboardData)
  
  // Validate that we have data
  if (parsed.rowCount === 0 || parsed.columnCount === 0) {
    return null
  }
  
  return parsed
}

/**
 * Show toast notification for paste operation
 */
export function showPasteNotification(
  rowCount: number,
  columnCount: number,
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void
) {
  showToast(
    `Pasted ${rowCount} row${rowCount !== 1 ? 's' : ''}, ${columnCount} column${columnCount !== 1 ? 's' : ''}`,
    'success'
  )
}
