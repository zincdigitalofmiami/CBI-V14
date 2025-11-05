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
    const zlCost = searchParams.get('zl_cost') ? parseFloat(searchParams.get('zl_cost')!) : null
    const tankerCost = searchParams.get('tanker_cost') ? parseFloat(searchParams.get('tanker_cost')!) : null

    // Get ZL cost from Dashboard forecast if not provided
    let actualZlCost = zlCost
    if (!actualZlCost) {
      try {
        const zlQuery = `
          SELECT close as zl_cost
          FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`
          ORDER BY time DESC
          LIMIT 1
        `
        const zlResult = await executeBigQueryQuery(zlQuery)
        if (zlResult && zlResult.length > 0 && zlResult[0]?.zl_cost) {
          actualZlCost = zlResult[0].zl_cost
        }
      } catch (e) {
        // ZL cost not available, will return NULL for calculations requiring it
      }
    }

    // Build query with conditional calculations based on provided inputs
    const tpmValue = tpm !== null ? tpm : 'NULL'
    const eventDaysValue = eventDays !== null ? eventDays : 'NULL'
    const eventMultiplierValue = eventMultiplier !== null ? eventMultiplier : 'NULL'
    const upsellPctValue = upsellPct !== null ? upsellPct : 'NULL'
    const pricePerGalValue = pricePerGal !== null ? pricePerGal : 'NULL'

    // NO FAKE DATA - Return empty until real event data available
    // Event data must come from Glide or verified external source
    const query = `
      SELECT 
        'no_data' as id,
        'No Event Data' as venue_name,
        NULL as event_name,
        NULL as event_date,
        NULL as event_duration_days,
        NULL as expected_attendance,
        NULL as oil_demand_surge_gal,
        NULL as revenue_usd,
        'MONITOR' as urgency,
        NULL as opportunity_score_display,
        NULL as opportunity_score,
        NULL as distance_km,
        NULL as days_until,
        [] as analysis_bullets,
        NULL as messaging_strategy_target,
        NULL as messaging_strategy_monthly_forecast,
        NULL as messaging_strategy_message,
        NULL as messaging_strategy_timing,
        NULL as messaging_strategy_value_prop,
        false as calculation_available
      LIMIT 0
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      // Table doesn't exist yet - return empty array
      return NextResponse.json([])
    }

    // Transform to match component interface - REAL EVENT OPPORTUNITIES WITH SCORES
    const opportunities = results.map((row: any) => ({
      id: row.id,
      venue_name: row.venue_name,
      event_name: row.event_name,
      event_date: row.event_date?.value || row.event_date || null,
      event_duration_days: row.event_duration_days || null,
      expected_attendance: row.expected_attendance || null,
      oil_demand_surge_gal: row.oil_demand_surge_gal || null,
      revenue_opportunity: row.revenue_usd || null,
      urgency: row.urgency,
      calculation_available: row.calculation_available || false,
      opportunity_score: row.opportunity_score || null,
      opportunity_score_display: row.opportunity_score_display || null,
      distance_km: row.distance_km || null,
      days_until: row.days_until || null,
      analysis_bullets: row.analysis_bullets || [],
      messaging_strategy: {
        target: row.messaging_strategy_target || null,
        monthly_forecast: row.messaging_strategy_monthly_forecast || null,
        message: row.messaging_strategy_message || null,
        timing: row.messaging_strategy_timing || null,
        value_prop: row.messaging_strategy_value_prop || null
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
