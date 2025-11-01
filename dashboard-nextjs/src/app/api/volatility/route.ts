import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300

export async function GET() {
  try {
    const query = `
      SELECT 
        as_of_timestamp,
        signal_name,
        signal_value
      FROM \`cbi-v14.forecasting_data_warehouse.signals_1w\`
      WHERE as_of_timestamp = (
        SELECT MAX(as_of_timestamp) 
        FROM \`cbi-v14.forecasting_data_warehouse.signals_1w\`
      )
      ORDER BY as_of_timestamp DESC
      LIMIT 100
    `
    
    const rows = await executeBigQueryQuery(query)
    
    return NextResponse.json(rows, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Volatility API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

