import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'

export default function SentimentPage() {
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
                Quantitative Sentiment Analysis
              </h1>
              <p className="text-text-secondary text-sm">
                Multi-horizon neural ensemble with adaptive regime detection
              </p>
            </div>
            
            <div className="bg-background-secondary rounded-lg border border-border-primary p-8 text-center">
              <div className="text-text-tertiary mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 8h10m0 0V18a2 2 0 01-2 2H9a2 2 0 01-2-2V8m5 0V4a2 2 0 00-2-2H8a2 2 0 00-2 2v4m5 0V4a2 2 0 012-2h2a2 2 0 012 2v4" />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-text-primary mb-2">Sentiment Analysis Coming Soon</h3>
              <p className="text-text-secondary max-w-md mx-auto">
                Advanced sentiment analysis dashboard with real-time social media monitoring, 
                news sentiment scoring, and market psychology indicators.
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
