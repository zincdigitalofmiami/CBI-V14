import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: Request) {
  try {
    // Get query parameters for Kevin inputs (all optional)
    const { searchParams } = new URL(request.url)
    const tpm = searchParams.get('tpm') ? parseFloat(searchParams.get('tpm')!) : null

    // Build query with conditional calculations based on provided inputs
    const tpmValue = tpm !== null ? tpm : 4  // Default TPM = 4

    // Query for customer relationship data with REAL FRYER CAPACITY (READ ONLY from Glide)
    const query = `
      WITH restaurant_metrics AS (
        SELECT 
          r.glide_rowID as id,
          r.MHXYO as name,
          r.U0Jf2 as account_type,
          COUNT(f.glide_rowID) as fryer_count,
          -- Apply cuisine multiplier to weekly gallons
          ROUND((SUM(f.xhrM0) * ${tpmValue}) / 7.6 * COALESCE(c.oil_multiplier, 1.0), 2) as weekly_gallons,
          c.cuisine_type,
          COALESCE(c.oil_multiplier, 1.0) as cuisine_multiplier,
          -- Relationship score based on fryer count (proxy for account size)
          CASE 
            WHEN COUNT(f.glide_rowID) >= 5 THEN 85
            WHEN COUNT(f.glide_rowID) >= 3 THEN 70
            WHEN COUNT(f.glide_rowID) >= 1 THEN 50
            ELSE 30
          END as relationship_score,
          r.Po4Zg as delivery_frequency,
          r.uwU2A as last_order_date,
          -- Growth potential based on fryer count and status
          CASE 
            WHEN COUNT(f.glide_rowID) >= 5 THEN 'High'
            WHEN COUNT(f.glide_rowID) >= 3 THEN 'Medium'
            ELSE 'Low'
          END as growth_potential,
          CASE 
            WHEN r.s8tNr = 'Open' AND COUNT(f.glide_rowID) >= 3 THEN 'Pitch event upsell'
            WHEN r.s8tNr = 'Open' THEN 'Monitor for opportunities'
            ELSE 'Reactivate account'
          END as next_action
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_fryers\` f
          ON r.glide_rowID = f.\`2uBBn\`
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_cuisine_multipliers\` c
          ON r.glide_rowID = c.glide_rowID
        GROUP BY r.glide_rowID, r.MHXYO, r.U0Jf2, r.Po4Zg, r.uwU2A, r.s8tNr, c.cuisine_type, c.oil_multiplier
      )
      SELECT 
        id,
        name,
        account_type,
        relationship_score,
        CAST(ROUND(weekly_gallons, 0) as INT64) as current_volume,
        last_order_date,
        growth_potential,
        next_action
      FROM restaurant_metrics
      ORDER BY relationship_score DESC, weekly_gallons DESC
      LIMIT 50
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      return NextResponse.json([])
    }

    const customers = results.map((row: any) => ({
      id: row.id,
      name: row.name,
      account_type: row.account_type,
      relationship_score: row.relationship_score,
      current_volume: row.current_volume,
      last_order_date: row.last_order_date?.value || row.last_order_date,
      growth_potential: row.growth_potential,
      next_action: row.next_action
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
