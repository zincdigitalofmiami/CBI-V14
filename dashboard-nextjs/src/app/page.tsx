import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { ForwardCurve } from '@/components/dashboard/ForwardCurve'
import { ForecastCards } from '@/components/dashboard/ForecastCards'
import { BreakingNews } from '@/components/dashboard/BreakingNews'
import { ProcurementSignal } from '@/components/dashboard/ProcurementSignal'
import { CurrentPrice } from '@/components/dashboard/CurrentPrice'
import { ChrisFourFactors } from '@/components/dashboard/ChrisFourFactors'
import { MarketDrivers } from '@/components/dashboard/MarketDrivers'
import { BigEightSignals } from '@/components/dashboard/BigEightSignals'
import PriceDrivers from '@/components/dashboard/PriceDrivers'
import ProcurementOptimizer from '@/components/dashboard/ProcurementOptimizer'

export default function DashboardPage() {
  return (
    <div className="flex h-screen bg-background-primary">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />
        
        {/* Dashboard Content */}
        <main className="flex-1 overflow-auto p-6 space-y-6">
          {/* Page Header */}
          <div className="mb-4">
            <h1 className="text-4xl font-light text-text-primary mb-2" style={{
              background: 'linear-gradient(135deg, #E0E0E3 0%, #9099a6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Soybean Oil Futures Intelligence
            </h1>
            <p className="text-text-secondary text-sm">
              Real-time market signals and institutional-grade forecasting for procurement decisions
            </p>
          </div>
          
          {/* ROW 1: MAIN FORWARD CURVE (FULL WIDTH - Most Important!) */}
          <ForwardCurve />
          
          {/* ROW 2: 4 MINI FORECAST CHARTS (Equal width) */}
          <ForecastCards />
          
          {/* ROW 3: BREAKING NEWS + AI ANALYSIS (FULL WIDTH) */}
          <BreakingNews />
          
          {/* ROW 4: VIX METER + PRICE DRIVERS (Side by side, 40%/60%) */}
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
            <div className="xl:col-span-2">
              <ProcurementSignal />
            </div>
            <div className="xl:col-span-3">
              <MarketDrivers />
            </div>
          </div>
          
          {/* ROW 5: CHRIS'S 4 CRITICAL FACTORS (Equal cards) */}
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div>
              <CurrentPrice />
            </div>
            <div className="xl:col-span-3">
              <ChrisFourFactors />
            </div>
          </div>
          
          {/* ROW 6: WHY PRICES ARE MOVING - AI INTELLIGENCE (Full width) */}
          <PriceDrivers />
          
          {/* ROW 7: BIG 8 SIGNALS (Full width for all 8) */}
          <BigEightSignals />
          
          {/* ROW 8: PROCUREMENT TIMING OPTIMIZER WITH VIX (Full width) */}
          <ProcurementOptimizer />
        </main>
      </div>
    </div>
  )
}
