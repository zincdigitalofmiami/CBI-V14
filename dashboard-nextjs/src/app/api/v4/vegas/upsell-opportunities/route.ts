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

    // Query for upsell opportunities with REAL FRYER DATA ONLY (READ ONLY from Glide)
    // Only calculates if Kevin provides all required inputs
    const query = `
      WITH restaurant_fryer_capacity AS (
        SELECT 
          r.glide_rowID as restaurant_id,
          r.MHXYO as restaurant_name,
          r.U0Jf2 as oil_type,
          r.s8tNr as status,
          r.Po4Zg as delivery_freq,
          COUNT(f.glide_rowID) as fryer_count,
          ROUND(SUM(f.xhrM0), 2) as total_capacity_lbs,
          COALESCE(c.oil_multiplier, 1.0) as cuisine_multiplier,
          c.cuisine_type
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_fryers\` f
          ON r.glide_rowID = f.\`2uBBn\`
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_cuisine_multipliers\` c
          ON r.glide_rowID = c.glide_rowID
        WHERE r.s8tNr = 'Open'
        GROUP BY r.glide_rowID, r.MHXYO, r.U0Jf2, r.s8tNr, r.Po4Zg, c.oil_multiplier, c.cuisine_type
        HAVING fryer_count > 0
      )
      SELECT 
        restaurant_id as id,
        restaurant_name as venue_name,
        NULL as event_name,
        NULL as event_date,
        NULL as event_duration_days,
        NULL as expected_attendance,
        total_capacity_lbs,
        fryer_count,
        -- Base weekly gallons: only calculate if TPM provided, WITH CUISINE MULTIPLIER
        CASE 
          WHEN ${tpm !== null ? `true` : `false`} THEN ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier, 2)
          ELSE NULL
        END as base_weekly_gallons,
        -- Event surge: only calculate if TPM, event_days, and multiplier provided, WITH CUISINE MULTIPLIER
        CASE 
          WHEN ${tpm !== null && eventDays !== null && eventMultiplier !== null ? `true` : `false`} 
          THEN ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier * (${eventDaysValue}/7.0) * ${eventMultiplierValue}, 0)
          ELSE NULL
        END as event_surge_gallons,
        -- Upsell potential: only calculate if surge and upsell % provided, WITH CUISINE MULTIPLIER
        CASE 
          WHEN ${tpm !== null && eventDays !== null && eventMultiplier !== null && upsellPct !== null ? `true` : `false`}
          THEN ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier * (${eventDaysValue}/7.0) * ${eventMultiplierValue} * ${upsellPctValue}, 0)
          ELSE NULL
        END as upsell_gallons,
        -- Revenue opportunity: only calculate if upsell and price provided, WITH CUISINE MULTIPLIER
        CASE 
          WHEN ${tpm !== null && eventDays !== null && eventMultiplier !== null && upsellPct !== null && pricePerGal !== null ? `true` : `false`}
          THEN ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier * (${eventDaysValue}/7.0) * ${eventMultiplierValue} * ${upsellPctValue} * ${pricePerGalValue}, 0)
          ELSE NULL
        END as revenue_usd,
        -- Urgency based on fryer count only (real data)
        CASE 
          WHEN fryer_count >= 5 THEN 'IMMEDIATE ACTION'
          WHEN fryer_count >= 3 THEN 'HIGH PRIORITY'
          ELSE 'MONITOR'
        END as urgency,
        NULL as messaging_strategy_target,
        -- Monthly forecast message (WITH CUISINE MULTIPLIER)
        CASE 
          WHEN ${tpm !== null ? `true` : `false`}
          THEN CONCAT(CAST(fryer_count as STRING), ' fryers, ', CAST(ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier, 0) as STRING), ' gal/week baseline (', cuisine_type, ' ×', CAST(ROUND(cuisine_multiplier, 1) as STRING), ')')
          ELSE CONCAT(CAST(fryer_count as STRING), ' fryers')
        END as messaging_strategy_monthly_forecast,
        -- Event surge message (WITH CUISINE MULTIPLIER)
        CASE 
          WHEN ${tpm !== null && eventDays !== null && eventMultiplier !== null && upsellPct !== null ? `true` : `false`}
          THEN CONCAT('Event surge: +', CAST(ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier * (${eventDaysValue}/7.0) * ${eventMultiplierValue}, 0) as STRING), ' gal. Upsell: ', CAST(ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier * (${eventDaysValue}/7.0) * ${eventMultiplierValue} * ${upsellPctValue}, 0) as STRING), ' gal (', CAST(ROUND(${upsellPctValue} * 100, 0) as STRING), '%)')
          ELSE NULL
        END as messaging_strategy_message,
        NULL as messaging_strategy_timing,
        -- ROI value prop (only if all inputs provided including ZL cost and tanker cost, WITH CUISINE MULTIPLIER)
        CASE 
          WHEN ${tpm !== null && eventDays !== null && eventMultiplier !== null && upsellPct !== null && pricePerGal !== null && actualZlCost !== null && actualZlCost !== undefined && tankerCost !== null ? `true` : `false`}
          THEN CONCAT('ROI: ', CAST(ROUND((ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier * (${eventDaysValue}/7.0) * ${eventMultiplierValue} * ${upsellPctValue} * ${pricePerGalValue}, 0)) / NULLIF(ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier * (${eventDaysValue}/7.0) * ${eventMultiplierValue} * ${upsellPctValue}, 0) * ${actualZlCost} + ${tankerCost}, 0), 1) as STRING), 'x')
          ELSE NULL
        END as messaging_strategy_value_prop,
        -- Calculation available flag
        CASE 
          WHEN ${tpm !== null && eventDays !== null && eventMultiplier !== null && upsellPct !== null && pricePerGal !== null ? `true` : `false`} THEN true
          ELSE false
        END as calculation_available
      FROM restaurant_fryer_capacity
      WHERE fryer_count > 0
      ORDER BY 
        CASE 
          WHEN ${tpm !== null && eventDays !== null && eventMultiplier !== null && upsellPct !== null && pricePerGal !== null ? `true` : `false`} THEN revenue_usd
          ELSE fryer_count
        END DESC
      LIMIT 20
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      // Table doesn't exist yet - return empty array
      return NextResponse.json([])
    }

    // Transform to match component interface - REAL DATA ONLY, NULL for missing inputs
    const opportunities = results.map((row: any) => ({
      id: row.id,
      venue_name: row.venue_name,
      event_name: row.event_name,
      event_date: row.event_date?.value || row.event_date || null,
      event_duration_days: row.event_duration_days || null,
      expected_attendance: row.expected_attendance || null,
      oil_demand_surge_gal: row.event_surge_gallons !== null && row.event_surge_gallons !== undefined ? parseInt(row.event_surge_gallons) : null,
      revenue_opportunity: row.revenue_usd !== null && row.revenue_usd !== undefined ? parseInt(row.revenue_usd) : null,
      urgency: row.urgency,
      calculation_available: row.calculation_available || false,
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
