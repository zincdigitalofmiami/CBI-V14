'use client'

import { useQuery } from '@tanstack/react-query'
import { Globe, Wheat, Fuel, TreePine } from 'lucide-react'

interface FourFactorsData {
  china_status: {
    imports_mt: number
    status: string
    impact_cwt: number
    timeline: string
  }
  harvest_status: {
    brazil_pct: number
    argentina_status: string
    impact_cwt: number
    description: string
  }
  biofuel_status: {
    rin_prices: string
    industrial_demand: number
    impact_cwt: number
    trend: string
  }
  palm_oil_status: {
    spread_mt: number
    substitution_risk: string
    impact_cwt: number
    assessment: string
  }
}

async function fetchFourFactors(): Promise<FourFactorsData> {
  const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
  
  // Get forecast data to derive factors
  const response = await fetch(`${apiUrl}/api/v4/forecast/1w`)
  
  if (!response.ok) {
    throw new Error('Market data temporarily unavailable')
  }
  
  const forecastData = await response.json()
  
  // Get Big 8 signals
  const signalsResponse = await fetch('/api/v4/big-eight-signals')
  if (!signalsResponse.ok) {
    throw new Error('Signals unavailable')
  }
  
  const signalsData = await signalsResponse.json()
  
  // Find specific signals
  const chinaSignal = signalsData.signals.find((s: any) => s.key === 'china_imports')
  const argentinaSignal = signalsData.signals.find((s: any) => s.key === 'argentina_tax')
  const industrialSignal = signalsData.signals.find((s: any) => s.key === 'industrial_demand')
  const palmSignal = signalsData.signals.find((s: any) => s.key === 'palm_spread')
  const harvestSignal = signalsData.signals.find((s: any) => s.key === 'harvest_pace')
  
  // Transform to four factors format
  return {
    china_status: {
      imports_mt: chinaSignal?.value || 0,
      status: chinaSignal?.value < 1 ? 'BOYCOTT ACTIVE' : chinaSignal?.value > 12 ? 'STRONG DEMAND' : 'NORMAL',
      impact_cwt: chinaSignal?.value < 1 ? -1.20 : chinaSignal?.value > 12 ? 1.50 : 0,
      timeline: chinaSignal?.value < 1 ? 'Through Q1 2026' : 'Ongoing'
    },
    harvest_status: {
      brazil_pct: (harvestSignal?.value || 0) * 100,
      argentina_status: argentinaSignal?.value < 5 ? 'Competitive (low tax)' : 'Normal taxation',
      impact_cwt: (harvestSignal?.value || 0) > 0.7 ? -0.80 : 0,
      description: (harvestSignal?.value || 0) > 0.7 ? 'Supply glut developing' : 'Normal supply'
    },
    biofuel_status: {
      rin_prices: 'Stable',
      industrial_demand: industrialSignal?.value || 0,
      impact_cwt: (industrialSignal?.value || 0) > 0.5 ? 0.40 : 0,
      trend: (industrialSignal?.value || 0) > 0.5 ? 'Growing demand' : 'Stable'
    },
    palm_oil_status: {
      spread_mt: palmSignal?.value || 0,
      substitution_risk: (palmSignal?.value || 0) < 10 ? 'High' : (palmSignal?.value || 0) > 20 ? 'Low' : 'Medium',
      impact_cwt: (palmSignal?.value || 0) < 10 ? -0.50 : 0,
      assessment: (palmSignal?.value || 0) < 10 ? 'Risk of substitution' : 'Neutral impact'
    }
  }
}

function getImpactColor(impact: number) {
  if (impact > 0) return 'text-bull-500'
  if (impact < 0) return 'text-bear-500'
  return 'text-neutral-500'
}

