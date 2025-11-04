'use client'

import { useQuery } from '@tanstack/react-query'
import { Users } from 'lucide-react'

interface Customer {
  id: string
  name: string
  account_type: 'Casino' | 'Restaurant' | 'Hotel' | 'Other'
  relationship_score: number
  current_volume: number
  last_order_date: string
  growth_potential: 'HIGH' | 'MEDIUM' | 'LOW'
  next_action: string
}

async function fetchCustomers(): Promise<Customer[]> {
  const response = await fetch('/api/v4/vegas/customers')
  if (!response.ok) return []
  return response.json()
}

export function CustomerRelationshipMatrix() {
  const { data: customers, isLoading } = useQuery({
    queryKey: ['vegas-customers'],
    queryFn: fetchCustomers,
    refetchInterval: 300000,
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="loading-shimmer h-64 w-full rounded"></div>
      </div>
    )
  }

  const customersList = customers || []

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">Customer Relationship Matrix</h2>
        <Users className="w-5 h-5 text-accent-blue" />
      </div>

      {customersList.length === 0 ? (
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-text-tertiary mx-auto mb-4" />
          <p className="text-text-secondary mb-2">No Customer Data</p>
          <p className="text-sm text-text-tertiary">Connect to Glide App or CRM to sync customer relationships</p>
        </div>
      ) : (
        <div className="space-y-3">
          {customersList.slice(0, 6).map((customer) => (
            <div key={customer.id} className="bg-background-tertiary border border-border-secondary rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-text-primary">{customer.name}</h3>
                <span className="px-2 py-1 rounded text-xs bg-accent-blue/20 text-accent-blue border border-accent-blue/30">
                  {customer.account_type}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-xs text-text-tertiary mb-1">Relationship Score</div>
                  <div className="font-semibold text-text-primary">{customer.relationship_score}/100</div>
                </div>
                <div>
                  <div className="text-xs text-text-tertiary mb-1">Current Volume</div>
                  <div className="font-semibold text-text-primary">{customer.current_volume.toLocaleString()}</div>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-border-secondary text-xs text-text-secondary">
                {customer.next_action}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
