import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { EventDrivenUpsell } from '@/components/vegas/EventDrivenUpsell'
import { CustomerRelationshipMatrix } from '@/components/vegas/CustomerRelationshipMatrix'
import { EventVolumeMultipliers } from '@/components/vegas/EventVolumeMultipliers'
import { MarginProtectionAlerts } from '@/components/vegas/MarginProtectionAlerts'
import { SalesIntelligenceOverview } from '@/components/vegas/SalesIntelligenceOverview'
import { VegasHeatMap } from '@/components/vegas/VegasHeatMap'

export default function VegasIntelPage() {
  return (
    <div className="flex h-screen bg-background-primary">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Page Header */}
            <div className="mb-6">
              <h1 className="text-4xl font-light text-text-primary mb-2" style={{
                background: 'linear-gradient(135deg, #E0E0E3 0%, #9099a6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Vegas Intelligence & Market Rumors
              </h1>
              <p className="text-text-secondary text-sm">
                Event-driven sales intelligence and customer relationship analytics
              </p>
            </div>

            {/* Sales Intelligence Overview */}
            <SalesIntelligenceOverview />

            {/* Geographic Heat Map - Full Width */}
            <VegasHeatMap />

            {/* AI-Powered Event-Driven Oil Demand Forecasting - Full Width */}
            <EventDrivenUpsell />

            {/* Two Column Grid */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <CustomerRelationshipMatrix />
              <EventVolumeMultipliers />
            </div>

            {/* Margin Protection Alerts */}
            <MarginProtectionAlerts />
          </div>
        </main>
      </div>
    </div>
  )
}
