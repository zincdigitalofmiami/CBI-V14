'use client'

import { useQuery } from '@tanstack/react-query'
import { Users, TrendingUp, Calendar, DollarSign, AlertCircle } from 'lucide-react'

interface SalesMetrics {
  total_customers: number
  active_opportunities: number
  upcoming_events: number
  estimated_revenue_potential: number
  margin_risk_alerts: number
}

async function fetchSalesMetrics(): Promise<SalesMetrics> {
  const response = await fetch('/api/v4/vegas/metrics')
  if (!response.ok) {
    return {
      total_customers: 0,
      active_opportunities: 0,
      upcoming_events: 0,
      estimated_revenue_potential: 0,
      margin_risk_alerts: 0
    }
  }
  return response.json()
}

export function SalesIntelligenceOverview() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['vegas-sales-metrics'],
    queryFn: fetchSalesMetrics,
    refetchInterval: 60000,
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="loading-shimmer h-20 w-full rounded"></div>
          ))}
        </div>
      </div>
    )
  }

  const stats = [
    { label: 'Total Customers', value: metrics?.total_customers || 0, icon: Users },
    { label: 'Active Opportunities', value: metrics?.active_opportunities || 0, icon: TrendingUp },
    { label: 'Upcoming Events', value: metrics?.upcoming_events || 0, icon: Calendar },
    { label: 'Revenue Potential', value: `$${((metrics?.estimated_revenue_potential || 0) / 1000).toFixed(0)}K`, icon: DollarSign },
    { label: 'Margin Alerts', value: metrics?.margin_risk_alerts || 0, icon: AlertCircle },
  ]

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
      <h2 className="text-lg font-semibold text-text-primary mb-4">Sales Intelligence Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon
          return (
            <div key={i} className="bg-background-tertiary border border-border-secondary rounded-lg p-4">
              <Icon className="w-5 h-5 text-accent-blue mb-2" />
              <div className="text-2xl font-semibold text-text-primary mb-1">{stat.value}</div>
              <div className="text-xs text-text-tertiary uppercase tracking-wider">{stat.label}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
