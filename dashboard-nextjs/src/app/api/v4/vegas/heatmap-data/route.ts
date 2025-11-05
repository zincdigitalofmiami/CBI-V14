import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // Get heat map data: events + restaurants with impact scores
    const query = `
      WITH event_points AS (
        SELECT 
          lat,
          lng,
          AVG(combined_impact_score) as weight,
          'event' as type,
          ANY_VALUE(event_name) as name
        FROM \`cbi-v14.forecasting_data_warehouse.event_restaurant_impact\`
        WHERE event_lat IS NOT NULL AND event_lng IS NOT NULL
        GROUP BY lat, lng
      ),
      restaurant_points AS (
        SELECT 
          r.lat,
          r.lng,
          CAST(COUNT(DISTINCT e.event_id) as FLOAT64) as weight,
          'restaurant' as type,
          r.MHXYO as name
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.event_restaurant_impact\` e
          ON r.glide_rowID = e.restaurant_id
        WHERE r.lat IS NOT NULL AND r.lng IS NOT NULL
        GROUP BY r.lat, r.lng, r.MHXYO
      )
      SELECT lat, lng, weight, type, name
      FROM event_points
      WHERE weight > 0
      UNION ALL
      SELECT lat, lng, weight, type, name
      FROM restaurant_points
      WHERE weight > 0
      ORDER BY weight DESC
      LIMIT 200
    `
    
    const results = await executeBigQueryQuery(query)
    
    return NextResponse.json(results)
  } catch (error: any) {
    console.error('Heat map data error:', error)
    return NextResponse.json([])
  }
}

