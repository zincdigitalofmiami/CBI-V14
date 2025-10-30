import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'

export default function LegislationPage() {
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
                Real-time tracking of legislative developments affecting commodity markets
              </p>
            </div>
            
            <div className="bg-background-secondary rounded-lg border border-border-primary p-8 text-center">
              <div className="text-text-tertiary mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-text-primary mb-2">Policy Tracker Coming Soon</h3>
              <p className="text-text-secondary max-w-md mx-auto">
                Real-time policy and legislation tracking dashboard with biofuel mandate analysis, 
                trade policy impact assessment, and regulatory change monitoring.
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
