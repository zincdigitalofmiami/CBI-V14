import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { AdminUtilities } from '@/components/admin/AdminUtilities'

export default function AdminPage() {
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
                Quant Admin
              </h1>
              <p className="text-text-secondary text-sm">
                Data management and system configuration
              </p>
            </div>
            
            <AdminUtilities />
          </div>
        </main>
      </div>
    </div>
  )
}
