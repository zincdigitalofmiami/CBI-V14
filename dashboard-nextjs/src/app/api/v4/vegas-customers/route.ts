import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    const query = `
      SELECT 
        customer_id,
        customer_name,
        location,
        consumption_gallons_per_month,
        last_order_date,
        status
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_customers\`
      ORDER BY customer_name
    `
    
    const rows = await executeBigQueryQuery(query)
    
    return NextResponse.json(rows, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Vegas customers API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

