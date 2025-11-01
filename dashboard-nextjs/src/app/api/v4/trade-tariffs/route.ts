import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    // Get tariff events
    const eventsQuery = `
      SELECT 
        event_date,
        event_title,
        description,
        impact_score,
        price_impact_per_lb
      FROM \`cbi-v14.forecasting_data_warehouse.legislation_events\`
      WHERE event_type IN ('tariff', 'trade_deal')
        AND event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      ORDER BY event_date DESC
    `
    
    // Get historical tariff data
    const tariffQuery = `
      SELECT 
        date,
        country,
        tariff_rate,
        commodity_type,
        impact_per_mt
      FROM \`cbi-v14.forecasting_data_warehouse.tariff_data\`
      WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      ORDER BY date DESC, country
    `
    
    const events = await executeBigQueryQuery(eventsQuery)
    const tariffs = await executeBigQueryQuery(tariffQuery)
    
    return NextResponse.json({
      events,
      tariffs
    }, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Trade tariffs API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

