import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { ProcurementSignal } from '@/components/dashboard/ProcurementSignal'
import { ForecastCards } from '@/components/dashboard/ForecastCards'
import { ChrisFourFactors } from '@/components/dashboard/ChrisFourFactors'
import { CurrentPrice } from '@/components/dashboard/CurrentPrice'
import { MarketDrivers } from '@/components/dashboard/MarketDrivers'
import { BigEightSignals } from '@/components/dashboard/BigEightSignals'

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
          {/* Chris's Procurement Decision Hub */}
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-2">
              <ProcurementSignal />
            </div>
            <div>
              <CurrentPrice />
            </div>
            <div>
              <ChrisFourFactors />
            </div>
          </div>
          
          {/* Model Forecasts - Chris's Timeline */}
          <ForecastCards />
          
          {/* AI-Driven Market Intelligence - Real-Time Data */}
          <MarketDrivers />
          
          {/* Big 8 Signals - Live BigQuery Data */}
          <BigEightSignals />
        </main>
      </div>
    </div>
  )
}
