'use client'

import { useQuery } from '@tanstack/react-query'
import { Newspaper, TrendingUp, TrendingDown, AlertTriangle, Clock } from 'lucide-react'

interface NewsItem {
  published: string
  headline: string
  whyItMatters: string
  dollarImpact: string
  impactDirection: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  recommendation: 'BUY' | 'WAIT' | 'MONITOR'
  urgency: 'CRITICAL' | 'HIGH' | 'MEDIUM'
  confidenceScore: number
  source: string
}

interface BreakingNewsData {
  news: NewsItem[]
  updated_at: string
}

async function fetchBreakingNews(): Promise<BreakingNewsData> {
  const response = await fetch('/api/v4/breaking-news')
  
  if (!response.ok) {
    throw new Error('News data unavailable')
  }
  
  return await response.json()
}

const getImpactColor = (direction: string) => {
  switch (direction) {
    case 'BULLISH': return 'text-buy-primary'
    case 'BEARISH': return 'text-sell-primary'
    case 'NEUTRAL': return 'text-text-secondary'
    default: return 'text-text-secondary'
  }
}

const getUrgencyColor = (urgency: string) => {
  switch (urgency) {
    case 'CRITICAL': return 'bg-sell-critical/20 border-sell-critical/50 text-sell-critical'
    case 'HIGH': return 'bg-sell-caution/20 border-sell-caution/50 text-sell-caution'
    case 'MEDIUM': return 'bg-buy-accent/20 border-buy-accent/50 text-buy-accent'
    default: return 'bg-background-tertiary border-border-primary text-text-secondary'
  }
}

export function BreakingNews() {
  const { data: newsData, isLoading, error } = useQuery({
    queryKey: ['breaking-news'],
    queryFn: fetchBreakingNews,
    refetchInterval: 5 * 60 * 1000, // Update every 5 minutes
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Newspaper className="w-5 h-5 text-accent-purple animate-pulse" />
          <h2 className="text-lg font-semibold text-text-primary">
            Breaking News & AI Analysis
          </h2>
        </div>
        <div className="space-y-3">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="bg-background-tertiary rounded-lg p-4">
              <div className="loading-shimmer h-5 w-3/4 rounded mb-2"></div>
              <div className="loading-shimmer h-4 w-full rounded mb-2"></div>
              <div className="loading-shimmer h-4 w-1/2 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error || !newsData || newsData.news.length === 0) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Newspaper className="w-5 h-5 text-accent-purple" />
          <h2 className="text-lg font-semibold text-text-primary">
            Breaking News & AI Analysis
          </h2>
        </div>
        <div className="text-center py-6 text-text-secondary">
          No breaking news in last 24 hours
        </div>
      </div>
    )
  }

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6 shadow-depth">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Newspaper className="w-5 h-5 text-accent-purple" />
          <h2 className="text-lg font-semibold text-text-primary">
            Breaking News & AI Analysis
          </h2>
        </div>
        <div className="flex items-center space-x-2 text-xs text-text-tertiary">
          <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse"></div>
          <span>LIVE FEED</span>
        </div>
      </div>

      {/* News Items */}
      <div className="space-y-4">
        {newsData.news.map((item, index) => {
          const isNegative = item.impactDirection === 'BEARISH'
          const isPositive = item.impactDirection === 'BULLISH'
          
          return (
            <div
              key={index}
              className={`rounded-lg border p-4 transition-all hover:border-accent-purple/50 ${
                getUrgencyColor(item.urgency)
              }`}
            >
              {/* News Headline */}
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-base font-medium text-text-primary flex-1">
                  {item.headline}
                </h3>
                <div className={`ml-4 flex items-center space-x-1 font-semibold ${
                  isNegative ? 'text-sell-primary' : isPositive ? 'text-buy-primary' : 'text-text-secondary'
                }`}>
                  {isNegative ? <TrendingDown className="w-4 h-4" /> : isPositive ? <TrendingUp className="w-4 h-4" /> : null}
                  <span>{item.dollarImpact}/cwt</span>
                </div>
              </div>

              {/* AI Analysis - Why It Matters */}
              <div className="mb-3 p-3 bg-background-primary/50 rounded border border-border-secondary">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-accent-purple mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-xs text-text-tertiary uppercase tracking-wider mb-1 font-mono">
                      WHY IT MATTERS FOR YOUR PROCUREMENT:
                    </p>
                    <p className="text-sm text-text-primary leading-relaxed">
                      {item.whyItMatters}
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Recommendation */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    item.recommendation === 'BUY' 
                      ? 'bg-buy-primary/20 text-buy-primary border border-buy-primary/30'
                      : item.recommendation === 'WAIT'
                      ? 'bg-sell-caution/20 text-sell-caution border border-sell-caution/30'
                      : 'bg-text-secondary/20 text-text-secondary border border-text-secondary/30'
                  }`}>
                    {item.recommendation}
                  </div>
                  <div className="text-xs text-text-tertiary font-mono">
                    AI Confidence: {item.confidenceScore}%
                  </div>
                </div>
                <div className="flex items-center space-x-1 text-xs text-text-tertiary">
                  <Clock className="w-3 h-3" />
                  <span>{new Date(item.published).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Bottom Status */}
      <div className="mt-4 pt-4 border-t border-border-secondary flex items-center justify-between">
        <div className="text-xs text-text-secondary">
          <span className="font-mono">SOURCE:</span> GDELT Global Events + AI Analysis
        </div>
        <div className="text-xs text-text-tertiary">
          Last updated: {new Date(newsData.updated_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

