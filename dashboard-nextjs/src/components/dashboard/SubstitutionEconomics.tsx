'use client'

import { useState, useEffect } from 'react'
import useSWR from 'swr'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ScatterChart, Scatter } from 'recharts'

interface SubstitutionData {
  data_date: string
  current_analysis: {
    [key: string]: {
      name: string
      base_price: number
      transport_cost: number
      total_cost: number
      transport_description: string
      substitution_signal: string
      correlation: number
      model_importance: number
    }
  }
  cost_curves: Array<{
    soy_price: number
    soy_total_cost: number
    palm_total_cost: number
    canola_total_cost: number
    optimal_choice: string
  }>
  switching_points: Array<{
    price: number
    from_oil: string
    to_oil: string
    cost_difference: number
  }>
  market_dynamics: {
    palm_correlation: number
    substitution_active: boolean
    current_leader: string
    arbitrage_opportunity: number
  }
  feature_importance: {
    palm_correlation_weight: number
    price_correlation_weight: number
    substitution_regime: string
  }
  last_updated: string
}

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function SubstitutionEconomics() {
  const { data, error, isLoading } = useSWR<SubstitutionData>('/api/v4/substitution-economics', fetcher, {
    refreshInterval: 30 * 60 * 1000, // 30 minutes
    revalidateOnFocus: false
  })

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center">
          <div className="text-red-400 text-sm font-medium mb-2">
            ⚠️ SUBSTITUTION ANALYSIS OFFLINE
          </div>
          <div className="text-gray-400 text-xs">
            Oil price comparison data unavailable
          </div>
        </div>
      </div>
    )
  }

  if (isLoading || !data) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-700 rounded mb-4"></div>
          <div className="grid grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const getOptimalColor = (choice: string) => {
    switch (choice) {
      case 'soy': return '#10B981'      // Green
      case 'palm': return '#F59E0B'     // Amber  
      case 'canola': return '#3B82F6'   // Blue
      default: return '#6B7280'         // Gray
    }
  }

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'SUBSTITUTE': return 'text-green-400 bg-green-400/20'
      case 'NO_SUBSTITUTE': return 'text-red-400 bg-red-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }

  // Prepare chart data
  const chartData = data.cost_curves.map((curve, index) => ({
    price: curve.soy_price,
    soy: curve.soy_total_cost,
    palm: curve.palm_total_cost,
    canola: curve.canola_total_cost,
    optimal: curve.optimal_choice,
    savings: Math.max(curve.soy_total_cost, curve.palm_total_cost, curve.canola_total_cost) - 
             Math.min(curve.soy_total_cost, curve.palm_total_cost, curve.canola_total_cost)
  }))

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-background-tertiary border border-gray-600 rounded-lg p-3 shadow-xl">
          <p className="text-gray-300 font-medium mb-2">Soy Price: ${label.toFixed(2)}</p>
          <div className="space-y-1 text-sm">
            <p className="text-green-400">Soy Total: ${data.soy.toFixed(2)}</p>
            <p className="text-yellow-400">Palm Total: ${data.palm.toFixed(2)}</p>
            <p className="text-blue-400">Canola Total: ${data.canola.toFixed(2)}</p>
            <p className="text-purple-400 font-medium">
              Optimal: {data.optimal.toUpperCase()}
            </p>
            <p className="text-gray-400">Max Savings: ${data.savings.toFixed(2)}</p>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-1">
            Substitution Economics Calculator
          </h2>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400">Current Leader: {data.market_dynamics.current_leader.toUpperCase()}</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              data.feature_importance.substitution_regime === 'HIGH_IMPACT' ? 
              'bg-yellow-400/20 text-yellow-400' : 'bg-blue-400/20 text-blue-400'
            }`}>
              {data.feature_importance.substitution_regime.replace('_', ' ')}
            </span>
            <span className="text-gray-400">Arbitrage: ${data.market_dynamics.arbitrage_opportunity.toFixed(2)}</span>
          </div>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>Data: {data.data_date}</div>
          <div>Updated: {new Date(data.last_updated).toLocaleTimeString()}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Cost Curve Chart */}
        <div className="xl:col-span-2">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="price" 
                  stroke="#9CA3AF" 
                  fontSize={12}
                  tick={{ fill: '#9CA3AF' }}
                  label={{ value: 'Soybean Oil Price ($)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
                />
                <YAxis 
                  stroke="#9CA3AF" 
                  fontSize={12}
                  tick={{ fill: '#9CA3AF' }}
                  label={{ value: 'Total Delivered Cost ($)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
                />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Cost Lines */}
                <Line 
                  type="monotone" 
                  dataKey="soy" 
                  stroke="#10B981" 
                  strokeWidth={3}
                  dot={false}
                  name="Soybean Oil"
                />
                <Line 
                  type="monotone" 
                  dataKey="palm" 
                  stroke="#F59E0B" 
                  strokeWidth={3}
                  dot={false}
                  name="Palm Oil"
                />
                <Line 
                  type="monotone" 
                  dataKey="canola" 
                  stroke="#3B82F6" 
                  strokeWidth={3}
                  dot={false}
                  name="Canola Oil"
                />
                
                {/* Current Price Reference */}
                <ReferenceLine 
                  x={data.current_analysis.soy.base_price} 
                  stroke="#EF4444" 
                  strokeDasharray="2 2" 
                  strokeOpacity={0.7}
                  label={{ value: "Current", position: "top", fill: "#EF4444" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Switching Points */}
          {data.switching_points.length > 0 && (
            <div className="mt-4 p-3 bg-background-tertiary rounded-lg border border-gray-700">
              <h3 className="text-sm font-medium text-text-primary mb-2">
                💎 Switching Points (Arbitrage Opportunities)
              </h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 text-xs">
                {data.switching_points.slice(0, 4).map((point, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-gray-300">
                      ${point.price.toFixed(2)}: {point.from_oil} → {point.to_oil}
                    </span>
                    <span className="text-green-400 font-medium">
                      ${point.cost_difference.toFixed(2)} savings
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Feature Importance Overlay */}
          <div className="mt-4 p-3 bg-background-tertiary rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-text-primary mb-2">
              🎯 Model Feature Importance
            </h3>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <div className="text-gray-400">Palm Correlation Impact</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-700 rounded-full h-2">
                    <div 
                      className="h-2 bg-yellow-400 rounded-full" 
                      style={{ width: `${Math.min(100, data.feature_importance.palm_correlation_weight)}%` }}
                    />
                  </div>
                  <span className="text-yellow-400 font-medium">
                    {data.feature_importance.palm_correlation_weight.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div>
                <div className="text-gray-400">Price Correlation Impact</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-700 rounded-full h-2">
                    <div 
                      className="h-2 bg-green-400 rounded-full" 
                      style={{ width: `${Math.min(100, data.feature_importance.price_correlation_weight)}%` }}
                    />
                  </div>
                  <span className="text-green-400 font-medium">
                    {data.feature_importance.price_correlation_weight.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Current Analysis */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-text-primary">Current Cost Analysis</h3>
          
          {Object.entries(data.current_analysis).map(([key, oil]) => (
            <div key={key} className="bg-background-tertiary rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-text-primary">{oil.name}</h4>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getSignalColor(oil.substitution_signal)}`}>
                  {oil.substitution_signal.replace('_', ' ')}
                </span>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Base Price:</span>
                  <span className="text-text-primary font-medium">${oil.base_price.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Transport:</span>
                  <span className="text-text-primary">${oil.transport_cost.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-t border-gray-600 pt-2">
                  <span className="text-gray-400 font-medium">Total Cost:</span>
                  <span className={`font-bold ${
                    key === data.market_dynamics.current_leader ? 'text-green-400' : 'text-text-primary'
                  }`}>
                    ${oil.total_cost.toFixed(2)}
                  </span>
                </div>
              </div>
              
              <div className="mt-3 pt-2 border-t border-gray-600">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-gray-500">Correlation:</span>
                  <span className="text-gray-400">{(oil.correlation * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-gray-500">Model Weight:</span>
                  <span className="text-gray-400">{oil.model_importance.toFixed(1)}%</span>
                </div>
              </div>
              
              <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                {oil.transport_description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 text-sm">
          <div>
            <div className="text-gray-400">Palm Correlation</div>
            <div className={`font-bold ${
              Math.abs(data.market_dynamics.palm_correlation) > 0.5 ? 'text-yellow-400' : 'text-gray-400'
            }`}>
              {(data.market_dynamics.palm_correlation * 100).toFixed(0)}%
            </div>
          </div>
          <div>
            <div className="text-gray-400">Substitution Active</div>
            <div className={`font-bold ${
              data.market_dynamics.substitution_active ? 'text-green-400' : 'text-gray-400'
            }`}>
              {data.market_dynamics.substitution_active ? 'YES' : 'NO'}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Switching Points</div>
            <div className="font-bold text-blue-400">
              {data.switching_points.length}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Max Arbitrage</div>
            <div className="font-bold text-purple-400">
              ${data.market_dynamics.arbitrage_opportunity.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Model Regime</div>
            <div className={`font-bold text-xs ${
              data.feature_importance.substitution_regime === 'HIGH_IMPACT' ? 'text-yellow-400' : 'text-blue-400'
            }`}>
              {data.feature_importance.substitution_regime.replace('_', ' ')}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
