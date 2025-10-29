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
              <h1 className="text-3xl font-light text-text-primary mb-2">
                Admin Console
              </h1>
              <p className="text-text-secondary">
                Data uploading, system utilities, and platform management for Chris and team
              </p>
            </div>
            
            <AdminUtilities />
          </div>
        </main>
      </div>
    </div>
  )
}
