import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    // Get top 10 bills
    const billsQuery = `
      SELECT 
        bill_id,
        bill_number,
        title,
        status,
        passage_probability,
        soy_relevance_score,
        demand_impact_pct
      FROM \`cbi-v14.forecasting_data_warehouse.all_bills\`
      WHERE soy_relevance_score > 0.5
      ORDER BY passage_probability DESC, soy_relevance_score DESC
      LIMIT 10
    `
    
    // Get lobbying data
    const lobbyingQuery = `
      SELECT 
        date,
        organization,
        amount,
        bill_id,
        issue_category
      FROM \`cbi-v14.forecasting_data_warehouse.lobbying\`
      WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY)
        AND issue_category LIKE '%soy%' OR issue_category LIKE '%biofuel%'
      ORDER BY amount DESC
      LIMIT 50
    `
    
    const bills = await executeBigQueryQuery(billsQuery)
    const lobbying = await executeBigQueryQuery(lobbyingQuery)
    
    return NextResponse.json({
      bills,
      lobbying
    }, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Bills lobbying API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

