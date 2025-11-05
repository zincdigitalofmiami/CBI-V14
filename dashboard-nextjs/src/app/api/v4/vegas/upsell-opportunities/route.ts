import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // Query for event-driven upsell opportunities from vegas_upsell_opportunities table
    const query = `
      SELECT 
        id,
        venue_name,
        event_name,
        event_date,
        event_duration_days,
        expected_attendance,
        oil_demand_surge_gal,
        revenue_opportunity,
        urgency,
        messaging_strategy_target,
        messaging_strategy_monthly_forecast,
        messaging_strategy_message,
        messaging_strategy_timing,
        messaging_strategy_value_prop
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_upsell_opportunities\`
      ORDER BY 
        CASE urgency
          WHEN 'IMMEDIATE ACTION' THEN 1
          WHEN 'HIGH PRIORITY' THEN 2
          ELSE 3
        END,
        revenue_opportunity DESC
      LIMIT 20
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      // Table doesn't exist yet - return empty array
      return NextResponse.json([])
    }

    // Transform to match component interface - NO FAKE DATA
    const opportunities = results.map((row: any) => ({
      id: row.id,
      venue_name: row.venue_name,
      event_name: row.event_name,
      event_date: row.event_date?.value || row.event_date,
      event_duration_days: row.event_duration_days,
      expected_attendance: row.expected_attendance,
      oil_demand_surge_gal: row.oil_demand_surge_gal,
      revenue_opportunity: row.revenue_opportunity,
      urgency: row.urgency,
      messaging_strategy: {
        target: row.messaging_strategy_target,
        monthly_forecast: row.messaging_strategy_monthly_forecast,
        message: row.messaging_strategy_message,
        timing: row.messaging_strategy_timing,
        value_prop: row.messaging_strategy_value_prop
      }
    }))

    return NextResponse.json(opportunities)
  } catch (error: any) {
    // Table doesn't exist yet - return empty array gracefully
    if (error.message?.includes('not found') || error.message?.includes('does not exist')) {
      return NextResponse.json([])
    }
    console.error('Vegas upsell opportunities error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
