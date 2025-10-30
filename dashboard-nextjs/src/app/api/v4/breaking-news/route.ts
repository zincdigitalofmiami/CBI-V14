import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get latest 3 news items
    const newsQuery = `
      SELECT 
        published,
        title,
        content,
        intelligence_score,
        REGEXP_EXTRACT(content, r'Goldstein Scale: ([0-9.]+)') as goldstein_scale,
        REGEXP_EXTRACT(content, r'Tone: ([\\-0-9.]+)') as sentiment_tone,
        REGEXP_EXTRACT(content, r'Event Code: ([0-9]+)') as event_code,
        REGEXP_EXTRACT(content, r'Actors: ([A-Z]+) → ([A-Z]+)') as actors
      FROM \`cbi-v14.forecasting_data_warehouse.news_intelligence\`
      WHERE published >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      ORDER BY published DESC, intelligence_score DESC
      LIMIT 3
    `
    
    const newsResult = await executeBigQueryQuery(newsQuery)
    
    if (newsResult.length === 0) {
      return NextResponse.json({
        news: [],
        message: 'No recent news in last 24 hours'
      }, { status: 200 })
    }

    // Transform news into Chris-friendly format with AI analysis
    const breakingNews = newsResult.map((item: any) => {
      const goldstein = parseFloat(item.goldstein_scale) || 0
      const tone = parseFloat(item.sentiment_tone) || 0
      const eventCode = item.event_code || 'UNKNOWN'
      
      // AI Analysis - Translate to procurement impact
      let headline = item.title
      let whyItMatters = ''
      let dollarImpact = 0
      let recommendation = 'MONITOR'
      
      // China-US trade events
      if (item.title.includes('China') && item.title.includes('Trade')) {
        if (tone < 0) {
          headline = '🔴 China-US Trade Tensions Escalate'
          whyItMatters = 'Negative trade relations = China continues boycott of US soybeans. Keeps buying from Argentina instead, pressuring US prices down.'
          dollarImpact = -0.80
          recommendation = 'WAIT'
        } else if (tone > 1) {
          headline = '🟢 China-US Trade Relations Improving'
          whyItMatters = 'Positive diplomatic signals could lead to China resuming US soy purchases. Would spike demand and prices.'
          dollarImpact = +1.50
          recommendation = 'BUY'
        } else {
          headline = '🟡 China-US Trade Activity (Neutral)'
          whyItMatters = 'Standard trade communications. No immediate impact on soybean demand or prices.'
          dollarImpact = 0
          recommendation = 'MONITOR'
        }
      }
      
      // Calculate urgency (Goldstein scale 0-10)
      const urgency = goldstein > 7 ? 'CRITICAL' : goldstein > 4 ? 'HIGH' : 'MEDIUM'
      
      return {
        published: item.published,
        headline,
        whyItMatters,
        dollarImpact: dollarImpact.toFixed(2),
        impactDirection: dollarImpact > 0 ? 'BULLISH' : dollarImpact < 0 ? 'BEARISH' : 'NEUTRAL',
        recommendation,
        urgency,
        confidenceScore: Math.round(item.intelligence_score * 100),
        rawTone: tone.toFixed(2),
        goldsteinScale: goldstein,
        source: 'GDELT + AI Analysis'
      }
    })

    return NextResponse.json({
      news: breakingNews,
      updated_at: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Breaking news error:', error)
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error',
        details: 'Cannot fetch news intelligence'
      },
      { status: 500 }
    )
  }
}

