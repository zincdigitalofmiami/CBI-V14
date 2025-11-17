'use client'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import {
  BarChart3,
  Clock, DollarSign,
  Lock,
  Package,
  Target,
  TrendingUp
} from 'lucide-react'
import { useEffect, useState } from 'react'

interface TrumpPrediction {
  generated_at: string
  prediction: {
    most_likely_action: string
    probability: number
    timing: string
    triggers: string[]
    risk_level: string
  }
  expected_impact: {
    sp500_futures: string
    vix: string
    dollar_index: string
    commodities: string
    confidence: string
  }
  alternative_scenarios: Array<{
    action: string
    probability: number
    es_impact: string
  }>
  key_indicators: {
    posting_velocity_24h: number
    threat_level: number
    action_signals: number
    market_condition: string
  }
  recommendations: string[]
}

interface ZLImpact {
  generated_at: string
  current_zl_price: number
  primary_impact: {
    action: string
    impact_percent: number
    impact_direction: string
    confidence: number
    time_to_impact_hours: number
    current_price: number
    expected_price: number
    worst_case_price: number
    best_case_price: number
    price_range: string
    procurement_action: string
    procurement_urgency: string
    procurement_reasoning: string
    savings_opportunity: string
    historical_similar: {
      date: string
      context: string
      actual_move: string
      result: string
    }
  }
  procurement_alerts: Array<{
    level: string
    action: string
    probability: number
    message: string
    reasoning: string
    potential_savings: string
    time_window: string
    price_target: number
  }>
  procurement_summary: {
    recommendation: string
    urgency: string
    confidence: string
    expected_move: string
    price_target: number
    time_window: string
  }
  chris_language_summary: string
}

