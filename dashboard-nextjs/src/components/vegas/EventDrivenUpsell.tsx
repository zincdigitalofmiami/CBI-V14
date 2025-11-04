'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, Download, Brain, Check, Clock } from 'lucide-react'

interface UpsellOpportunity {
  id: string
  venue_name: string
  event_name: string
  event_date: string
  event_duration_days: number
  expected_attendance: number
  oil_demand_surge_gal: number
  revenue_opportunity: number
  urgency: 'IMMEDIATE ACTION' | 'HIGH PRIORITY' | 'MONITOR'
  messaging_strategy: {
    target: string
    monthly_forecast: string
    message: string
    timing: string
    value_prop: string
  }
}

async function fetchUpsellOpportunities(): Promise<UpsellOpportunity[]> {
  const response = await fetch('/api/v4/vegas/upsell-opportunities')
  
  if (!response.ok) {
    return []
  }
  
  return response.json()
}

export function EventDrivenUpsell() {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const { data: opportunities, isLoading } = useQuery({
    queryKey: ['vegas-upsell-opportunities'],
    queryFn: fetchUpsellOpportunities,
    refetchInterval: 300000, // Update every 5 minutes
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="loading-shimmer h-64 w-full rounded"></div>
      </div>
    )
  }

  const opportunitiesList = opportunities || []

  const handleDownloadList = (eventId: string) => {
    // TODO: Implement download functionality
    console.log('Download list for event:', eventId)
  }

  const handleAIMessage = (eventId: string) => {
    // TODO: Implement AI message generation
    console.log('Generate AI message for event:', eventId)
  }

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-text-primary mb-2">
          AI-Powered Event-Driven Oil Demand Forecasting
        </h2>
        <p className="text-sm text-text-secondary">
          Goldman Sachs ML · Real-Time Event Analytics · Proactive Restaurant Messaging System
        </p>
      </div>

      {opportunitiesList.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-12 h-12 text-text-tertiary mx-auto mb-4" />
          <p className="text-text-secondary mb-2">No Event Opportunities</p>
          <p className="text-sm text-text-tertiary">
            Connect to event calendar and customer data to see opportunities
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {opportunitiesList.map((opp) => {
            const isExpanded = expandedId === opp.id
            return (
              <div
                key={opp.id}
                className="bg-background-tertiary border border-border-secondary rounded-lg overflow-hidden hover:border-accent-blue/50 transition-colors"
              >
                {/* Event Row Header */}
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-base font-semibold text-text-primary">
                          {opp.venue_name} - {opp.event_name}
                        </h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          opp.urgency === 'IMMEDIATE ACTION' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                          opp.urgency === 'HIGH PRIORITY' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                          'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                        }`}>
                          {opp.urgency}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 text-sm text-text-secondary">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(opp.event_date).toLocaleDateString()}</span>
                        <span>·</span>
                        <span>{opp.event_duration_days} {opp.event_duration_days === 1 ? 'day' : 'days'}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-text-tertiary mb-1">Revenue Opportunity</div>
                      <div className="text-lg font-semibold text-bull-500">
                        +${opp.revenue_opportunity.toLocaleString()}
                      </div>
                    </div>
                  </div>

                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <div className="text-xs text-text-tertiary mb-1">Expected Attendance</div>
                      <div className="text-base font-semibold text-text-primary">
                        {opp.expected_attendance.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-text-tertiary mb-1">Oil Demand Surge</div>
                      <div className="text-base font-semibold text-bull-500">
                        +{opp.oil_demand_surge_gal} gal/day
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center justify-end space-x-3">
                    <button
                      onClick={() => handleDownloadList(opp.id)}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 rounded-lg transition-colors text-sm font-medium"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download List</span>
                    </button>
                    <button
                      onClick={() => handleAIMessage(opp.id)}
                      className="flex items-center space-x-2 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 border border-purple-500/30 rounded-lg transition-colors text-sm font-medium"
                    >
                      <Brain className="w-4 h-4" />
                      <span>AI Message</span>
                    </button>
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : opp.id)}
                      className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
                    >
                      {isExpanded ? 'Hide Strategy' : 'Show Strategy'}
                    </button>
                  </div>
                </div>

                {/* Expandable Messaging Strategy */}
                {isExpanded && opp.messaging_strategy && (
                  <div className="border-t border-border-secondary bg-background-secondary p-4">
                    <div className="flex items-start space-x-2 mb-4">
                      <Check className="w-5 h-5 text-green-400 mt-0.5" />
                      <h4 className="text-sm font-semibold text-text-primary">
                        Recommended Restaurant Messaging Strategy
                      </h4>
                    </div>
                    
                    <div className="space-y-3 text-sm">
                      <div>
                        <span className="text-text-tertiary font-medium">Target:</span>
                        <span className="text-text-secondary ml-2">{opp.messaging_strategy.target}</span>
                      </div>
                      
                      <div>
                        <span className="text-text-tertiary font-medium">Monthly Forecast:</span>
                        <span className="text-text-secondary ml-2">{opp.messaging_strategy.monthly_forecast}</span>
                      </div>
                      
                      <div className="bg-background-tertiary border border-border-secondary rounded-lg p-3">
                        <div className="text-text-tertiary font-medium mb-1">Message:</div>
                        <div className="text-text-primary">{opp.messaging_strategy.message}</div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-text-tertiary" />
                        <span className="text-text-tertiary font-medium">Timing:</span>
                        <span className="text-text-secondary">{opp.messaging_strategy.timing}</span>
                      </div>
                      
                      <div>
                        <span className="text-text-tertiary font-medium">Value Prop:</span>
                        <span className="text-text-secondary ml-2">{opp.messaging_strategy.value_prop}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
