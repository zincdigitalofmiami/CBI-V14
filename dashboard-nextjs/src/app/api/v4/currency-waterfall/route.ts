import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    const query = `
      SELECT 
        date,
        pair,
        close_rate,
        pct_change,
        impact_score,
        source_name
      FROM \`cbi-v14.forecasting_data_warehouse.currency_impact\`
      WHERE pair IN ('USD/BRL', 'USD/ARS', 'USD/MYR', 'USD/IDR', 'USD/CNY')
        AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
      ORDER BY date DESC, pair ASC
    `
    
    const rows = await executeBigQueryQuery(query)
    
    return NextResponse.json(rows, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Currency waterfall API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

