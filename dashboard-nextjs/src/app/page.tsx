import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'

export default function DashboardPage() {
  return (
    <div className="flex h-screen bg-background-primary">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />
        
        {/* Dashboard Content - Being Rebuilt */}
        <main className="flex-1 overflow-auto p-6">
          <div className="text-center py-12">
            <h1 className="text-2xl font-semibold text-text-primary mb-4">
              Dashboard Under Construction
            </h1>
            <p className="text-text-secondary">
              Dashboard is being completely rebuilt
            </p>
          </div>
        </main>
      </div>
    </div>
  )
}
