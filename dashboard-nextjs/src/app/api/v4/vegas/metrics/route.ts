import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // Aggregate metrics from multiple tables
    const query = `
      WITH customer_count AS (
        SELECT COUNT(DISTINCT customer_id) as total_customers
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_customers\`
      ),
      opportunity_count AS (
        SELECT COUNT(*) as active_opportunities
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_events\`
        WHERE event_date >= CURRENT_DATE()
          AND revenue_opportunity > 0
      ),
      event_count AS (
        SELECT COUNT(*) as upcoming_events
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_events\`
        WHERE event_date >= CURRENT_DATE()
          AND event_date <= DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY)
      ),
      revenue_sum AS (
        SELECT COALESCE(SUM(revenue_opportunity), 0) as estimated_revenue_potential
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_events\`
        WHERE event_date >= CURRENT_DATE()
          AND event_date <= DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY)
      ),
      alert_count AS (
        SELECT COUNT(*) as margin_risk_alerts
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_margin_alerts\`
      )
      SELECT 
        c.total_customers,
        o.active_opportunities,
        e.upcoming_events,
        r.estimated_revenue_potential,
        a.margin_risk_alerts
      FROM customer_count c
      CROSS JOIN opportunity_count o
      CROSS JOIN event_count e
      CROSS JOIN revenue_sum r
      CROSS JOIN alert_count a
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      return NextResponse.json({
        total_customers: 0,
        active_opportunities: 0,
        upcoming_events: 0,
        estimated_revenue_potential: 0,
        margin_risk_alerts: 0
      })
    }

    const metrics = results[0]
    return NextResponse.json({
      total_customers: metrics.total_customers,
      active_opportunities: metrics.active_opportunities,
      upcoming_events: metrics.upcoming_events,
      estimated_revenue_potential: metrics.estimated_revenue_potential,
      margin_risk_alerts: metrics.margin_risk_alerts
    })
  } catch (error: any) {
    // Tables don't exist yet - return zeros
    if (error.message?.includes('not found') || error.message?.includes('does not exist')) {
      return NextResponse.json({
        total_customers: 0,
        active_opportunities: 0,
        upcoming_events: 0,
        estimated_revenue_potential: 0,
        margin_risk_alerts: 0
      })
    }
    console.error('Vegas metrics error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
