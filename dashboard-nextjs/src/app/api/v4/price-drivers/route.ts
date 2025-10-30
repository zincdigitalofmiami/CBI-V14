import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get latest feature importance from Big-8 table
    const driversQuery = `
      WITH latest_features AS (
        SELECT 
          date,
          -- VIX Stress (Market Fear)
          feature_vix_stress * 100 as vix_stress_pct,
          -- China Relations Impact
          feature_china_relations * 100 as china_relations_pct,
          -- Harvest Pace Pressure
          feature_harvest_pace * 100 as harvest_pace_pct,
          -- Tariff Threat Level
          feature_tariff_threat * 100 as tariff_threat_pct,
          -- Current ZL Price for dollar impact calculation
          zl_price_current,
          -- Raw feature values for impact calculation
          china_soybean_imports_mt,
          argentina_export_tax,
          industrial_demand_index,
          palm_price,
          -- Volatility indicators
          feature_vix_stress as vix_raw,
          -- Correlation features
          zl_crude_corr_30d,
          zl_palm_corr_30d,
          zl_vix_corr_30d
        FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`
        WHERE date = (SELECT MAX(date) FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`)
      )
      SELECT * FROM latest_features
    `
    
    const result = await executeBigQueryQuery(driversQuery)
    if (result.length === 0) {
      return NextResponse.json({
        error: 'No feature data available',
        message: 'Big-8 feature table is empty'
      }, { status: 503 })
    }

    const data = result[0]
    const currentPrice = data.zl_price_current || 50.0

    // Calculate dollar impacts based on feature importance and correlations
    const drivers = [
      {
        id: 'vix_stress',
        name: 'Market Volatility (VIX)',
        technical_name: 'feature_vix_stress',
        current_value: data.vix_stress_pct,
        impact_score: Math.abs(data.vix_stress_pct),
        dollar_impact: (data.vix_stress_pct / 100) * currentPrice * 0.15, // VIX has ~15% price correlation
        direction: data.vix_stress_pct > 50 ? 'BEARISH' : 'BULLISH',
        explanation: data.vix_stress_pct > 70 ? 'Extreme fear driving commodity selloff' :
                    data.vix_stress_pct > 50 ? 'Market stress pressuring oil prices' :
                    data.vix_stress_pct > 30 ? 'Moderate volatility - neutral impact' :
                    'Low volatility supporting steady demand',
        confidence: data.vix_stress_pct > 60 ? 'HIGH' : data.vix_stress_pct > 30 ? 'MEDIUM' : 'LOW'
      },
      {
        id: 'china_demand',
        name: 'China Import Demand',
        technical_name: 'china_soybean_imports_mt',
        current_value: data.china_soybean_imports_mt,
        impact_score: Math.abs(data.china_relations_pct),
        dollar_impact: (data.china_relations_pct / 100) * currentPrice * 0.25, // China has ~25% price impact
        direction: data.china_relations_pct > 0 ? 'BULLISH' : 'BEARISH',
        explanation: data.china_soybean_imports_mt > 8 ? 'Strong Chinese buying supporting prices' :
                    data.china_soybean_imports_mt > 6 ? 'Steady Chinese demand' :
                    data.china_soybean_imports_mt > 4 ? 'Moderate Chinese imports' :
                    'Weak Chinese demand pressuring prices',
        confidence: Math.abs(data.china_relations_pct) > 60 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'harvest_pressure',
        name: 'Harvest Supply Pressure',
        technical_name: 'feature_harvest_pace',
        current_value: data.harvest_pace_pct,
        impact_score: Math.abs(data.harvest_pace_pct),
        dollar_impact: -(data.harvest_pace_pct / 100) * currentPrice * 0.20, // Harvest pressure negative
        direction: data.harvest_pace_pct > 50 ? 'BEARISH' : 'BULLISH',
        explanation: data.harvest_pace_pct > 80 ? 'Record harvest pace pressuring prices' :
                    data.harvest_pace_pct > 60 ? 'Fast harvest increasing supply' :
                    data.harvest_pace_pct > 40 ? 'Normal harvest pace' :
                    'Slow harvest supporting prices',
        confidence: data.harvest_pace_pct > 70 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'tariff_risk',
        name: 'Trade War Risk',
        technical_name: 'feature_tariff_threat',
        current_value: data.tariff_threat_pct,
        impact_score: Math.abs(data.tariff_threat_pct),
        dollar_impact: (data.tariff_threat_pct / 100) * currentPrice * 0.18, // Trade uncertainty premium
        direction: data.tariff_threat_pct > 50 ? 'BULLISH' : 'BEARISH',
        explanation: data.tariff_threat_pct > 80 ? 'High trade war risk boosting US premiums' :
                    data.tariff_threat_pct > 60 ? 'Elevated trade tensions' :
                    data.tariff_threat_pct > 30 ? 'Moderate trade uncertainty' :
                    'Low trade risk - normal flows',
        confidence: data.tariff_threat_pct > 70 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'argentina_crisis',
        name: 'Argentina Export Crisis',
        technical_name: 'argentina_export_tax',
        current_value: data.argentina_export_tax,
        impact_score: Math.abs(data.argentina_export_tax * 2), // Scale for display
        dollar_impact: (data.argentina_export_tax / 100) * currentPrice * 0.12,
        direction: data.argentina_export_tax > 30 ? 'BULLISH' : 'NEUTRAL',
        explanation: data.argentina_export_tax > 40 ? 'High export taxes limiting Argentine supply' :
                    data.argentina_export_tax > 30 ? 'Export taxes supporting global prices' :
                    'Normal Argentine export flows',
        confidence: data.argentina_export_tax > 35 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'industrial_demand',
        name: 'Industrial Demand Index',
        technical_name: 'industrial_demand_index',
        current_value: data.industrial_demand_index,
        impact_score: Math.abs((data.industrial_demand_index - 100) / 2), // Normalize around 100
        dollar_impact: ((data.industrial_demand_index - 100) / 100) * currentPrice * 0.15,
        direction: data.industrial_demand_index > 105 ? 'BULLISH' : data.industrial_demand_index < 95 ? 'BEARISH' : 'NEUTRAL',
        explanation: data.industrial_demand_index > 110 ? 'Strong industrial demand boosting consumption' :
                    data.industrial_demand_index > 105 ? 'Above-normal industrial demand' :
                    data.industrial_demand_index > 95 ? 'Normal industrial demand' :
                    'Weak industrial demand pressuring prices',
        confidence: Math.abs(data.industrial_demand_index - 100) > 10 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'palm_substitution',
        name: 'Palm Oil Competition',
        technical_name: 'palm_price',
        current_value: data.palm_price,
        impact_score: Math.abs(data.zl_palm_corr_30d * 100),
        dollar_impact: -(data.zl_palm_corr_30d * (data.palm_price - 800) / 100) * 0.10, // Palm competition effect
        direction: data.palm_price > 900 ? 'BULLISH' : 'BEARISH',
        explanation: data.palm_price > 1000 ? 'High palm prices boosting soy oil demand' :
                    data.palm_price > 900 ? 'Palm oil premium supporting soy prices' :
                    data.palm_price > 800 ? 'Normal palm oil competition' :
                    'Cheap palm oil pressuring soy oil demand',
        confidence: Math.abs(data.zl_palm_corr_30d) > 0.6 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'crude_energy',
        name: 'Crude Oil Energy Complex',
        technical_name: 'zl_crude_corr_30d',
        current_value: data.zl_crude_corr_30d * 100,
        impact_score: Math.abs(data.zl_crude_corr_30d * 100),
        dollar_impact: data.zl_crude_corr_30d * currentPrice * 0.08, // Energy correlation
        direction: data.zl_crude_corr_30d > 0.3 ? 'BULLISH' : 'BEARISH',
        explanation: data.zl_crude_corr_30d > 0.5 ? 'Strong energy complex correlation lifting oils' :
                    data.zl_crude_corr_30d > 0.2 ? 'Moderate energy sector support' :
                    data.zl_crude_corr_30d > -0.2 ? 'Neutral energy impact' :
                    'Energy weakness pressuring vegetable oils',
        confidence: Math.abs(data.zl_crude_corr_30d) > 0.4 ? 'HIGH' : 'MEDIUM'
      }
    ]

    // Sort by absolute impact score (most important first)
    drivers.sort((a, b) => Math.abs(b.impact_score) - Math.abs(a.impact_score))

    return NextResponse.json({
      data_date: data.date,
      current_price: currentPrice,
      total_drivers: drivers.length,
      net_dollar_impact: drivers.reduce((sum, d) => sum + d.dollar_impact, 0),
      drivers: drivers.slice(0, 8), // Top 8 drivers
      market_regime: data.vix_raw > 0.7 ? 'HIGH_VOLATILITY' : 
                    data.vix_raw > 0.5 ? 'ELEVATED_VOLATILITY' : 
                    data.vix_raw > 0.3 ? 'NORMAL_VOLATILITY' : 'LOW_VOLATILITY',
      last_updated: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Price drivers error:', error)
    return NextResponse.json({ 
      error: error.message || 'Internal server error',
      drivers: []
    }, { status: 500 })
  }
}
