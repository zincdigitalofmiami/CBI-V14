import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: Request) {
  try {
    // Get query parameters for Kevin inputs (all optional)
    const { searchParams } = new URL(request.url)
    const tpm = searchParams.get('tpm') ? parseFloat(searchParams.get('tpm')!) : null
    const pricePerGal = searchParams.get('price_per_gal') ? parseFloat(searchParams.get('price_per_gal')!) : null
    const zlCost = searchParams.get('zl_cost') ? parseFloat(searchParams.get('zl_cost')!) : null

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
    const tpmValue = tpm !== null ? tpm : 4  // Default TPM = 4
    const pricePerGalValue = pricePerGal !== null ? pricePerGal : null
    const zlCostValue = actualZlCost !== null && actualZlCost !== undefined ? actualZlCost : null

    // Query for margin alerts based on REAL FRYER CAPACITY (READ ONLY from Glide)
    // High-volume accounts (many fryers) = higher margin risk if pricing slips
    const query = `
      WITH restaurant_risk AS (
        SELECT 
          r.glide_rowID as restaurant_id,
          r.MHXYO as restaurant_name,
          r.U0Jf2 as oil_type,
          COUNT(f.glide_rowID) as fryer_count,
          -- Apply cuisine multiplier to weekly gallons
          ROUND((SUM(f.xhrM0) * ${tpmValue}) / 7.6 * COALESCE(c.oil_multiplier, 1.0), 2) as weekly_gallons,
          COALESCE(c.oil_multiplier, 1.0) as cuisine_multiplier,
          -- Calculate margin risk based on volume
          CASE 
            WHEN COUNT(f.glide_rowID) >= 5 THEN 'HIGH'      -- Large accounts = high risk
            WHEN COUNT(f.glide_rowID) >= 3 THEN 'MEDIUM'    -- Medium accounts
            ELSE 'LOW'                                       -- Small accounts
          END as severity,
          -- Risk amount = weekly gallons × margin per gallon × 4 weeks (WITH CUISINE MULTIPLIER)
          -- Only calculate if price and cost provided
          CASE 
            WHEN ${pricePerGal !== null && zlCostValue !== null ? `true` : `false`}
            THEN ROUND((SUM(f.xhrM0) * ${tpmValue}) / 7.6 * COALESCE(c.oil_multiplier, 1.0) * (${pricePerGalValue !== null ? pricePerGalValue : 'NULL'} - ${zlCostValue !== null ? zlCostValue : 'NULL'}) * 4, 0)
            ELSE NULL
          END as risk_amount_monthly,
          -- Current margin estimate (only if price and cost provided)
          CASE 
            WHEN ${pricePerGal !== null && zlCostValue !== null ? `true` : `false`}
            THEN ROUND(((${pricePerGalValue !== null ? pricePerGalValue : 'NULL'} - ${zlCostValue !== null ? zlCostValue : 'NULL'}) / ${pricePerGalValue !== null ? pricePerGalValue : 'NULL'}) * 100, 1)
            ELSE NULL
          END as current_margin_pct
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_restaurants\` r
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_fryers\` f
          ON r.glide_rowID = f.\`2uBBn\`
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_cuisine_multipliers\` c
          ON r.glide_rowID = c.glide_rowID
        WHERE r.s8tNr = 'Open'
        GROUP BY r.glide_rowID, r.MHXYO, r.U0Jf2, c.oil_multiplier
        HAVING fryer_count >= 3  -- Only alert on medium+ accounts
      )
      SELECT 
        restaurant_id as id,
        restaurant_name as customer_name,
        'Volume Risk' as alert_type,
        severity,
        current_margin_pct as current_margin,
        CASE 
          WHEN risk_amount_monthly IS NOT NULL THEN CAST(risk_amount_monthly as INT64)
          ELSE NULL
        END as risk_amount,
        CASE 
          WHEN severity = 'HIGH' THEN 'Lock pricing now - high volume account'
          WHEN severity = 'MEDIUM' THEN 'Review margin protection options'
          ELSE 'Monitor for price changes'
        END as recommended_action,
        CASE 
          WHEN severity = 'HIGH' THEN 'Immediate action required'
          WHEN severity = 'MEDIUM' THEN 'Review within 48 hours'
          ELSE 'Monitor weekly'
        END as urgency
      FROM restaurant_risk
      ORDER BY 
        CASE severity
          WHEN 'HIGH' THEN 1
          WHEN 'MEDIUM' THEN 2
          ELSE 3
        END,
        CASE 
          WHEN ${pricePerGal !== null && zlCostValue !== null ? `true` : `false`} THEN risk_amount_monthly
          ELSE fryer_count
        END DESC
      LIMIT 20
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      return NextResponse.json([])
    }

    const alerts = results.map((row: any) => ({
      id: row.id,
      customer_name: row.customer_name,
      alert_type: row.alert_type,
      severity: row.severity,
      current_margin: row.current_margin !== null && row.current_margin !== undefined ? parseFloat(row.current_margin) : null,
      risk_amount: row.risk_amount !== null && row.risk_amount !== undefined ? parseInt(row.risk_amount) : null,
      recommended_action: row.recommended_action,
      urgency: row.urgency
    }))

    return NextResponse.json(alerts)
  } catch (error: any) {
    if (error.message?.includes('not found') || error.message?.includes('does not exist')) {
      return NextResponse.json([])
    }
    console.error('Vegas margin alerts error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
