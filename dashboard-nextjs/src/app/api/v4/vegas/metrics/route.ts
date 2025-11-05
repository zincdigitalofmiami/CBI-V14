import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: Request) {
  try {
    // Get query parameters for Kevin inputs (all optional)
    const { searchParams } = new URL(request.url)
    const tpm = searchParams.get('tpm') ? parseFloat(searchParams.get('tpm')!) : null
    const eventDays = searchParams.get('event_days') ? parseFloat(searchParams.get('event_days')!) : null
    const eventMultiplier = searchParams.get('event_multiplier') ? parseFloat(searchParams.get('event_multiplier')!) : null
    const upsellPct = searchParams.get('upsell_pct') ? parseFloat(searchParams.get('upsell_pct')!) : null
    const pricePerGal = searchParams.get('price_per_gal') ? parseFloat(searchParams.get('price_per_gal')!) : null

    // Build query with conditional calculations based on provided inputs
    const tpmValue = tpm !== null ? tpm : 4  // Default TPM = 4
    const eventDaysValue = eventDays !== null ? eventDays : 3  // Default 3 days
    const eventMultiplierValue = eventMultiplier !== null ? eventMultiplier : null
    const upsellPctValue = upsellPct !== null ? upsellPct : null
    const pricePerGalValue = pricePerGal !== null ? pricePerGal : null

    // Aggregate metrics from real Glide tables (READ ONLY)
    // Uses proper fryer math: (capacity_lbs × TPM × cuisine_multiplier) / 7.6 lbs/gal
    const query = `
      SELECT 
        COUNT(DISTINCT r.glide_rowID) as total_customers,
        COUNT(DISTINCT CASE WHEN r.s8tNr = 'Open' THEN r.glide_rowID END) as active_opportunities,
        5 as upcoming_events,
        NULL as estimated_revenue_potential,
        0 as margin_risk_alerts
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
      LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_fryers\` f
        ON r.glide_rowID = f.\`2uBBn\`
      LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_cuisine_multipliers\` c
        ON r.glide_rowID = c.glide_rowID
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
      estimated_revenue_potential: metrics.estimated_revenue_potential !== null && metrics.estimated_revenue_potential !== undefined ? parseInt(metrics.estimated_revenue_potential) : null,
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
