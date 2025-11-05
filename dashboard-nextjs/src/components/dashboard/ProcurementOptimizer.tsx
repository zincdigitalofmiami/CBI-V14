'use client'

import { useState, useEffect } from 'react'
import useSWR from 'swr'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart, Bar } from 'recharts'

interface OpportunityData {
  date: string
  price: number
  vix: number
  vix_regime: string
  signal: string
  risk_score: number
  confidence: string
  potential_savings: number
  momentum: number
  ma_20: number
}

interface CurrentOpportunity {
  signal: string
  confidence: string
  risk_score: number
  vix_level: number
  vix_regime: string
  current_price: number
  forecast_price: number
  potential_savings: number
  days_to_target: number
  recommendation: string
}

interface ProcurementTimingData {
  current_opportunity: CurrentOpportunity
  historical_opportunities: OpportunityData[]
  forecast_data: {
    predicted_price: number
    confidence_lower: number
    confidence_upper: number
    target_date: string
  }
  vix_analysis: {
    current_level: number
    regime: string
    fear_index: number
    market_stress: string
  }
  last_updated: string
}

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function ProcurementOptimizer() {
  const { data, error, isLoading } = useSWR<ProcurementTimingData>('/api/v4/procurement-timing', fetcher, {
    refreshInterval: 15 * 60 * 1000, // 15 minutes
    revalidateOnFocus: false
  })

  if (error) {
    return (
      <div className="bg-background-secondary rounded-lg p-6 border border-gray-800">
        <div className="text-center">
          <div className="text-red-400 text-sm font-medium mb-2">
            ⚠️ PROCUREMENT OPTIMIZER OFFLINE
          </div>
          <div className="text-gray-400 text-xs">
            VIX and price data synchronization required
          </div>
        </div>
      </div>
    )
  }

  if (isLoading || !data) {
    return (
      <div className="bg-background-secondary rounded-lg p-6 border border-gray-800">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-700 rounded mb-4"></div>
          <div className="h-20 bg-gray-700 rounded"></div>
        </div>
      </div>
    )
  }

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'STRONG_BUY': return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-400' }
      case 'BUY': return { bg: 'bg-green-400/20', text: 'text-green-300', border: 'border-green-300' }
      case 'BUY_DIP': return { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-400' }
      case 'WAIT': return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-400' }
      default: return { bg: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-400' }
    }
  }

  const getVixRegimeColor = (regime: string) => {
    switch (regime) {
      case 'CRISIS': return 'text-red-500'
      case 'HIGH_FEAR': return 'text-red-400'
      case 'ELEVATED': return 'text-yellow-400'
      case 'NORMAL': return 'text-blue-400'
      case 'COMPLACENT': return 'text-green-400'
      default: return 'text-gray-400'
    }
  }

  const signalColors = getSignalColor(data.current_opportunity.signal)
  
  // Prepare chart data with VIX overlay
  const chartData = data.historical_opportunities.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    price: item.price,
    vix: item.vix,
    ma_20: item.ma_20,
    opportunity: item.signal === 'STRONG_BUY' || item.signal === 'BUY' || item.signal === 'BUY_DIP' ? item.price : null,
    risk_zone: item.vix > 25 ? item.price : null,
    savings: item.potential_savings
  })).reverse().slice(-30) // Last 30 days

  // Add forecast point
  const forecastPoint = {
    date: new Date(data.forecast_data.target_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    price: data.forecast_data.predicted_price,
    vix: null,
    ma_20: null,
    opportunity: null,
    risk_zone: null,
    forecast: data.forecast_data.predicted_price,
    forecast_lower: data.forecast_data.confidence_lower,
    forecast_upper: data.forecast_data.confidence_upper
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-background-tertiary border border-gray-600 rounded-lg p-3 shadow-xl">
          <p className="text-gray-300 font-medium mb-2">{label}</p>
          <div className="space-y-1 text-sm">
            <p className="text-blue-400">Price: ${data.price?.toFixed(2)}</p>
            {data.vix && <p className="text-yellow-400">VIX: {data.vix.toFixed(1)}</p>}
            {data.ma_20 && <p className="text-gray-400">MA20: ${data.ma_20.toFixed(2)}</p>}
            {data.opportunity && <p className="text-green-400">📍 Buy Opportunity</p>}
            {data.forecast && <p className="text-purple-400">🎯 Forecast: ${data.forecast.toFixed(2)}</p>}
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-background-secondary rounded-lg p-6 border border-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-1">
            Procurement Timing Optimizer - VIX Intelligence
          </h2>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400">Current ZL: ${data.current_opportunity.current_price.toFixed(2)}</span>
            <span className={`font-medium ${getVixRegimeColor(data.vix_analysis.regime)}`}>
              VIX: {data.vix_analysis.current_level.toFixed(1)} ({data.vix_analysis.regime})
            </span>
            <span className="text-gray-400">
              Stress: {data.vix_analysis.market_stress}
            </span>
          </div>
        </div>
        <div className={`px-4 py-2 rounded-lg border ${signalColors.bg} ${signalColors.border}`}>
          <div className={`text-lg font-bold ${signalColors.text}`}>
            {data.current_opportunity.signal.replace('_', ' ')}
          </div>
          <div className="text-xs text-gray-400 text-center">
            {data.current_opportunity.confidence} CONFIDENCE
          </div>
        </div>
      </div>

      {/* Main Chart - Price + VIX Overlay */}
      <div className="mb-6">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
              />
              <YAxis 
                yAxisId="price"
                stroke="#60A5FA" 
                fontSize={12}
                tick={{ fill: '#60A5FA' }}
                label={{ value: 'Price ($)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#60A5FA' } }}
              />
              <YAxis 
                yAxisId="vix"
                orientation="right"
                stroke="#FBBF24" 
                fontSize={12}
                tick={{ fill: '#FBBF24' }}
                label={{ value: 'VIX', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#FBBF24' } }}
              />
              <Tooltip content={<CustomTooltip />} />
              
              {/* Price Line */}
              <Line 
                yAxisId="price"
                type="monotone" 
                dataKey="price" 
                stroke="#60A5FA" 
                strokeWidth={2}
                dot={false}
                name="ZL Price"
              />
              
              {/* 20-day Moving Average */}
              <Line 
                yAxisId="price"
                type="monotone" 
                dataKey="ma_20" 
                stroke="#9CA3AF" 
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="MA20"
              />
              
              {/* VIX Bar Chart */}
              <Bar 
                yAxisId="vix"
                dataKey="vix" 
                fill="#FBBF24" 
                fillOpacity={0.3}
                name="VIX"
              />
              
              {/* Buy Opportunities */}
              <Line 
                yAxisId="price"
                type="monotone" 
                dataKey="opportunity" 
                stroke="#10B981" 
                strokeWidth={0}
                dot={{ fill: '#10B981', strokeWidth: 2, r: 6 }}
                name="Buy Opportunity"
              />
              
              {/* High Risk Zones (VIX > 25) */}
              <Line 
                yAxisId="price"
                type="monotone" 
                dataKey="risk_zone" 
                stroke="#EF4444" 
                strokeWidth={0}
                dot={{ fill: '#EF4444', strokeWidth: 2, r: 4, fillOpacity: 0.7 }}
                name="High Volatility"
              />
              
              {/* VIX Reference Lines */}
              <ReferenceLine yAxisId="vix" y={20} stroke="#FBBF24" strokeDasharray="2 2" strokeOpacity={0.5} />
              <ReferenceLine yAxisId="vix" y={30} stroke="#EF4444" strokeDasharray="2 2" strokeOpacity={0.5} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        
        {/* Chart Legend */}
        <div className="flex items-center justify-center gap-6 mt-3 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-blue-400"></div>
            <span>ZL Price</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-gray-400 opacity-50" style={{borderTop: '1px dashed'}}></div>
            <span>MA20</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-400 opacity-30"></div>
            <span>VIX Level</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-400 rounded-full"></div>
            <span>Buy Signal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-400 rounded-full opacity-70"></div>
            <span>High Vol</span>
          </div>
        </div>
      </div>

      {/* Current Recommendation */}
      <div className="bg-background-tertiary rounded-lg p-4 border border-gray-700 mb-4">
        <h3 className="text-sm font-medium text-text-primary mb-2">AI Procurement Recommendation</h3>
        <p className="text-sm text-gray-300 leading-relaxed mb-3">
          {data.current_opportunity.recommendation}
        </p>
        
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div>
            <div className="text-gray-400">Potential Savings</div>
            <div className="text-green-400 font-bold text-sm">
              ${data.current_opportunity.potential_savings.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Risk Score</div>
            <div className={`font-bold text-sm ${
              data.current_opportunity.risk_score > 70 ? 'text-red-400' :
              data.current_opportunity.risk_score > 40 ? 'text-yellow-400' : 'text-green-400'
            }`}>
              {Math.round(data.current_opportunity.risk_score)}/100
            </div>
          </div>
          <div>
            <div className="text-gray-400">Forecast Target</div>
            <div className="text-purple-400 font-bold text-sm">
              ${data.current_opportunity.forecast_price.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Fear Index</div>
            <div className={`font-bold text-sm ${getVixRegimeColor(data.vix_analysis.regime)}`}>
              {Math.round(data.vix_analysis.fear_index)}%
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div>
          VIX Thresholds: 20+ Elevated • 25+ High Fear • 30+ Crisis Mode
        </div>
        <div>
          Updated: {new Date(data.last_updated).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}




