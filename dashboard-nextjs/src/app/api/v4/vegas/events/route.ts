import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
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
          ROUND(SUM((f.xhrM0 * 4) / 7.6 * COALESCE(cuisine.oil_multiplier, 1.0)), 0) as weekly_base_gallons,
          -- Event multiplier based on fryer count (more fryers = higher surge potential)
          CASE 
            WHEN COUNT(f.glide_rowID) >= 20 THEN 3.4  -- Major casino (F1-level surge)
            WHEN COUNT(f.glide_rowID) >= 10 THEN 2.5  -- Large casino
            WHEN COUNT(f.glide_rowID) >= 5 THEN 1.8   -- Medium casino
            ELSE 1.3  -- Small casino
          END as volume_multiplier
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
        DATE_ADD(CURRENT_DATE(), INTERVAL 14 DAY) as date,
        location,
        volume_multiplier,
        restaurant_count as affected_customers,
        CAST(ROUND(weekly_base_gallons * volume_multiplier * 0.68 * 8.20, 0) as INT64) as revenue_impact,
        14 as days_until
      FROM casino_capacity
      WHERE total_fryers > 0
      ORDER BY revenue_impact DESC
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
      date: row.date?.value || row.date,
      location: row.location,
      volume_multiplier: row.volume_multiplier,
      affected_customers: row.expected_attendance,  // Use actual attendance data
      revenue_impact: row.revenue_impact,
      days_until: row.days_until
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
