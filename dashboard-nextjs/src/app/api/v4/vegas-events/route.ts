import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    const query = `
      SELECT 
        event_id,
        event_name,
        venue,
        start_date,
        end_date,
        expected_attendance,
        oil_demand_gallons_estimate,
        priority
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_events\`
      WHERE start_date >= CURRENT_DATE()
      ORDER BY start_date ASC
    `
    
    const rows = await executeBigQueryQuery(query)
    
    return NextResponse.json(rows, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Vegas events API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

