'use client'

import { useQuery } from '@tanstack/react-query'
import { Calendar, TrendingUp } from 'lucide-react'

interface Event {
  id: string
  name: string
  type: 'F1 Race' | 'Convention' | 'Festival' | 'Concert' | 'Other'
  date: string
  location: string
  volume_multiplier: number
  affected_customers: number
  revenue_impact: number
  days_until: number
}

async function fetchUpcomingEvents(): Promise<Event[]> {
  const response = await fetch('/api/v4/vegas/events')
  if (!response.ok) return []
  return response.json()
}

export function EventVolumeMultipliers() {
  const { data: events, isLoading } = useQuery({
    queryKey: ['vegas-upcoming-events'],
    queryFn: fetchUpcomingEvents,
    refetchInterval: 3600000,
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="loading-shimmer h-48 w-full rounded"></div>
      </div>
    )
  }

  const eventsList = events || []

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">F1 Race & Convention Volume Multipliers</h2>
        <Calendar className="w-5 h-5 text-accent-blue" />
      </div>

      {eventsList.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-12 h-12 text-text-tertiary mx-auto mb-4" />
          <p className="text-text-secondary mb-2">No Upcoming Events</p>
          <p className="text-sm text-text-tertiary">Connect to event calendar to track volume multipliers</p>
        </div>
      ) : (
        <div className="space-y-3">
          {eventsList.map((event) => (
            <div key={event.id} className="bg-background-tertiary border border-border-secondary rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-sm font-medium text-text-primary mb-1">{event.name}</h3>
                  <div className="text-xs text-text-secondary">{event.location}</div>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-1 text-bull-500">
                    <TrendingUp className="w-4 h-4" />
                    <span className="text-lg font-semibold">{event.volume_multiplier.toFixed(1)}x</span>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-xs text-text-tertiary mb-1">Revenue Impact</div>
                  <div className="font-semibold text-bull-500">${(event.revenue_impact / 1000).toFixed(0)}K</div>
                </div>
                <div>
                  <div className="text-xs text-text-tertiary mb-1">Customers</div>
                  <div className="font-semibold text-text-primary">{event.affected_customers}</div>
                </div>
                <div>
                  <div className="text-xs text-text-tertiary mb-1">Days Until</div>
                  <div className="font-semibold text-text-primary">{event.days_until}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
