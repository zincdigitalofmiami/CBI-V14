import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // Query for events - simplified to match actual table schema
    const query = `
      SELECT 
        event_id as id,
        event_name as name,
        event_type as type,
        event_date as date,
        location,
        expected_attendance,
        volume_multiplier,
        event_duration_days,
        revenue_opportunity as revenue_impact,
        DATE_DIFF(event_date, CURRENT_DATE(), DAY) as days_until
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_events\`
      WHERE event_date >= CURRENT_DATE()
      ORDER BY event_date ASC
      LIMIT 30
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      return NextResponse.json([])
    }

    const events = results.map((row: any) => ({
      id: row.id,
      name: row.name,
      type: row.type || 'Other',
      date: row.date?.value || row.date,
      location: row.location || 'Las Vegas, NV',
      volume_multiplier: row.volume_multiplier || 1.0,
      affected_customers: 3,  // Default for sample data
      revenue_impact: row.revenue_impact || 0,
      days_until: row.days_until || 0
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
