'use client'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Activity, AlertTriangle, BarChart3, Shield, Target, TrendingDown, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'

interface ESPrediction {
    timestamp: string
    horizon: string
    current_price: number
    prediction: {
        direction: string
        magnitude: number
        target_price: number
        expected_return: string
        confidence: string
    }
    model_predictions: {
        [key: string]: string
    }
    key_drivers: string[]
    support_resistance: {
        immediate_resistance: number
        immediate_support: number
        major_resistance: number
        major_support: number
        pivot_point: number
        r1: number
        s1: number
    }
    risk_metrics: {
        annualized_volatility: string
        value_at_risk_95: string
        expected_shortfall: string
        suggested_stop_loss: string
        risk_reward_ratio: string
    }
    trading_signals: string[]
}

export default function ESPredictionPage() {
    const [esPrediction, setESPrediction] = useState<ESPrediction | null>(null)
    const [loading, setLoading] = useState(true)
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

    useEffect(() => {
        const fetchPrediction = async () => {
            try {
                const response = await fetch('/api/es_prediction.json')
                if (response.ok) {
                    const data = await response.json()
                    setESPrediction(data)
                }
            } catch (error) {
                console.error('Failed to fetch ES prediction:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchPrediction()
        const interval = setInterval(() => {
            fetchPrediction()
            setLastUpdate(new Date())
        }, 30000) // Update every 30 seconds

        return () => clearInterval(interval)
    }, [])

    const getDirectionColor = (direction: string) => {
        return direction === 'UP' ? 'text-green-500' : 'text-red-500'
    }

    const getSignalIcon = (signal: string) => {
        if (signal.includes('BUY')) return '📈'
        if (signal.includes('SELL')) return '📉'
        if (signal.includes('NEUTRAL')) return '⏸️'
        if (signal.includes('WARNING') || signal.includes('⚠️')) return '⚠️'
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
                            <div className="flex items-center justify-between">
                                <div>
                                    <h1 className="text-4xl font-light text-text-primary mb-2" style={{
                                        background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
                                        WebkitBackgroundClip: 'text',
                                        WebkitTextFillColor: 'transparent',
                                        backgroundClip: 'text'
                                    }}>
                                        ES Futures Prediction System
                                    </h1>
                                    <p className="text-text-secondary text-sm">
                                        Advanced S&P 500 futures analysis with machine learning
                                    </p>
                                </div>
                                <Badge variant="destructive" className="animate-pulse">
                                    PRIVATE - CONFIDENTIAL
                                </Badge>
                            </div>
                        </div>

                        {loading ? (
                            <div className="flex items-center justify-center h-64">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary"></div>
                            </div>
                        ) : esPrediction ? (
                            <div className="space-y-6">
                                {/* Main Prediction Panel */}
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                    <Card className="lg:col-span-2 p-6 bg-background-secondary border-border-primary">
                                        <div className="flex items-center justify-between mb-6">
                                            <h2 className="text-xl font-semibold text-text-primary">Market Prediction</h2>
                                            <Badge variant="outline">{esPrediction.horizon}</Badge>
                                        </div>

                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-4">
                                                <div>
                                                    <p className="text-sm text-text-tertiary mb-1">Current Price</p>
                                                    <p className="text-2xl font-bold text-text-primary">
                                                        {esPrediction.current_price.toFixed(2)}
                                                    </p>
                                                </div>
                                                <div>
                                                    <p className="text-sm text-text-tertiary mb-1">Target Price</p>
                                                    <div className="flex items-center gap-2">
                                                        <p className="text-2xl font-bold text-text-primary">
                                                            {esPrediction.prediction.target_price.toFixed(2)}
                                                        </p>
                                                        {esPrediction.prediction.direction === 'UP' ?
                                                            <TrendingUp className="w-5 h-5 text-green-500" /> :
                                                            <TrendingDown className="w-5 h-5 text-red-500" />
                                                        }
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-4">
                                                <div>
                                                    <p className="text-sm text-text-tertiary mb-1">Expected Return</p>
                                                    <p className={`text-2xl font-bold ${getDirectionColor(esPrediction.prediction.direction)}`}>
                                                        {esPrediction.prediction.expected_return}
                                                    </p>
                                                </div>
                                                <div>
                                                    <p className="text-sm text-text-tertiary mb-1">Confidence</p>
                                                    <div className="flex items-center gap-2">
                                                        <p className="text-2xl font-bold text-text-primary">
                                                            {esPrediction.prediction.confidence}
                                                        </p>
                                                        <div className="flex-1">
                                                            <div className="w-full bg-background-primary rounded-full h-2">
                                                                <div
                                                                    className="bg-accent-primary h-2 rounded-full"
                                                                    style={{ width: esPrediction.prediction.confidence }}
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Model Predictions */}
                                        <div className="mt-6 pt-6 border-t border-border-primary">
                                            <h3 className="text-sm font-medium text-text-secondary mb-3">Model Ensemble</h3>
                                            <div className="grid grid-cols-3 gap-4">
                                                {Object.entries(esPrediction.model_predictions).map(([model, prediction]) => (
                                                    <div key={model} className="text-center">
                                                        <p className="text-xs text-text-tertiary capitalize mb-1">{model.replace('_', ' ')}</p>
                                                        <p className={`text-lg font-semibold ${prediction.includes('+') ? 'text-green-500' :
                                                                prediction.includes('-') ? 'text-red-500' : 'text-text-primary'
                                                            }`}>
                                                            {prediction}
                                                        </p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </Card>

                                    {/* Risk Metrics */}
                                    <Card className="p-6 bg-background-secondary border-border-primary">
                                        <div className="flex items-center gap-2 mb-4">
                                            <Shield className="w-5 h-5 text-blue-500" />
                                            <h3 className="text-lg font-medium text-text-primary">Risk Analysis</h3>
                                        </div>
                                        <div className="space-y-3">
                                            <div>
                                                <p className="text-xs text-text-tertiary">Volatility (Annual)</p>
                                                <p className="text-lg font-semibold text-text-primary">
                                                    {esPrediction.risk_metrics.annualized_volatility}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-text-tertiary">Value at Risk (95%)</p>
                                                <p className="text-lg font-semibold text-red-500">
                                                    {esPrediction.risk_metrics.value_at_risk_95}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-text-tertiary">Expected Shortfall</p>
                                                <p className="text-lg font-semibold text-red-500">
                                                    {esPrediction.risk_metrics.expected_shortfall}
                                                </p>
                                            </div>
                                            <div className="pt-3 mt-3 border-t border-border-primary">
                                                <p className="text-xs text-text-tertiary">Suggested Stop Loss</p>
                                                <p className="text-lg font-semibold text-orange-500">
                                                    {esPrediction.risk_metrics.suggested_stop_loss}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-text-tertiary">Risk/Reward Ratio</p>
                                                <p className="text-lg font-semibold text-text-primary">
                                                    {esPrediction.risk_metrics.risk_reward_ratio}
                                                </p>
                                            </div>
                                        </div>
                                    </Card>
                                </div>

                                {/* Support & Resistance Levels */}
                                <Card className="p-6 bg-background-secondary border-border-primary">
                                    <div className="flex items-center gap-2 mb-4">
                                        <BarChart3 className="w-5 h-5 text-purple-500" />
                                        <h3 className="text-lg font-medium text-text-primary">Support & Resistance Levels</h3>
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                                        <div className="text-center">
                                            <p className="text-xs text-text-tertiary mb-1">Major Support</p>
                                            <p className="text-lg font-bold text-red-500">
                                                {esPrediction.support_resistance.major_support.toFixed(2)}
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-xs text-text-tertiary mb-1">Support (S1)</p>
                                            <p className="text-lg font-semibold text-red-400">
                                                {esPrediction.support_resistance.s1.toFixed(2)}
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-xs text-text-tertiary mb-1">Immediate Support</p>
                                            <p className="text-lg font-medium text-orange-500">
                                                {esPrediction.support_resistance.immediate_support.toFixed(2)}
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-xs text-text-tertiary mb-1">Pivot Point</p>
                                            <p className="text-lg font-bold text-blue-500">
                                                {esPrediction.support_resistance.pivot_point.toFixed(2)}
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-xs text-text-tertiary mb-1">Immediate Resistance</p>
                                            <p className="text-lg font-medium text-green-400">
                                                {esPrediction.support_resistance.immediate_resistance.toFixed(2)}
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-xs text-text-tertiary mb-1">Resistance (R1)</p>
                                            <p className="text-lg font-semibold text-green-500">
                                                {esPrediction.support_resistance.r1.toFixed(2)}
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <p className="text-xs text-text-tertiary mb-1">Major Resistance</p>
                                            <p className="text-lg font-bold text-green-600">
                                                {esPrediction.support_resistance.major_resistance.toFixed(2)}
                                            </p>
                                        </div>
                                    </div>
                                </Card>

                                {/* Key Drivers and Trading Signals */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    {/* Key Drivers */}
                                    <Card className="p-6 bg-background-secondary border-border-primary">
                                        <div className="flex items-center gap-2 mb-4">
                                            <Activity className="w-5 h-5 text-yellow-500" />
                                            <h3 className="text-lg font-medium text-text-primary">Key Market Drivers</h3>
                                        </div>
                                        <div className="space-y-2">
                                            {esPrediction.key_drivers.map((driver, i) => (
                                                <div key={i} className="flex items-center gap-2">
                                                    <div className="w-2 h-2 rounded-full bg-accent-primary flex-shrink-0" />
                                                    <p className="text-sm text-text-primary">{driver}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </Card>

                                    {/* Trading Signals */}
                                    <Card className="p-6 bg-background-secondary border-border-primary">
                                        <div className="flex items-center gap-2 mb-4">
                                            <Target className="w-5 h-5 text-green-500" />
                                            <h3 className="text-lg font-medium text-text-primary">Trading Signals</h3>
                                        </div>
                                        <div className="space-y-3">
                                            {esPrediction.trading_signals.map((signal, i) => (
                                                <div key={i} className={`p-3 rounded-lg ${signal.includes('BUY') ? 'bg-green-500/10 border border-green-500/20' :
                                                        signal.includes('SELL') ? 'bg-red-500/10 border border-red-500/20' :
                                                            signal.includes('WARNING') || signal.includes('⚠️') ? 'bg-yellow-500/10 border border-yellow-500/20' :
                                                                'bg-background-primary'
                                                    }`}>
                                                    <div className="flex items-start gap-2">
                                                        <span className="text-lg">{getSignalIcon(signal)}</span>
                                                        <p className="text-sm text-text-primary flex-1">{signal.replace(/[📈📉⏸️⚠️]/g, '').trim()}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </Card>
                                </div>

                                {/* Footer */}
                                <div className="text-center text-xs text-text-tertiary mt-6">
                                    <p>Last updated: {lastUpdate.toLocaleTimeString()}</p>
                                    <p className="mt-1">Generated: {new Date(esPrediction.timestamp).toLocaleString()}</p>
                                </div>
                            </div>
                        ) : (
                            <Card className="p-8 text-center bg-background-secondary border-border-primary">
                                <AlertTriangle className="w-12 h-12 text-text-tertiary mx-auto mb-4" />
                                <p className="text-text-secondary">No ES prediction data available</p>
                            </Card>
                        )}
                    </div>
                </main>
            </div>
        </div>
    )
}
