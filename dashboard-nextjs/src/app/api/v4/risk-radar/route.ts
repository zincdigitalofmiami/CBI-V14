import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get latest risk factors from Big-8 features - ONLY COLUMNS THAT EXIST
    const riskQuery = `
      SELECT 
        date,
        feature_vix_stress,
        feature_harvest_pace,
        feature_china_relations,
        feature_tariff_threat,
        feature_geopolitical_volatility,
        feature_biofuel_cascade,
        feature_hidden_correlation,
        feature_biofuel_ethanol,
        big8_composite_score,
        market_regime
      FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`
      WHERE date = (SELECT MAX(date) FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`)
    `
    
    const result = await executeBigQueryQuery(riskQuery)
    if (result.length === 0) {
      return NextResponse.json({
        error: 'No risk data available',
        message: 'Big-8 risk features not found'
      }, { status: 503 })
    }

    const data = result[0]
    
    // Calculate risk scores using ONLY real Big-8 feature values (0-1 scale)
    // Convert to 0-100 scale for display
    const riskFactors = [
      {
        factor: 'Price Volatility',
        value: Math.min(100, Math.max(0, data.feature_vix_stress * 100)),
        description: data.feature_vix_stress > 0.7 ? 'Extreme price swings expected' :
                    data.feature_vix_stress > 0.5 ? 'High volatility environment' :
                    data.feature_vix_stress > 0.3 ? 'Moderate price fluctuations' :
                    'Stable price environment',
        top_driver: 'VIX Stress',
        importance: Math.abs(data.feature_vix_stress) * 100
      },
      {
        factor: 'FX Risk',
        value: Math.min(100, Math.max(0, data.feature_geopolitical_volatility * 100)),
        description: data.feature_geopolitical_volatility > 0.7 ? 'High geopolitical currency risk' :
                    data.feature_geopolitical_volatility > 0.5 ? 'Elevated FX uncertainty' :
                    data.feature_geopolitical_volatility > 0.3 ? 'Moderate currency impact' :
                    'Minimal FX risk',
        top_driver: 'Geopolitical Volatility',
        importance: Math.abs(data.feature_geopolitical_volatility) * 100
      },
      {
        factor: 'Weather Risk',
        value: Math.min(100, Math.max(0, data.feature_harvest_pace * 50)), // Harvest pace as weather proxy
        description: data.feature_harvest_pace > 0.8 ? 'Fast harvest - good weather' :
                    data.feature_harvest_pace > 0.6 ? 'Normal harvest conditions' :
                    data.feature_harvest_pace > 0.4 ? 'Slow harvest - weather concerns' :
                    'Weather impacting harvest',
        top_driver: 'Harvest Pace',
        importance: Math.abs(data.feature_harvest_pace) * 100
      },
      {
        factor: 'Supply Tightness',
        value: Math.min(100, Math.max(0, (1 - data.feature_harvest_pace) * 100)), // Inverse of harvest pace
        description: data.feature_harvest_pace < 0.3 ? 'Critical supply shortages' :
                    data.feature_harvest_pace < 0.5 ? 'Tight supply conditions' :
                    data.feature_harvest_pace < 0.7 ? 'Adequate supply levels' :
                    'Abundant supply available',
        top_driver: 'Harvest Pace',
        importance: Math.abs(data.feature_harvest_pace) * 100
      },
      {
        factor: 'Demand Shock',
        value: Math.min(100, Math.max(0, Math.abs(data.feature_china_relations) * 100)),
        description: Math.abs(data.feature_china_relations) > 0.7 ? 'Major demand disruption risk' :
                    Math.abs(data.feature_china_relations) > 0.5 ? 'Elevated demand uncertainty' :
                    Math.abs(data.feature_china_relations) > 0.3 ? 'Stable demand outlook' :
                    'Strong demand fundamentals',
        top_driver: 'China Relations',
        importance: Math.abs(data.feature_china_relations) * 100
      },
      {
        factor: 'Policy Risk',
        value: Math.min(100, Math.max(0, data.feature_tariff_threat * 100)),
        description: data.feature_tariff_threat > 0.7 ? 'High trade war escalation risk' :
                    data.feature_tariff_threat > 0.5 ? 'Elevated policy uncertainty' :
                    data.feature_tariff_threat > 0.3 ? 'Moderate regulatory risk' :
                    'Stable policy environment',
        top_driver: 'Tariff Threat',
        importance: Math.abs(data.feature_tariff_threat) * 100
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
        vix_level: data.feature_vix_stress * 100,
        big8_composite: data.big8_composite_score,
        market_regime: data.market_regime,
        hidden_correlations: Math.abs(data.feature_hidden_correlation) * 100
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
