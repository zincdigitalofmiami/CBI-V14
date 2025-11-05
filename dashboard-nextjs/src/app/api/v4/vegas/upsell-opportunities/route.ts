import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // Query for event-driven upsell opportunities
    // TODO: Update table name when Vegas events table is created
    const query = `
      SELECT 
        event_id as id,
        venue_name,
        event_name,
        event_date,
        event_duration_days,
        expected_attendance,
        oil_demand_surge_gal,
        revenue_opportunity,
        urgency,
        target_restaurants as messaging_target,
        monthly_forecast_text,
        ai_message,
        timing_recommendation,
        value_proposition
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_events\`
      WHERE event_date >= CURRENT_DATE()
        AND revenue_opportunity > 0
      ORDER BY event_date ASC, revenue_opportunity DESC
      LIMIT 20
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      // Table doesn't exist yet - return empty array
      return NextResponse.json([])
    }

    // Transform to match component interface
    const opportunities = results.map((row: any) => ({
      id: row.id,
      venue_name: row.venue_name,
      event_name: row.event_name,
      event_date: row.event_date?.value || row.event_date,
      event_duration_days: row.event_duration_days || 1,
      expected_attendance: row.expected_attendance || 0,
      oil_demand_surge_gal: row.oil_demand_surge_gal || 0,
      revenue_opportunity: row.revenue_opportunity || 0,
      urgency: row.urgency || 'MONITOR',
      messaging_strategy: {
        target: row.messaging_target || 'Las Vegas area restaurants',
        monthly_forecast: row.monthly_forecast_text || 'Check dashboard for monthly forecast',
        message: row.ai_message || `${row.venue_name} - ${row.event_name} bringing increased demand. Increase oil delivery to meet surge.`,
        timing: row.timing_recommendation || 'Send TODAY',
        value_prop: row.value_proposition || 'Avoid stockouts during peak demand. We\'ll adjust delivery schedule automatically.'
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