export function ChrisFourFactors() {
  const { data: factors, isLoading, error } = useQuery({
    queryKey: ['four-factors'],
    queryFn: fetchFourFactors,
    refetchInterval: 300000, // Update every 5 minutes (slower data)
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="space-y-4">
          <div className="loading-shimmer h-5 w-32 rounded"></div>
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="loading-shimmer h-12 w-full rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error || !factors) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-background-tertiary flex items-center justify-center">
            <Globe className="w-8 h-8 text-text-secondary animate-pulse" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Loading Market Factors
          </h3>
          <p className="text-text-secondary">
            Analyzing market conditions...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
      {/* Header */}
      <h3 className="text-lg font-semibold text-text-primary mb-4">
        Chris's Four Critical Factors
      </h3>

      <div className="space-y-4">
        {/* 1. China Purchases */}
        <div className="flex items-start space-x-3 p-3 bg-background-tertiary rounded-lg">
          <Globe className="w-5 h-5 text-text-secondary mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-sm font-medium text-text-primary">China Demand</h4>
              <span className={`text-sm font-semibold ${getImpactColor(factors.china_status.impact_cwt)}`}>
                {factors.china_status.impact_cwt > 0 ? '+' : ''}{factors.china_status.impact_cwt.toFixed(2)}/cwt
              </span>
            </div>
            <div className="text-xs text-bear-500 font-medium mb-1">
              {factors.china_status.imports_mt} MT • {factors.china_status.status}
            </div>
            <div className="text-xs text-text-tertiary">
              {factors.china_status.timeline}
            </div>
          </div>
        </div>

        {/* 2. Harvest Updates */}
        <div className="flex items-start space-x-3 p-3 bg-background-tertiary rounded-lg">
          <Wheat className="w-5 h-5 text-text-secondary mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-sm font-medium text-text-primary">Supply Pressure</h4>
              <span className={`text-sm font-semibold ${getImpactColor(factors.harvest_status.impact_cwt)}`}>
                {factors.harvest_status.impact_cwt > 0 ? '+' : ''}{factors.harvest_status.impact_cwt.toFixed(2)}/cwt
              </span>
            </div>
            <div className="text-xs text-bear-500 font-medium mb-1">
              Brazil {factors.harvest_status.brazil_pct}% • {factors.harvest_status.argentina_status}
            </div>
            <div className="text-xs text-text-tertiary">
              {factors.harvest_status.description}
            </div>
          </div>
        </div>

        {/* 3. Biofuel Markets */}
        <div className="flex items-start space-x-3 p-3 bg-background-tertiary rounded-lg">
          <Fuel className="w-5 h-5 text-text-secondary mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-sm font-medium text-text-primary">New Uses for Soy Oil</h4>
              <span className={`text-sm font-semibold ${getImpactColor(factors.biofuel_status.impact_cwt)}`}>
                +{factors.biofuel_status.impact_cwt.toFixed(2)}/cwt
              </span>
            </div>
            <div className="text-xs text-bull-500 font-medium mb-1">
              RIN {factors.biofuel_status.rin_prices} • Industrial {factors.biofuel_status.industrial_demand.toFixed(2)}
            </div>
            <div className="text-xs text-text-tertiary">
              {factors.biofuel_status.trend}
            </div>
          </div>
        </div>

        {/* 4. Palm Oil Substitution */}
        <div className="flex items-start space-x-3 p-3 bg-background-tertiary rounded-lg">
          <TreePine className="w-5 h-5 text-text-secondary mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-sm font-medium text-text-primary">Palm Oil Threat</h4>
              <span className={`text-sm font-semibold ${getImpactColor(factors.palm_oil_status.impact_cwt)}`}>
                {factors.palm_oil_status.impact_cwt === 0 ? '±' : factors.palm_oil_status.impact_cwt > 0 ? '+' : ''}{factors.palm_oil_status.impact_cwt.toFixed(2)}/cwt
              </span>
            </div>
            <div className="text-xs text-neutral-500 font-medium mb-1">
              ${factors.palm_oil_status.spread_mt}/MT Premium • {factors.palm_oil_status.substitution_risk} Risk
            </div>
            <div className="text-xs text-text-tertiary">
              {factors.palm_oil_status.assessment}
            </div>
          </div>
        </div>
      </div>

      {/* Net Impact */}
      <div className="mt-4 pt-4 border-t border-border-primary">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-text-secondary">Net Impact:</span>
          <span className={`text-lg font-bold ${getImpactColor(
            factors.china_status.impact_cwt + 
            factors.harvest_status.impact_cwt + 
            factors.biofuel_status.impact_cwt + 
            factors.palm_oil_status.impact_cwt
          )}`}>
            {(factors.china_status.impact_cwt + 
              factors.harvest_status.impact_cwt + 
              factors.biofuel_status.impact_cwt + 
              factors.palm_oil_status.impact_cwt) > 0 ? '+' : ''}
            {(factors.china_status.impact_cwt + 
              factors.harvest_status.impact_cwt + 
              factors.biofuel_status.impact_cwt + 
              factors.palm_oil_status.impact_cwt).toFixed(2)}/cwt
          </span>
        </div>
        <div className="text-xs text-text-tertiary mt-1 text-center">
          BEARISH SHORT-TERM → Wait for lower prices
        </div>
      </div>
    </div>
  )
}
