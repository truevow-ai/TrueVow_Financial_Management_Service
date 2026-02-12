'use client'

import { ReactNode, useState } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'
import { Breadcrumbs } from './Breadcrumbs'
import { CommandPalette } from '@/components/common/CommandPalette'
import { GlobalSearch } from '@/components/common/GlobalSearch'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const [isSearchOpen, setIsSearchOpen] = useState(false)

  return (
    <>
      <div className="flex h-screen bg-gray-50">
        {/* Column 1: Dark Purple Sidebar */}
        <Sidebar />
        
        {/* Column 2: Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Sticky Header with Enterprise Features */}
          <Header onSearchClick={() => setIsSearchOpen(true)} />
          
          {/* Column 3: Contextual Navigation (Breadcrumbs) + Main Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Breadcrumbs Navigation */}
            <div className="bg-white border-b border-secondary-200 px-6 py-3">
              <Breadcrumbs />
            </div>
            
            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-6">
              {children}
            </main>
          </div>
        </div>
      </div>
      
      {/* Command Palette (Global - Cmd+K / Ctrl+K) */}
      <CommandPalette />
      
      {/* Global Search (Search-First Navigation) */}
      <GlobalSearch isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </>
  )
}
