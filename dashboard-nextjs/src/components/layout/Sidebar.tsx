'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  TrendingUp, 
  LineChart, 
  Gavel, 
  Dices,
  Settings
} from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Sentiment', href: '/sentiment', icon: TrendingUp },
  { name: 'Strategy', href: '/strategy', icon: LineChart },
  { name: 'Legislation', href: '/legislation', icon: Gavel },
  { name: 'Vegas Intel', href: '/vegas', icon: Dices },
  { name: 'Admin', href: '/admin', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-background-secondary border-r border-border-primary flex flex-col">
      {/* Logo/Brand */}
      <div className="p-6 border-b border-border-primary">
        <h1 className="text-xl font-bold text-text-primary">
          U.S. Oil Solutions
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Intelligence Platform
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors',
                isActive
                  ? 'bg-bull-500/10 text-bull-500 border-l-2 border-bull-500'
                  : 'text-text-secondary hover:text-text-primary hover:bg-background-tertiary'
              )}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Zinc Digital Branding */}
      <div className="px-4 py-4">
        <div className="flex items-center justify-center px-3 py-2 text-text-tertiary">
          <span className="text-xs font-semibold tracking-wider" style={{ fontFamily: 'monospace' }}>
            ZINC DIGITAL
          </span>
        </div>
      </div>

      {/* Bottom Status */}
      <div className="p-4 border-t border-border-primary">
        <div className="text-2xs text-text-tertiary mb-2 uppercase tracking-wider">
          System Status
        </div>
        <div className="space-y-1">
          <div className="flex items-center text-xs">
            <div className="w-2 h-2 bg-bull-500 rounded-full mr-2"></div>
            <span className="text-text-secondary">Models Active</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-2 h-2 bg-bull-500 rounded-full mr-2"></div>
            <span className="text-text-secondary">Real-Time Data</span>
          </div>
          <div className="flex items-center text-xs">
            <div className="w-2 h-2 bg-bull-500 rounded-full mr-2"></div>
            <span className="text-text-secondary">BigQuery Connected</span>
          </div>
        </div>
      </div>
    </div>
  )
}
