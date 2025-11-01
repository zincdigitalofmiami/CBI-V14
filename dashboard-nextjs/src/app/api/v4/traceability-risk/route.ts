import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    const query = `
      SELECT 
        event_date,
        event_title,
        description,
        compliance_region,
        compliance_score,
        cost_impact_per_mt,
        deadline_date,
        risk_level
      FROM \`cbi-v14.forecasting_data_warehouse.legislation_events\`
      WHERE event_type = 'traceability'
        AND event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      ORDER BY risk_level DESC, deadline_date ASC
    `
    
    const rows = await executeBigQueryQuery(query)
    
    return NextResponse.json(rows, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Traceability risk API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

