import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'

export default function VegasIntelPage() {
  return (
    <div className="flex h-screen bg-background-primary">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-light text-text-primary mb-2">
                Vegas Sales Intelligence
              </h1>
              <p className="text-text-secondary">
                Event-driven upsell opportunities, customer relationship matrix, and margin protection alerts
              </p>
            </div>
            
            <div className="bg-background-secondary rounded-lg border border-border-primary p-8 text-center">
              <div className="text-text-tertiary mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-text-primary mb-2">Vegas Intel Coming Soon</h3>
              <p className="text-text-secondary max-w-md mx-auto">
                Kevin's sales intelligence dashboard with event-driven upsell engine, 
                customer relationship matrix, and AI-enhanced sales strategy recommendations.
              </p>
              <div className="mt-6 p-4 bg-background-tertiary rounded-lg border border-border-secondary">
                <div className="text-sm text-text-secondary">
                  <strong className="text-text-primary">Features in Development:</strong>
                  <ul className="mt-2 space-y-1 text-left max-w-sm mx-auto">
                    <li>• F1 Race & Convention Volume Multipliers</li>
                    <li>• Casino Customer Relationship Tracking</li>
                    <li>• Event-Driven Margin Protection Alerts</li>
                    <li>• Glide App Integration for Customer Data</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
