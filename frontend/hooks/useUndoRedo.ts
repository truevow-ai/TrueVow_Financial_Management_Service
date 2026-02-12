"use client"

import { useState, useCallback, useRef } from 'react'

/**
 * Undo/Redo Hook for Grid Components
 * Manages undo/redo stack for grid cell edits
 */

export interface GridState {
  [cellKey: string]: any // cellKey format: "row-col" or "row-columnName"
}

interface HistoryEntry {
  state: GridState
  timestamp: number
}

export function useUndoRedo(initialState: GridState = {}) {
  const [currentState, setCurrentState] = useState<GridState>(initialState)
  const [history, setHistory] = useState<HistoryEntry[]>([{ state: initialState, timestamp: Date.now() }])
  const [historyIndex, setHistoryIndex] = useState(0)
  const maxHistorySize = 50 // Limit history to prevent memory issues
  
  const canUndo = historyIndex > 0
  const canRedo = historyIndex < history.length - 1
  
  /**
   * Save current state to history
   */
  const saveState = useCallback((newState: GridState) => {
    setCurrentState(newState)
    
    setHistory(prev => {
      // Remove any future history if we're not at the end
      const newHistory = prev.slice(0, historyIndex + 1)
      
      // Add new state
      newHistory.push({ state: newState, timestamp: Date.now() })
      
      // Limit history size
      if (newHistory.length > maxHistorySize) {
        newHistory.shift()
        return newHistory
      }
      
      return newHistory
    })
    
    setHistoryIndex(prev => {
      const newIndex = prev + 1
      // Don't exceed max history size
      return Math.min(newIndex, maxHistorySize - 1)
    })
  }, [historyIndex, maxHistorySize])
  
  /**
   * Undo last change
   */
  const undo = useCallback(() => {
    if (!canUndo) return
    
    const newIndex = historyIndex - 1
    setHistoryIndex(newIndex)
    setCurrentState(history[newIndex].state)
  }, [canUndo, historyIndex, history])
  
  /**
   * Redo last undone change
   */
  const redo = useCallback(() => {
    if (!canRedo) return
    
    const newIndex = historyIndex + 1
    setHistoryIndex(newIndex)
    setCurrentState(history[newIndex].state)
  }, [canRedo, historyIndex, history])
  
  /**
   * Update a single cell value
   */
  const updateCell = useCallback((cellKey: string, value: any) => {
    const newState = {
      ...currentState,
      [cellKey]: value
    }
    saveState(newState)
  }, [currentState, saveState])
  
  /**
   * Update multiple cells (for bulk operations like paste)
   */
  const updateCells = useCallback((updates: Record<string, any>) => {
    const newState = {
      ...currentState,
      ...updates
    }
    saveState(newState)
  }, [currentState, saveState])
  
  /**
   * Clear history (useful when loading new data)
   */
  const clearHistory = useCallback(() => {
    setHistory([{ state: currentState, timestamp: Date.now() }])
    setHistoryIndex(0)
  }, [currentState])
  
  /**
   * Reset to initial state
   */
  const reset = useCallback((newInitialState: GridState) => {
    setCurrentState(newInitialState)
    setHistory([{ state: newInitialState, timestamp: Date.now() }])
    setHistoryIndex(0)
  }, [])
  
  return {
    state: currentState,
    canUndo,
    canRedo,
    undo,
    redo,
    updateCell,
    updateCells,
    clearHistory,
    reset,
    saveState
  }
}

/**
 * Hook for keyboard shortcuts (Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z)
 */
export function useUndoRedoKeyboard(
  undo: () => void,
  redo: () => void,
  canUndo: boolean,
  canRedo: boolean
) {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Ctrl+Z or Cmd+Z for undo
    if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
      if (canUndo) {
        event.preventDefault()
        undo()
      }
    }
    
    // Ctrl+Y or Ctrl+Shift+Z or Cmd+Shift+Z for redo
    if (
      ((event.ctrlKey || event.metaKey) && event.key === 'y') ||
      ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'z')
    ) {
      if (canRedo) {
        event.preventDefault()
        redo()
      }
    }
  }, [undo, redo, canUndo, canRedo])
  
  return { handleKeyDown }
}
