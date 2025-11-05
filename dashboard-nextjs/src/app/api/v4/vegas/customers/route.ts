import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // Query for customer relationship data
    const query = `
      SELECT 
        customer_id as id,
        customer_name as name,
        account_type,
        relationship_score,
        current_volume_gal as current_volume,
        last_order_date,
        growth_potential,
        next_action
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_customers\`
      ORDER BY relationship_score DESC, current_volume_gal DESC
      LIMIT 50
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      return NextResponse.json([])
    }

    const customers = results.map((row: any) => ({
      id: row.id,
      name: row.name,
      account_type: row.account_type || 'Other',
      relationship_score: row.relationship_score || 0,
      current_volume: row.current_volume || 0,
      last_order_date: row.last_order_date?.value || row.last_order_date || new Date().toISOString(),
      growth_potential: row.growth_potential || 'MEDIUM',
      next_action: row.next_action || 'Monitor relationship'
    }))

    return NextResponse.json(customers)
  } catch (error: any) {
    if (error.message?.includes('not found') || error.message?.includes('does not exist')) {
      return NextResponse.json([])
    }
    console.error('Vegas customers error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
