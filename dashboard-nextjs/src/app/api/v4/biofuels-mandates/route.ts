import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    const query = `
      SELECT 
        event_date,
        event_title,
        event_type,
        description,
        impact_score,
        passage_probability,
        soybean_oil_demand_impact_pct
      FROM \`cbi-v14.forecasting_data_warehouse.legislation_events\`
      WHERE event_type = 'biofuel_mandate'
        AND event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      ORDER BY passage_probability DESC, impact_score DESC
    `
    
    const rows = await executeBigQueryQuery(query)
    
    return NextResponse.json(rows, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Biofuels mandates API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

