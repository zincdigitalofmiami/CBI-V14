'use client'

import { Bell, Search, User } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-background-secondary border-b border-border-primary px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Empty space for clean header */}
        <div></div>

        {/* Right side controls */}
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-text-tertiary" />
            <input
              type="text"
              placeholder="Search..."
              className="pl-10 pr-4 py-2 bg-background-tertiary border border-border-primary rounded-lg text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-bull-500/50 focus:border-bull-500"
            />
          </div>

          {/* Notifications */}
          <button className="relative p-2 text-text-secondary hover:text-text-primary hover:bg-background-tertiary rounded-lg transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-bear-500 rounded-full"></span>
          </button>

          {/* User menu */}
          <button className="flex items-center space-x-2 p-2 text-text-secondary hover:text-text-primary hover:bg-background-tertiary rounded-lg transition-colors">
            <User className="w-5 h-5" />
            <span className="text-sm">Chris Stacy</span>
          </button>
        </div>
      </div>
    </header>
  )
}
