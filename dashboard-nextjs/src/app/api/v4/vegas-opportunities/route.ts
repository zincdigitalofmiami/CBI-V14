import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    const query = `
      SELECT 
        opportunity_id,
        event_id,
        customer_id,
        opportunity_name,
        estimated_gallons,
        estimated_revenue,
        confidence_score,
        created_at
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_sales_opportunities\`
      ORDER BY confidence_score DESC, estimated_revenue DESC
    `
    
    const rows = await executeBigQueryQuery(query)
    
    return NextResponse.json(rows, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Vegas opportunities API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

