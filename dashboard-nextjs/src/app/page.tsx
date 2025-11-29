import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { ZLChart } from '@/components/charts/ZLChart'

export default function DashboardPage() {
  return (
    <div className="flex h-screen bg-background-primary">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />
        
        {/* Dashboard Content - Full Width Chart */}
        <main className="flex-1 overflow-hidden">
          <ZLChart />
        </main>
      </div>
    </div>
  )
}
