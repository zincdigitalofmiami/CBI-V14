import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get latest risk factors from Big-8 feature table
    const riskQuery = `
      WITH latest_risk_data AS (
        SELECT 
          date,
          -- Price Volatility Risk (from VIX and price movements)
          feature_vix_stress * 100 as vix_stress_pct,
          STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) / 
            AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) * 100 as price_volatility,
          
          -- FX Risk (USD strength impact)
          ABS(zl_dxy_corr_30d) * 100 as fx_risk_score,
          
          -- Weather Risk (temperature and precipitation extremes)
          CASE 
            WHEN ABS(brazil_temp_max - 25) > 10 OR ABS(us_temp_max - 20) > 15 THEN 80
            WHEN ABS(brazil_temp_max - 25) > 5 OR ABS(us_temp_max - 20) > 8 THEN 60
            WHEN brazil_precip > 150 OR us_precip > 100 THEN 70
            WHEN brazil_precip < 20 OR us_precip < 30 THEN 65
            ELSE 30
          END as weather_risk_score,
          
          -- Supply Tightness (harvest pace and stocks)
          CASE
            WHEN feature_harvest_pace > 0.8 THEN 20  -- Fast harvest = low supply risk
            WHEN feature_harvest_pace > 0.6 THEN 40
            WHEN feature_harvest_pace > 0.4 THEN 60
            ELSE 80  -- Slow harvest = high supply risk
          END as supply_risk_score,
          
          -- Demand Shock Risk (China relations and industrial demand)
          CASE
            WHEN china_soybean_imports_mt < 4 THEN 85  -- Low China demand = high risk
            WHEN china_soybean_imports_mt < 6 THEN 60
            WHEN china_soybean_imports_mt < 8 THEN 40
            ELSE 20  -- High China demand = low risk
          END + 
          CASE
            WHEN industrial_demand_index < 90 THEN 30
            WHEN industrial_demand_index < 95 THEN 20
            WHEN industrial_demand_index < 105 THEN 10
            ELSE 5
          END as demand_risk_score,
          
          -- Policy Risk (tariff threats and trade war)
          feature_tariff_threat * 100 as policy_risk_score,
          
          -- Feature importance weights for overlay
          corr_price as price_importance,
          target_1w as target_1w_importance,
          corr_zl_palm_90d as palm_correlation_importance,
          corr_zl_crude_365d as crude_correlation_importance,
          crush_margin_30d_ma as crush_margin_importance,
          seasonal_sin as seasonal_importance
          
        FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`
        WHERE date = (SELECT MAX(date) FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`)
      )
      SELECT * FROM latest_risk_data
    `
    
    const result = await executeBigQueryQuery(riskQuery)
    if (result.length === 0) {
      return NextResponse.json({
        error: 'No risk data available',
        message: 'Big-8 risk features not found'
      }, { status: 503 })
    }

    const data = result[0]
    
    // Normalize all risk scores to 0-100 scale
    const riskFactors = [
      {
        factor: 'Price Volatility',
        value: Math.min(100, Math.max(0, data.price_volatility || data.vix_stress_pct || 30)),
        description: data.vix_stress_pct > 70 ? 'Extreme price swings expected' :
                    data.vix_stress_pct > 50 ? 'High volatility environment' :
                    data.vix_stress_pct > 30 ? 'Moderate price fluctuations' :
                    'Stable price environment',
        top_driver: 'VIX Stress',
        importance: Math.abs(data.price_importance || 0.15) * 100
      },
      {
        factor: 'FX Risk',
        value: Math.min(100, Math.max(0, data.fx_risk_score || 25)),
        description: data.fx_risk_score > 70 ? 'USD strength severely impacting commodities' :
                    data.fx_risk_score > 50 ? 'Significant FX headwinds' :
                    data.fx_risk_score > 30 ? 'Moderate currency impact' :
                    'Minimal FX risk',
        top_driver: 'USD/CNY Correlation',
        importance: Math.abs(data.crude_correlation_importance || 0.08) * 100
      },
      {
        factor: 'Weather Risk',
        value: Math.min(100, Math.max(0, data.weather_risk_score || 35)),
        description: data.weather_risk_score > 75 ? 'Severe weather threatening crops' :
                    data.weather_risk_score > 60 ? 'Elevated weather concerns' :
                    data.weather_risk_score > 40 ? 'Normal weather variability' :
                    'Favorable weather conditions',
        top_driver: 'Brazil Temperature',
        importance: Math.abs(data.seasonal_importance || 0.06) * 100
      },
      {
        factor: 'Supply Tightness',
        value: Math.min(100, Math.max(0, data.supply_risk_score || 40)),
        description: data.supply_risk_score > 75 ? 'Critical supply shortages developing' :
                    data.supply_risk_score > 60 ? 'Tight supply conditions' :
                    data.supply_risk_score > 40 ? 'Adequate supply levels' :
                    'Abundant supply available',
        top_driver: 'Harvest Pace',
        importance: Math.abs(data.target_1w_importance || 0.12) * 100
      },
      {
        factor: 'Demand Shock',
        value: Math.min(100, Math.max(0, data.demand_risk_score || 45)),
        description: data.demand_risk_score > 75 ? 'Major demand disruption risk' :
                    data.demand_risk_score > 60 ? 'Elevated demand uncertainty' :
                    data.demand_risk_score > 40 ? 'Stable demand outlook' :
                    'Strong demand fundamentals',
        top_driver: 'China Imports',
        importance: Math.abs(data.palm_correlation_importance || 0.10) * 100
      },
      {
        factor: 'Policy Risk',
        value: Math.min(100, Math.max(0, data.policy_risk_score || 30)),
        description: data.policy_risk_score > 75 ? 'High trade war escalation risk' :
                    data.policy_risk_score > 60 ? 'Elevated policy uncertainty' :
                    data.policy_risk_score > 40 ? 'Moderate regulatory risk' :
                    'Stable policy environment',
        top_driver: 'Tariff Threat',
        importance: Math.abs(data.crush_margin_importance || 0.07) * 100
      }
    ]

    // Calculate overall risk score
    const overallRisk = riskFactors.reduce((sum, factor) => sum + factor.value, 0) / riskFactors.length
    
    // Determine risk regime
    const riskRegime = overallRisk > 70 ? 'CRITICAL' :
                      overallRisk > 55 ? 'HIGH' :
                      overallRisk > 40 ? 'MODERATE' :
                      overallRisk > 25 ? 'LOW' : 'MINIMAL'

    return NextResponse.json({
      data_date: data.date,
      overall_risk_score: Math.round(overallRisk),
      risk_regime: riskRegime,
      risk_factors: riskFactors,
      feature_overlays: {
        most_important: riskFactors.reduce((max, factor) => 
          factor.importance > max.importance ? factor : max
        ),
        top_3_drivers: riskFactors
          .sort((a, b) => b.importance - a.importance)
          .slice(0, 3)
          .map(f => ({ name: f.top_driver, importance: f.importance }))
      },
      market_stress_indicators: {
        vix_level: data.vix_stress_pct || 20,
        price_volatility: data.price_volatility || 15,
        correlation_breakdown: data.fx_risk_score > 50
      },
      last_updated: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Risk radar error:', error)
    return NextResponse.json({ 
      error: error.message || 'Internal server error'
    }, { status: 500 })
  }
}