export default function LegislationPage() {
  const [trumpPrediction, setTrumpPrediction] = useState<TrumpPrediction | null>(null)
  const [zlImpact, setZLImpact] = useState<ZLImpact | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch Trump prediction
        const trumpResponse = await fetch('/api/trump_prediction.json')
        if (trumpResponse.ok) {
          const trumpData = await trumpResponse.json()
          setTrumpPrediction(trumpData)
        }

        // Fetch ZL impact
        const zlResponse = await fetch('/api/zl_impact.json')
        if (zlResponse.ok) {
          const zlData = await zlResponse.json()
          setZLImpact(zlData)
        }
      } catch (error) {
        console.error('Failed to fetch predictions:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(() => {
      fetchData()
      setLastUpdate(new Date())
    }, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [])

  const getRiskColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'EXTREME': return 'text-red-500'
      case 'HIGH': return 'text-orange-500'
      case 'MODERATE': return 'text-yellow-500'
      case 'LOW': return 'text-green-500'
      default: return 'text-gray-500'
    }
  }

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toUpperCase()) {
      case 'URGENT': return 'bg-red-500 text-white'
      case 'HIGH': return 'bg-orange-500 text-white'
      case 'MODERATE': return 'bg-yellow-500 text-black'
      case 'LOW': return 'bg-gray-500 text-white'
      default: return 'bg-gray-400 text-white'
    }
  }

  const getActionIcon = (action: string) => {
    if (action?.includes('tariff')) return '🎯'
    if (action?.includes('trade')) return '🤝'
    if (action?.includes('social')) return '📱'
    if (action?.includes('china')) return '🇨🇳'
    if (action?.includes('deal')) return '💼'
    if (action?.includes('reversal')) return '🔄'
    return '📊'
  }

  return (
    <div className="flex h-screen bg-background-primary">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-4xl font-light text-text-primary mb-2" style={{
                background: 'linear-gradient(135deg, #E0E0E3 0%, #9099a6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Policy & Regulatory Intelligence
              </h1>
              <p className="text-text-secondary text-sm">
                Trump action predictions and ZL (Soybean Oil) procurement impact analysis
              </p>
            </div>

            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary"></div>
              </div>
            ) : (
              <>
                {/* ZL Procurement Alert - TOP PRIORITY */}
                {zlImpact && (
                  <Card className="mb-6 p-6 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-yellow-500/30">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <Package className="w-8 h-8 text-yellow-500" />
                        <div>
                          <h2 className="text-xl font-bold text-text-primary">ZL Procurement Alert</h2>
                          <p className="text-sm text-text-secondary">Soybean Oil: ${zlImpact.current_zl_price.toFixed(2)}/cwt</p>
                        </div>
                      </div>
                      <Badge className={getUrgencyColor(zlImpact.procurement_summary.urgency)}>
                        {zlImpact.procurement_summary.urgency}
                      </Badge>
                    </div>

                    {/* Chris's Language Summary - BIG AND BOLD */}
                    <div className="bg-background-primary/50 rounded-lg p-4 mb-4">
                      <p className="text-lg font-semibold text-text-primary">
                        {zlImpact.chris_language_summary}
                      </p>
                    </div>

                    {/* Key Procurement Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-background-secondary rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Target className="w-4 h-4 text-text-tertiary" />
                          <span className="text-xs text-text-tertiary">Action</span>
                        </div>
                        <p className="text-lg font-bold text-text-primary">
                          {zlImpact.procurement_summary.recommendation}
                        </p>
                      </div>
                      <div className="bg-background-secondary rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <TrendingUp className="w-4 h-4 text-text-tertiary" />
                          <span className="text-xs text-text-tertiary">Expected Move</span>
                        </div>
                        <p className={`text-lg font-bold ${zlImpact.primary_impact.impact_direction === 'DOWN' ? 'text-red-500' : 'text-green-500'
                          }`}>
                          {zlImpact.procurement_summary.expected_move}
                        </p>
                      </div>
                      <div className="bg-background-secondary rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <DollarSign className="w-4 h-4 text-text-tertiary" />
                          <span className="text-xs text-text-tertiary">Target Price</span>
                        </div>
                        <p className="text-lg font-bold text-text-primary">
                          ${zlImpact.procurement_summary.price_target.toFixed(2)}
                        </p>
                      </div>
                      <div className="bg-background-secondary rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Clock className="w-4 h-4 text-text-tertiary" />
                          <span className="text-xs text-text-tertiary">Time Window</span>
                        </div>
                        <p className="text-lg font-bold text-text-primary">
                          {zlImpact.procurement_summary.time_window}
                        </p>
                      </div>
                    </div>

                    {/* Historical Context */}
                    {zlImpact.primary_impact.historical_similar && (
                      <div className="mt-4 p-3 bg-background-secondary/50 rounded-lg">
                        <p className="text-xs text-text-tertiary mb-1">Historical Pattern</p>
                        <p className="text-sm text-text-primary">
                          {zlImpact.primary_impact.historical_similar.context} ({zlImpact.primary_impact.historical_similar.date}):
                          <span className="font-semibold ml-2">{zlImpact.primary_impact.historical_similar.result}</span>
                        </p>
                      </div>
                    )}
                  </Card>
                )}

                {/* Trump Prediction and ZL Correlation Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Trump Prediction Card */}
                  {trumpPrediction && (
                    <Card className="lg:col-span-2 p-6 bg-background-secondary border-border-primary">
                      <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold text-text-primary">Trump Action Prediction</h2>
                        <Badge className={getRiskColor(trumpPrediction.prediction.risk_level)}>
                          {trumpPrediction.prediction.risk_level} RISK
                        </Badge>
                      </div>

                      <div className="space-y-4">
                        {/* Most Likely Action */}
                        <div className="bg-background-primary rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-2xl">{getActionIcon(trumpPrediction.prediction.most_likely_action)}</span>
                              <div>
                                <h3 className="text-lg font-medium text-text-primary capitalize">
                                  {trumpPrediction.prediction.most_likely_action.replace(/_/g, ' ')}
                                </h3>
                                <p className="text-sm text-text-secondary">
                                  Timing: {trumpPrediction.prediction.timing}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-2xl font-bold text-accent-primary">
                                {(trumpPrediction.prediction.probability * 100).toFixed(0)}%
                              </div>
                              <div className="text-xs text-text-tertiary">Probability</div>
                            </div>
                          </div>

                          {trumpPrediction.prediction.triggers.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-border-primary">
                              <p className="text-xs text-text-tertiary mb-1">Triggers:</p>
                              <div className="flex flex-wrap gap-2">
                                {trumpPrediction.prediction.triggers.map((trigger, i) => (
                                  <Badge key={i} variant="secondary" className="text-xs">
                                    {trigger}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* ZL Impact for this action */}
                          {zlImpact && (
                            <div className="mt-3 pt-3 border-t border-border-primary bg-yellow-500/5 -m-2 p-2 rounded">
                              <p className="text-xs text-text-tertiary mb-1">ZL Impact:</p>
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-text-primary">
                                  Expected: {zlImpact.primary_impact.impact_direction} {Math.abs(zlImpact.primary_impact.impact_percent).toFixed(1)}%
                                </span>
                                <span className="text-sm text-text-secondary">
                                  ${zlImpact.primary_impact.expected_price.toFixed(2)}/cwt
                                </span>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Alternative Scenarios */}
                        {trumpPrediction.alternative_scenarios.length > 0 && (
                          <div className="bg-background-primary rounded-lg p-4">
                            <h3 className="text-sm font-medium text-text-secondary mb-3">Alternative Scenarios</h3>
                            <div className="space-y-2">
                              {trumpPrediction.alternative_scenarios.map((scenario, i) => (
                                <div key={i} className="flex items-center justify-between py-2 border-b border-border-primary last:border-0">
                                  <div className="flex items-center gap-2">
                                    <span>{getActionIcon(scenario.action)}</span>
                                    <span className="text-sm text-text-primary capitalize">
                                      {scenario.action.replace(/_/g, ' ')}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <Badge variant="outline" className="text-xs">
                                      {(scenario.probability * 100).toFixed(0)}%
                                    </Badge>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </Card>
                  )}

                  {/* Side Panel - ZL Alerts & Trump Indicators */}
                  <div className="space-y-6">
                    {/* Procurement Alerts */}
                    {zlImpact && zlImpact.procurement_alerts.length > 0 && (
                      <Card className="p-6 bg-background-secondary border-border-primary">
                        <div className="flex items-center gap-2 mb-4">
                          <Lock className="w-4 h-4 text-yellow-500" />
                          <h3 className="text-sm font-medium text-text-secondary">Procurement Alerts</h3>
                        </div>
                        <div className="space-y-3">
                          {zlImpact.procurement_alerts.slice(0, 3).map((alert, i) => (
                            <div key={i} className="p-3 rounded-lg bg-background-primary">
                              <div className="flex items-center justify-between mb-1">
                                <Badge className={getUrgencyColor(alert.level)} size="sm">
                                  {alert.level}
                                </Badge>
                                <span className="text-xs text-text-tertiary">
                                  {(alert.probability * 100).toFixed(0)}% likely
                                </span>
                              </div>
                              <p className="text-xs font-medium text-text-primary mt-2">
                                {alert.message}
                              </p>
                              <p className="text-xs text-text-secondary mt-1">
                                {alert.reasoning}
                              </p>
                              <div className="flex items-center justify-between mt-2 pt-2 border-t border-border-primary">
                                <span className="text-xs text-green-500">
                                  {alert.potential_savings}
                                </span>
                                <span className="text-xs text-text-tertiary">
                                  {alert.time_window}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </Card>
                    )}

                    {/* Trump Key Indicators */}
                    {trumpPrediction && (
                      <Card className="p-6 bg-background-secondary border-border-primary">
                        <h3 className="text-sm font-medium text-text-secondary mb-4">Trump Activity Indicators</h3>
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs text-text-tertiary">Posting Velocity (24h)</span>
                              <span className="text-sm font-medium text-text-primary">
                                {trumpPrediction.key_indicators.posting_velocity_24h}
                              </span>
                            </div>
                            <div className="w-full bg-background-primary rounded-full h-2">
                              <div
                                className="bg-accent-primary h-2 rounded-full"
                                style={{ width: `${Math.min(trumpPrediction.key_indicators.posting_velocity_24h * 10, 100)}%` }}
                              />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs text-text-tertiary">Threat Level</span>
                              <span className="text-sm font-medium text-text-primary">
                                {trumpPrediction.key_indicators.threat_level}
                              </span>
                            </div>
                            <div className="w-full bg-background-primary rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${trumpPrediction.key_indicators.threat_level > 10 ? 'bg-red-500' : 'bg-yellow-500'
                                  }`}
                                style={{ width: `${Math.min(trumpPrediction.key_indicators.threat_level * 5, 100)}%` }}
                              />
                            </div>
                          </div>
                          <div className="pt-2 mt-2 border-t border-border-primary">
                            <div className="flex justify-between items-center">
                              <span className="text-xs text-text-tertiary">Market Condition</span>
                              <Badge variant={trumpPrediction.key_indicators.market_condition === 'Risk-off' ? 'destructive' : 'default'}>
                                {trumpPrediction.key_indicators.market_condition}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </Card>
                    )}

                    {/* Last Update */}
                    <div className="text-xs text-text-tertiary text-center">
                      Last updated: {lastUpdate.toLocaleTimeString()}
                    </div>
                  </div>
                </div>

                {/* Trump → ZL Correlation Matrix */}
                {zlImpact && (
                  <Card className="mt-6 p-6 bg-background-secondary border-border-primary">
                    <div className="flex items-center gap-2 mb-4">
                      <BarChart3 className="w-5 h-5 text-purple-500" />
                      <h3 className="text-lg font-medium text-text-primary">Trump Action → ZL Impact Correlations</h3>
                    </div>
                    <div className="text-xs text-text-secondary mb-4">
                      Historical correlations between Trump actions and soybean oil price movements
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-border-primary">
                            <th className="text-left text-xs text-text-tertiary pb-2">Action Type</th>
                            <th className="text-center text-xs text-text-tertiary pb-2">Avg Impact</th>
                            <th className="text-center text-xs text-text-tertiary pb-2">Range</th>
                            <th className="text-center text-xs text-text-tertiary pb-2">Timing</th>
                            <th className="text-center text-xs text-text-tertiary pb-2">Reliability</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr className="border-b border-border-primary/50">
                            <td className="py-2 text-sm text-text-primary">Tariff Announcement</td>
                            <td className="py-2 text-center text-sm font-medium text-red-500">-2.5%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">-4.5% to -1.5%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">48 hours</td>
                            <td className="py-2 text-center"><Badge variant="default" size="sm">HIGH</Badge></td>
                          </tr>
                          <tr className="border-b border-border-primary/50">
                            <td className="py-2 text-sm text-text-primary">China Threat</td>
                            <td className="py-2 text-center text-sm font-medium text-red-500">-3.0%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">-5.0% to -1.5%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">24 hours</td>
                            <td className="py-2 text-center"><Badge variant="default" size="sm">HIGH</Badge></td>
                          </tr>
                          <tr className="border-b border-border-primary/50">
                            <td className="py-2 text-sm text-text-primary">Deal Making</td>
                            <td className="py-2 text-center text-sm font-medium text-green-500">+2.2%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">+1.0% to +3.5%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">96 hours</td>
                            <td className="py-2 text-center"><Badge variant="secondary" size="sm">MEDIUM</Badge></td>
                          </tr>
                          <tr className="border-b border-border-primary/50">
                            <td className="py-2 text-sm text-text-primary">Policy Reversal</td>
                            <td className="py-2 text-center text-sm font-medium text-green-500">+2.0%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">+0.5% to +4.0%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">48 hours</td>
                            <td className="py-2 text-center"><Badge variant="secondary" size="sm">MEDIUM</Badge></td>
                          </tr>
                          <tr className="border-b border-border-primary/50">
                            <td className="py-2 text-sm text-text-primary">Trade Negotiation</td>
                            <td className="py-2 text-center text-sm font-medium text-green-500">+1.5%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">-0.5% to +3.5%</td>
                            <td className="py-2 text-center text-xs text-text-secondary">72 hours</td>
                            <td className="py-2 text-center"><Badge variant="secondary" size="sm">MEDIUM</Badge></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </Card>
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}