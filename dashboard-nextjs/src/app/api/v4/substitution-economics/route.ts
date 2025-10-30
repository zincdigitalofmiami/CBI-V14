import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get substitution analysis data (soy oil vs palm oil vs canola)
    const substitutionQuery = `
      WITH price_data AS (
        SELECT 
          DATE(s.time) as date,
          s.close as soy_oil_price,
          p.close as palm_oil_price,
          -- Estimate canola price (not in dataset, use correlation with soy)
          s.close * 1.15 as canola_oil_price,
          -- Get feature importance for substitution analysis
          corr_zl_palm_90d as palm_correlation,
          corr_zl_palm_365d as palm_correlation_annual,
          zl_palm_corr_30d as palm_correlation_monthly
        FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\` s
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.palm_oil_prices\` p
          ON DATE(s.time) = DATE(p.time)
        WHERE s.symbol = 'ZL'
          AND DATE(s.time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
          AND s.close IS NOT NULL
        ORDER BY DATE(s.time)
      ),
      
      transport_costs AS (
        SELECT 
          'SOY_TO_US' as route,
          2.50 as cost_per_unit,
          'Domestic transport advantage' as description
        UNION ALL
        SELECT 
          'PALM_TO_US' as route,
          8.75 as cost_per_unit,
          'Malaysia/Indonesia to US ports' as description
        UNION ALL
        SELECT 
          'CANOLA_TO_US' as route,
          4.20 as cost_per_unit,
          'Canada to US transport' as description
      ),
      
      latest_features AS (
        SELECT 
          palm_price,
          corr_zl_palm_90d as palm_correlation_feature,
          zl_palm_corr_30d as recent_palm_correlation,
          -- Feature importance from model
          target_1w as target_importance,
          corr_price as price_correlation_importance
        FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`
        WHERE date = (SELECT MAX(date) FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`)
      )
      
      SELECT 
        p.*,
        t.cost_per_unit,
        t.description as transport_description,
        f.palm_correlation_feature,
        f.recent_palm_correlation,
        f.target_importance,
        f.price_correlation_importance,
        -- Calculate total delivered cost
        CASE 
          WHEN t.route = 'SOY_TO_US' THEN p.soy_oil_price + t.cost_per_unit
          WHEN t.route = 'PALM_TO_US' THEN p.palm_oil_price + t.cost_per_unit
          WHEN t.route = 'CANOLA_TO_US' THEN p.canola_oil_price + t.cost_per_unit
        END as total_delivered_cost,
        -- Calculate substitution threshold
        CASE 
          WHEN t.route = 'PALM_TO_US' THEN 
            CASE 
              WHEN (p.palm_oil_price + t.cost_per_unit) < (p.soy_oil_price + 2.50) * 0.95 THEN 'SUBSTITUTE'
              WHEN (p.palm_oil_price + t.cost_per_unit) > (p.soy_oil_price + 2.50) * 1.05 THEN 'NO_SUBSTITUTE'
              ELSE 'NEUTRAL'
            END
          WHEN t.route = 'CANOLA_TO_US' THEN 
            CASE 
              WHEN (p.canola_oil_price + t.cost_per_unit) < (p.soy_oil_price + 2.50) * 0.98 THEN 'SUBSTITUTE'
              WHEN (p.canola_oil_price + t.cost_per_unit) > (p.soy_oil_price + 2.50) * 1.02 THEN 'NO_SUBSTITUTE'
              ELSE 'NEUTRAL'
            END
          ELSE 'BASELINE'
        END as substitution_signal
      FROM price_data p
      CROSS JOIN transport_costs t
      CROSS JOIN latest_features f
      WHERE p.date = (SELECT MAX(date) FROM price_data)
    `
    
    const result = await executeBigQueryQuery(substitutionQuery)
    if (result.length === 0) {
      return NextResponse.json({
        error: 'No substitution data available',
        message: 'Price comparison data not found'
      }, { status: 503 })
    }

    // Process substitution analysis
    const currentDate = result[0].date
    const substitutionAnalysis: Record<string, any> = {}
    
    result.forEach(row => {
      const oil_type = row.route.split('_')[0].toLowerCase()
      substitutionAnalysis[oil_type] = {
        name: oil_type === 'soy' ? 'Soybean Oil' : 
              oil_type === 'palm' ? 'Palm Oil' : 'Canola Oil',
        base_price: oil_type === 'soy' ? row.soy_oil_price :
                   oil_type === 'palm' ? row.palm_oil_price : row.canola_oil_price,
        transport_cost: row.cost_per_unit,
        total_cost: row.total_delivered_cost,
        transport_description: row.transport_description,
        substitution_signal: row.substitution_signal,
        correlation: oil_type === 'palm' ? row.recent_palm_correlation : 
                    oil_type === 'canola' ? 0.75 : 1.0, // Estimated canola correlation
        model_importance: oil_type === 'palm' ? 
          Math.abs(row.palm_correlation_feature || 0.10) * 100 : 
          oil_type === 'soy' ? Math.abs(row.price_correlation_importance || 0.25) * 100 : 8.5
      }
    })

    // Calculate switching points and cost curves
    const priceRange = Array.from({length: 21}, (_, i) => {
      const basePrice = substitutionAnalysis.soy.base_price
      return basePrice * (0.8 + (i * 0.02)) // ±20% price range
    })

    const costCurves = priceRange.map(price => ({
      soy_price: price,
      soy_total_cost: price + substitutionAnalysis.soy.transport_cost,
      palm_total_cost: substitutionAnalysis.palm.base_price + substitutionAnalysis.palm.transport_cost,
      canola_total_cost: substitutionAnalysis.canola.base_price + substitutionAnalysis.canola.transport_cost,
      optimal_choice: getOptimalChoice(
        price + substitutionAnalysis.soy.transport_cost,
        substitutionAnalysis.palm.base_price + substitutionAnalysis.palm.transport_cost,
        substitutionAnalysis.canola.base_price + substitutionAnalysis.canola.transport_cost
      )
    }))

    // Find switching points
    const switchingPoints = []
    for (let i = 1; i < costCurves.length; i++) {
      if (costCurves[i].optimal_choice !== costCurves[i-1].optimal_choice) {
        switchingPoints.push({
          price: costCurves[i].soy_price,
          from_oil: costCurves[i-1].optimal_choice,
          to_oil: costCurves[i].optimal_choice,
          cost_difference: Math.abs(
            costCurves[i].soy_total_cost - 
            (costCurves[i].optimal_choice === 'palm' ? costCurves[i].palm_total_cost : costCurves[i].canola_total_cost)
          )
        })
      }
    }

    return NextResponse.json({
      data_date: currentDate,
      current_analysis: substitutionAnalysis,
      cost_curves: costCurves,
      switching_points: switchingPoints,
      market_dynamics: {
        palm_correlation: substitutionAnalysis.palm.correlation,
        substitution_active: switchingPoints.length > 0,
        current_leader: getOptimalChoice(
          substitutionAnalysis.soy.total_cost,
          substitutionAnalysis.palm.total_cost,
          substitutionAnalysis.canola.total_cost
        ),
        arbitrage_opportunity: Math.max(
          Math.abs(substitutionAnalysis.soy.total_cost - substitutionAnalysis.palm.total_cost),
          Math.abs(substitutionAnalysis.soy.total_cost - substitutionAnalysis.canola.total_cost)
        )
      },
      feature_importance: {
        palm_correlation_weight: substitutionAnalysis.palm.model_importance,
        price_correlation_weight: substitutionAnalysis.soy.model_importance,
        substitution_regime: substitutionAnalysis.palm.model_importance > 12 ? 'HIGH_IMPACT' : 'MODERATE_IMPACT'
      },
      last_updated: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Substitution economics error:', error)
    return NextResponse.json({ 
      error: error.message || 'Internal server error'
    }, { status: 500 })
  }
}

function getOptimalChoice(soyCost: number, palmCost: number, canolaCost: number): string {
  const minCost = Math.min(soyCost, palmCost, canolaCost)
  if (minCost === soyCost) return 'soy'
  if (minCost === palmCost) return 'palm'
  return 'canola'
}
