'use client'

import { useQuery } from '@tanstack/react-query'
import { TrendingUp, Database } from 'lucide-react'
import { LineChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceDot } from 'recharts'

interface ForwardCurveData {
  chartData: Array<{
    date: string
    price: number
    confidence_lower?: number
    confidence_upper?: number
    type: 'historical' | 'current' | 'forecast'
    horizon?: string
  }>
  buyZones: Array<{
    horizon: string
    date: string
    price: number
    savingsPercent: string
  }>
  currentPrice: number
  forecastCount: number
}

async function fetchForwardCurve(): Promise<ForwardCurveData> {
  const response = await fetch('/api/v4/forward-curve')
  
  if (!response.ok) {
    throw new Error('Forward curve data unavailable')
  }
  
  return await response.json()
}

export function ForwardCurve() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['forward-curve'],
    queryFn: fetchForwardCurve,
    refetchInterval: 60 * 1000, // Update every minute
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="flex items-center space-x-2 mb-4">
          <TrendingUp className="w-6 h-6 text-buy-primary animate-pulse" />
          <h2 className="text-2xl font-light text-text-primary">
            Forward Curve - Where ZL is Going
          </h2>
        </div>
        <div className="loading-shimmer h-96 w-full rounded"></div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="text-center py-12 text-text-secondary">
          Forward curve data temporarily unavailable
        </div>
      </div>
    )
  }

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6 shadow-depth">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <TrendingUp className="w-6 h-6 text-buy-primary" />
          <div>
            <h2 className="text-2xl font-light text-text-primary">
              Forward Curve - Where ZL is Going
            </h2>
            <p className="text-sm text-text-secondary mt-1">
              Historical prices + Vertex AI 6-month outlook
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-sm">
          <Database className="w-4 h-4 text-accent-green" />
          <span className="text-text-secondary">
            {data.forecastCount} AI predictions loaded
          </span>
        </div>
      </div>

      {/* Main Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data.chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          
          <XAxis 
            dataKey="date" 
            stroke="#9099a6"
            style={{ fontSize: '12px', fontFamily: 'SF Mono, monospace' }}
            tickFormatter={(value) => {
              const date = new Date(value)
              return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
            }}
          />
          
          <YAxis 
            stroke="#9099a6"
            domain={['dataMin - 2', 'dataMax + 2']}
            style={{ fontSize: '12px', fontFamily: 'SF Mono, monospace' }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          
          <Tooltip 
            contentStyle={{
              backgroundColor: '#0a0a0f',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              padding: '12px',
              fontFamily: 'SF Mono, monospace',
              fontSize: '12px'
            }}
            labelStyle={{ color: '#E0E0E3', marginBottom: '8px' }}
            formatter={(value: any, name: string) => {
              if (name === 'price') return [`$${parseFloat(value).toFixed(2)}`, 'Price']
              return [value, name]
            }}
          />
          
          <Legend 
            wrapperStyle={{ 
              paddingTop: '20px',
              fontFamily: 'SF Mono, monospace',
              fontSize: '12px'
            }}
          />
          
          {/* Historical line (gray) */}
          <Line 
            type="monotone" 
            dataKey="price"
            data={data.chartData.filter(d => d.type === 'historical' || d.type === 'current')}
            stroke="#6b7280" 
            strokeWidth={2}
            dot={false}
            name="Historical"
          />
          
          {/* Forecast line (electric blue) */}
          <Line 
            type="monotone" 
            dataKey="price"
            data={data.chartData.filter(d => d.type === 'forecast' || d.type === 'current')}
            stroke="#0055FF" 
            strokeWidth={3}
            strokeDasharray="5 5"
            dot={{ r: 6, fill: '#00C8FF', stroke: '#0055FF', strokeWidth: 2 }}
            name="Vertex AI Forecast"
          />
          
          {/* Confidence area (shaded blue) */}
          <Area
            type="monotone"
            dataKey="confidence_upper"
            stroke="none"
            fill="#0055FF"
            fillOpacity={0.1}
            data={data.chartData.filter(d => d.type === 'forecast')}
          />
          <Area
            type="monotone"
            dataKey="confidence_lower"
            stroke="none"
            fill="#0055FF"
            fillOpacity={0.1}
            data={data.chartData.filter(d => d.type === 'forecast')}
          />
          
          {/* Buy zone markers */}
          {data.buyZones.map((zone, idx) => (
            <ReferenceDot
              key={idx}
              x={zone.date}
              y={zone.price}
              r={8}
              fill="#00FF66"
              stroke="#00FF66"
              strokeWidth={2}
              opacity={0.8}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Buy Zones Legend */}
      {data.buyZones.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border-secondary">
          <div className="flex items-center space-x-4 flex-wrap">
            <span className="text-sm text-text-secondary font-mono">BUY ZONES:</span>
            {data.buyZones.map((zone, idx) => (
              <div key={idx} className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-accent-green rounded-full"></div>
                <span className="text-sm text-text-primary">
                  {zone.horizon}: ${zone.price.toFixed(2)} 
                  <span className="text-accent-green ml-2">(-{zone.savingsPercent}%)</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chart Info */}
      <div className="mt-4 pt-4 border-t border-border-secondary flex items-center justify-between">
        <div className="text-xs text-text-secondary">
          <span className="font-mono">DATA:</span> 365 days historical + {data.forecastCount} AI predictions
        </div>
        <div className="text-xs text-text-tertiary">
          Current: ${data.currentPrice.toFixed(2)}/cwt
        </div>
      </div>
    </div>
  )
}


