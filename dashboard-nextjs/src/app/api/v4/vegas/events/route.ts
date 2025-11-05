import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: Request) {
  try {
    // Get query parameters for Kevin inputs (all optional)
    const { searchParams } = new URL(request.url)
    const tpm = searchParams.get('tpm') ? parseFloat(searchParams.get('tpm')!) : null
    const eventMultiplier = searchParams.get('event_multiplier') ? parseFloat(searchParams.get('event_multiplier')!) : null
    const upsellPct = searchParams.get('upsell_pct') ? parseFloat(searchParams.get('upsell_pct')!) : null
    const pricePerGal = searchParams.get('price_per_gal') ? parseFloat(searchParams.get('price_per_gal')!) : null

    // Build query with conditional calculations based on provided inputs
    const tpmValue = tpm !== null ? tpm : 4  // Default TPM = 4
    const eventMultiplierValue = eventMultiplier !== null ? eventMultiplier : null
    const upsellPctValue = upsellPct !== null ? upsellPct : null
    const pricePerGalValue = pricePerGal !== null ? pricePerGal : null

    // Query for events with casino + fryer capacity (READ ONLY from Glide)
    // Shows volume multipliers based on real fryer capacity at each casino
    const query = `
      WITH casino_capacity AS (
        SELECT 
          c.glide_rowID as casino_id,
          c.Name as casino_name,
          c.L9K9x as location,
          COUNT(DISTINCT r.glide_rowID) as restaurant_count,
          COUNT(f.glide_rowID) as total_fryers,
          -- Total weekly capacity for this casino's restaurants WITH CUISINE MULTIPLIER
          ROUND(SUM((f.xhrM0 * ${tpmValue}) / 7.6 * COALESCE(cuisine.oil_multiplier, 1.0)), 0) as weekly_base_gallons
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_casinos\` c
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
          ON r.\`2Ca0T\` = c.glide_rowID OR r.g5WAm = c.glide_rowID
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_fryers\` f
          ON r.glide_rowID = f.\`2uBBn\`
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_cuisine_multipliers\` cuisine
          ON r.glide_rowID = cuisine.glide_rowID
        WHERE c.Name IS NOT NULL
        GROUP BY c.glide_rowID, c.Name, c.L9K9x
      )
      SELECT 
        casino_id as id,
        casino_name as name,
        'Casino Event Surge' as type,
        NULL as date,
        location,
        -- Volume multiplier from Kevin input or NULL
        CASE 
          WHEN ${eventMultiplier !== null ? `true` : `false`} THEN ${eventMultiplierValue !== null ? eventMultiplierValue : 'NULL'}
          ELSE NULL
        END as volume_multiplier,
        restaurant_count as affected_customers,
        -- Revenue impact: only calculate if all inputs provided
        CASE 
          WHEN ${eventMultiplier !== null && upsellPct !== null && pricePerGal !== null ? `true` : `false`}
          THEN CAST(ROUND(weekly_base_gallons * ${eventMultiplierValue !== null ? eventMultiplierValue : 'NULL'} * ${upsellPctValue !== null ? upsellPctValue : 'NULL'} * ${pricePerGalValue !== null ? pricePerGalValue : 'NULL'}, 0) as INT64)
          ELSE NULL
        END as revenue_impact,
        NULL as days_until
      FROM casino_capacity
      WHERE total_fryers > 0
      ORDER BY 
        CASE 
          WHEN ${eventMultiplier !== null && upsellPct !== null && pricePerGal !== null ? `true` : `false`} THEN revenue_impact
          ELSE total_fryers
        END DESC
      LIMIT 30
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      return NextResponse.json([])
    }

    const events = results.map((row: any) => ({
      id: row.id,
      name: row.name,
      type: row.type,
      date: row.date?.value || row.date || null,
      location: row.location,
      volume_multiplier: row.volume_multiplier !== null && row.volume_multiplier !== undefined ? parseFloat(row.volume_multiplier) : null,
      affected_customers: row.affected_customers || null,
      revenue_impact: row.revenue_impact !== null && row.revenue_impact !== undefined ? parseInt(row.revenue_impact) : null,
      days_until: row.days_until || null
    }))

    return NextResponse.json(events)
  } catch (error: any) {
    if (error.message?.includes('not found') || error.message?.includes('does not exist')) {
      return NextResponse.json([])
    }
    console.error('Vegas events error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
