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

    // Query REAL EVENT OPPORTUNITIES from proximity-based scoring system
    const query = `
      SELECT 
        CONCAT(event_id, '_', restaurant_id) as id,
        restaurant_name as venue_name,
        event_name,
        event_date,
        3 as event_duration_days,  -- Default 3 days for events
        expected_attendance,
        event_surge_gallons as oil_demand_surge_gal,
        revenue_opportunity as revenue_usd,
        urgency_classification as urgency,
        opportunity_score_display,
        opportunity_score,
        distance_km,
        days_until,
        analysis_bullets,
        -- Messaging strategy
        restaurant_name as messaging_strategy_target,
        CONCAT(event_name, ' on ', FORMAT_DATE('%B %d, %Y', event_date)) as messaging_strategy_monthly_forecast,
        CONCAT('Expected surge: +', CAST(event_surge_gallons as STRING), ' gallons. Revenue opportunity: $', FORMAT("%'d", CAST(revenue_opportunity as INT64))) as messaging_strategy_message,
        CONCAT('Contact ', CAST(days_until - 7 as STRING), ' days before event') as messaging_strategy_timing,
        CONCAT('$', FORMAT("%'d", CAST(revenue_opportunity as INT64)), ' incremental revenue') as messaging_strategy_value_prop,
        true as calculation_available
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_top_opportunities\`
      WHERE days_until >= 0 AND days_until <= 90
      ORDER BY opportunity_score DESC
      LIMIT 20
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
