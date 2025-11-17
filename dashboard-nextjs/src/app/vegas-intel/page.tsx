'use client'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { AlertCircle, Calendar, Clock, DollarSign, MapPin, TrendingUp, Users } from 'lucide-react'
import { useEffect, useState } from 'react'

interface VegasEvent {
    event_name: string
    venue: string
    date: string
    expected_attendance: number
    volume_multiplier: number
    oil_demand_estimate: number
    priority: 'HIGH' | 'MEDIUM' | 'LOW'
    upsell_opportunity: string
}

interface RestaurantData {
    name: string
    location: string
    current_volume: number
    event_proximity: number
    upsell_potential: number
    last_contact: string
}

interface VegasIntel {
    generated_at: string
    upcoming_events: VegasEvent[]
    top_restaurants: RestaurantData[]
    volume_forecast: {
        next_7_days: number
        next_30_days: number
        peak_day: string
        peak_volume: number
    }
    sales_opportunities: Array<{
        restaurant: string
        reason: string
        action: string
        urgency: string
    }>
    market_insights: {
        total_restaurants: number
        active_casinos: number
        avg_daily_volume: number
        growth_trend: string
    }
}

export default function VegasIntelPage() {
    const [intel, setIntel] = useState<VegasIntel | null>(null)
    const [loading, setLoading] = useState(true)
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

    useEffect(() => {
        const fetchIntel = async () => {
            try {
                const response = await fetch('/api/vegas_intel.json')
                if (response.ok) {
                    const data = await response.json()
                    setIntel(data)
                    setLastUpdate(new Date(data.generated_at))
                } else {
                    console.error('Failed to fetch Vegas Intel:', response.statusText)
                }
            } catch (error) {
                console.error('Error fetching Vegas Intel:', error)
            } finally {
                setLoading(false)
            }
        }
        fetchIntel()
        const interval = setInterval(fetchIntel, 300000) // Refresh every 5 minutes
        return () => clearInterval(interval)
    }, [])

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'HIGH': return 'bg-red-500'
            case 'MEDIUM': return 'bg-yellow-500'
            case 'LOW': return 'bg-green-500'
            default: return 'bg-gray-500'
        }
    }

    const getUrgencyColor = (urgency: string) => {
        switch (urgency.toLowerCase()) {
            case 'urgent': return 'text-red-600 dark:text-red-400'
            case 'high': return 'text-orange-600 dark:text-orange-400'
            case 'medium': return 'text-yellow-600 dark:text-yellow-400'
            default: return 'text-green-600 dark:text-green-400'
        }
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
                                Vegas Intel
                            </h1>
                            <p className="text-text-secondary text-sm">
                                Sales intelligence for restaurant upsell opportunities based on casino events
                            </p>
                            {intel && (
                                <p className="text-text-tertiary text-xs mt-1">
                                    Last Updated: {lastUpdate.toLocaleString()}
                                </p>
                            )}
                        </div>

                        {loading ? (
                            <div className="text-text-secondary text-center py-10">Loading Vegas Intel...</div>
                        ) : intel ? (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                {/* Market Overview */}
                                <Card className="lg:col-span-3 p-6 bg-background-secondary border border-border-primary">
                                    <h2 className="text-2xl font-semibold text-text-primary mb-4">Market Overview</h2>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div>
                                            <p className="text-text-tertiary text-sm">Total Restaurants</p>
                                            <p className="text-2xl font-bold text-text-primary">{intel.market_insights.total_restaurants}</p>
                                        </div>
                                        <div>
                                            <p className="text-text-tertiary text-sm">Active Casinos</p>
                                            <p className="text-2xl font-bold text-text-primary">{intel.market_insights.active_casinos}</p>
                                        </div>
                                        <div>
                                            <p className="text-text-tertiary text-sm">Avg Daily Volume</p>
                                            <p className="text-2xl font-bold text-text-primary">{intel.market_insights.avg_daily_volume.toLocaleString()} gal</p>
                                        </div>
                                        <div>
                                            <p className="text-text-tertiary text-sm">Growth Trend</p>
                                            <p className="text-2xl font-bold text-text-primary flex items-center">
                                                <TrendingUp className="w-5 h-5 mr-1 text-green-500" />
                                                {intel.market_insights.growth_trend}
                                            </p>
                                        </div>
                                    </div>
                                </Card>

                                {/* Volume Forecast */}
                                <Card className="lg:col-span-2 p-6 bg-background-secondary border border-border-primary">
                                    <h2 className="text-2xl font-semibold text-text-primary mb-4 flex items-center">
                                        <DollarSign className="mr-2 text-yellow-500" /> Volume Forecast
                                    </h2>
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-background-tertiary p-4 rounded-md border border-border-secondary">
                                                <p className="text-text-tertiary text-sm">Next 7 Days</p>
                                                <p className="text-2xl font-bold text-text-primary">{intel.volume_forecast.next_7_days.toLocaleString()} gal</p>
                                            </div>
                                            <div className="bg-background-tertiary p-4 rounded-md border border-border-secondary">
                                                <p className="text-text-tertiary text-sm">Next 30 Days</p>
                                                <p className="text-2xl font-bold text-text-primary">{intel.volume_forecast.next_30_days.toLocaleString()} gal</p>
                                            </div>
                                        </div>
                                        <div className="bg-yellow-100 dark:bg-yellow-900/20 p-4 rounded-md border border-yellow-300 dark:border-yellow-700">
                                            <p className="text-yellow-700 dark:text-yellow-300 font-bold flex items-center">
                                                <AlertCircle className="w-5 h-5 mr-2" /> Peak Day Alert
                                            </p>
                                            <p className="text-yellow-600 dark:text-yellow-400 mt-1">
                                                <strong>{intel.volume_forecast.peak_day}</strong>: Expected peak volume of <strong>{intel.volume_forecast.peak_volume.toLocaleString()} gal</strong>
                                            </p>
                                            <p className="text-yellow-600 dark:text-yellow-400 text-sm mt-1">
                                                Prepare for increased demand - contact restaurants in advance
                                            </p>
                                        </div>
                                    </div>
                                </Card>

                                {/* Top Restaurants */}
                                <Card className="p-6 bg-background-secondary border border-border-primary">
                                    <h2 className="text-2xl font-semibold text-text-primary mb-4 flex items-center">
                                        <Users className="mr-2 text-blue-500" /> Top Opportunities
                                    </h2>
                                    <div className="space-y-3">
                                        {intel.top_restaurants.slice(0, 5).map((restaurant, i) => (
                                            <div key={i} className="bg-background-tertiary p-3 rounded-md border border-border-secondary">
                                                <p className="font-medium text-text-primary">{restaurant.name}</p>
                                                <p className="text-text-secondary text-sm flex items-center mt-1">
                                                    <MapPin className="w-3 h-3 mr-1" /> {restaurant.location}
                                                </p>
                                                <div className="mt-2 flex justify-between items-center">
                                                    <span className="text-text-tertiary text-xs">Upsell Potential</span>
                                                    <Badge className="bg-green-500 text-white">
                                                        +{restaurant.upsell_potential}%
                                                    </Badge>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </Card>

                                {/* Upcoming Events */}
                                <Card className="lg:col-span-2 p-6 bg-background-secondary border border-border-primary">
                                    <h2 className="text-2xl font-semibold text-text-primary mb-4 flex items-center">
                                        <Calendar className="mr-2 text-purple-500" /> Upcoming Events
                                    </h2>
                                    <div className="space-y-3">
                                        {intel.upcoming_events.map((event, i) => (
                                            <div key={i} className="bg-background-tertiary p-4 rounded-md border border-border-secondary">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div>
                                                        <p className="font-bold text-text-primary">{event.event_name}</p>
                                                        <p className="text-text-secondary text-sm flex items-center mt-1">
                                                            <MapPin className="w-3 h-3 mr-1" /> {event.venue}
                                                        </p>
                                                        <p className="text-text-tertiary text-xs flex items-center mt-1">
                                                            <Clock className="w-3 h-3 mr-1" /> {new Date(event.date).toLocaleDateString()}
                                                        </p>
                                                    </div>
                                                    <Badge className={`${getPriorityColor(event.priority)} text-white`}>
                                                        {event.priority}
                                                    </Badge>
                                                </div>
                                                <div className="grid grid-cols-3 gap-2 mt-3 text-sm">
                                                    <div>
                                                        <p className="text-text-tertiary">Attendance</p>
                                                        <p className="font-medium text-text-primary">{event.expected_attendance.toLocaleString()}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-text-tertiary">Volume Multiplier</p>
                                                        <p className="font-medium text-text-primary">{event.volume_multiplier}x</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-text-tertiary">Oil Demand</p>
                                                        <p className="font-medium text-text-primary">{event.oil_demand_estimate.toLocaleString()} gal</p>
                                                    </div>
                                                </div>
                                                <div className="mt-3 bg-blue-100 dark:bg-blue-900/20 p-2 rounded border border-blue-300 dark:border-blue-700">
                                                    <p className="text-blue-700 dark:text-blue-300 text-sm font-medium">Upsell Opportunity:</p>
                                                    <p className="text-blue-600 dark:text-blue-400 text-sm">{event.upsell_opportunity}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </Card>

                                {/* Sales Opportunities */}
                                <Card className="p-6 bg-background-secondary border border-border-primary">
                                    <h2 className="text-2xl font-semibold text-text-primary mb-4 flex items-center">
                                        <AlertCircle className="mr-2 text-orange-500" /> Action Items
                                    </h2>
                                    <div className="space-y-3">
                                        {intel.sales_opportunities.map((opp, i) => (
                                            <div key={i} className="bg-background-tertiary p-3 rounded-md border border-border-secondary">
                                                <p className="font-medium text-text-primary">{opp.restaurant}</p>
                                                <p className="text-text-secondary text-sm mt-1">{opp.reason}</p>
                                                <p className={`text-sm font-medium mt-2 ${getUrgencyColor(opp.urgency)}`}>
                                                    {opp.urgency.toUpperCase()}: {opp.action}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </Card>
                            </div>
                        ) : (
                            <div className="bg-background-secondary rounded-lg border border-border-primary p-8 text-center">
                                <div className="text-text-tertiary mb-4">
                                    <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                </div>
                                <h3 className="text-xl font-medium text-text-primary mb-2">Vegas Intel Coming Soon</h3>
                                <p className="text-text-secondary max-w-md mx-auto">
                                    Sales intelligence dashboard for restaurant upsell opportunities based on casino events and customer data.
                                </p>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    )
}
