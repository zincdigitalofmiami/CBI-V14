'use client'

import { useQuery } from '@tanstack/react-query'
import { Shield, AlertTriangle } from 'lucide-react'

interface MarginAlert {
  id: string
  customer_name: string
  alert_type: 'Price Drop' | 'Volume Spike' | 'Competitor Threat' | 'Contract Risk'
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM'
  current_margin: number
  risk_amount: number
  recommended_action: string
  urgency: 'IMMEDIATE' | 'WITHIN_24H' | 'THIS_WEEK'
}

async function fetchMarginAlerts(): Promise<MarginAlert[]> {
  const response = await fetch('/api/v4/vegas/margin-alerts')
  if (!response.ok) return []
  return response.json()
}

export function MarginProtectionAlerts() {
  const { data: alerts, isLoading } = useQuery({
    queryKey: ['vegas-margin-alerts'],
    queryFn: fetchMarginAlerts,
    refetchInterval: 120000,
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="loading-shimmer h-48 w-full rounded"></div>
      </div>
    )
  }

  const alertsList = alerts || []

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/50'
      case 'HIGH':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/50'
      default:
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
    }
  }

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">Event-Driven Margin Protection Alerts</h2>
        <Shield className="w-5 h-5 text-bear-500" />
      </div>

      {alertsList.length === 0 ? (
        <div className="text-center py-12">
          <Shield className="w-12 h-12 text-text-tertiary mx-auto mb-4" />
          <p className="text-text-secondary mb-2">No Margin Alerts</p>
          <p className="text-sm text-text-tertiary">All margins protected. Alerts will appear when risks are detected.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alertsList.map((alert) => (
            <div key={alert.id} className={`border rounded-lg p-4 ${getSeverityColor(alert.severity)}`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <AlertTriangle className="w-5 h-5" />
                    <h3 className="text-sm font-medium">{alert.customer_name}</h3>
                    <span className="px-2 py-1 rounded text-xs border">{alert.severity}</span>
                  </div>
                  <div className="text-xs mb-2">
                    <span className="font-medium">Type:</span> {alert.alert_type}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 mb-3">
                <div>
                  <div className="text-xs opacity-80 mb-1">Current Margin</div>
                  <div className="text-sm font-semibold">{alert.current_margin.toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-xs opacity-80 mb-1">Risk Amount</div>
                  <div className="text-sm font-semibold text-red-400">${(alert.risk_amount / 1000).toFixed(0)}K</div>
                </div>
                <div>
                  <div className="text-xs opacity-80 mb-1">Urgency</div>
                  <div className="text-sm font-semibold">{alert.urgency.replace('_', ' ')}</div>
                </div>
              </div>
              <div className="text-xs pt-2 border-t border-current/20">
                <span className="font-medium">Action:</span> {alert.recommended_action}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
