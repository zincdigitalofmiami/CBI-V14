import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get the actual Big-8 feature values from the training dataset
    const signalsQuery = `
      SELECT 
        feature_vix_stress,
        feature_harvest_pace,
        feature_china_relations,
        feature_tariff_threat,
        feature_geopolitical_volatility,
        feature_biofuel_cascade,
        feature_hidden_correlation,
        feature_biofuel_ethanol,
        big8_composite_score,
        market_regime,
        date
      FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`
      WHERE date IS NOT NULL
      ORDER BY date DESC
      LIMIT 1
    `
    
    const result = await executeBigQueryQuery(signalsQuery)
    
    if (result.length === 0) {
      return NextResponse.json({
        error: 'No signal data available',
        message: 'Training dataset is empty'
      }, { status: 503 })
    }

    const signals = result[0]
    
    // Build Big 8 signals array using ACTUAL feature values only
    const big8 = [
      {
        name: 'Market Volatility',
        key: 'vix_stress',
        value: signals.feature_vix_stress,
        percentage: Math.round((signals.feature_vix_stress || 0) * 100),
        display_value: (signals.feature_vix_stress || 0).toFixed(3),
        status: signals.feature_vix_stress > 0.6 ? 'CRITICAL' : signals.feature_vix_stress > 0.3 ? 'ELEVATED' : 'NORMAL',
        impact: signals.feature_vix_stress > 0.6 ? 'HIGH' : signals.feature_vix_stress > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Harvest Pace',
        key: 'harvest_pace',
        value: signals.feature_harvest_pace,
        percentage: Math.round((signals.feature_harvest_pace || 0) * 100),
        display_value: (signals.feature_harvest_pace || 0).toFixed(3),
        status: signals.feature_harvest_pace > 0.7 ? 'BEARISH' : signals.feature_harvest_pace > 0.4 ? 'NEUTRAL' : 'BULLISH',
        impact: signals.feature_harvest_pace > 0.7 ? 'HIGH' : signals.feature_harvest_pace > 0.4 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'China Relations',
        key: 'china_relations',
        value: signals.feature_china_relations,
        percentage: Math.round(Math.abs(signals.feature_china_relations || 0) * 100),
        display_value: (signals.feature_china_relations || 0).toFixed(3),
        status: signals.feature_china_relations > 0.3 ? 'BULLISH' : signals.feature_china_relations < -0.3 ? 'BEARISH' : 'NEUTRAL',
        impact: Math.abs(signals.feature_china_relations || 0) > 0.5 ? 'HIGH' : Math.abs(signals.feature_china_relations || 0) > 0.2 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Tariff Risk',
        key: 'tariff_threat',
        value: signals.feature_tariff_threat,
        percentage: Math.round((signals.feature_tariff_threat || 0) * 100),
        display_value: (signals.feature_tariff_threat || 0).toFixed(3),
        status: signals.feature_tariff_threat > 0.6 ? 'CRITICAL' : signals.feature_tariff_threat > 0.3 ? 'ELEVATED' : 'LOW',
        impact: signals.feature_tariff_threat > 0.6 ? 'HIGH' : signals.feature_tariff_threat > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Geopolitical Risk',
        key: 'geopolitical_volatility',
        value: signals.feature_geopolitical_volatility,
        percentage: Math.round((signals.feature_geopolitical_volatility || 0) * 100),
        display_value: (signals.feature_geopolitical_volatility || 0).toFixed(3),
        status: signals.feature_geopolitical_volatility > 0.6 ? 'CRITICAL' : signals.feature_geopolitical_volatility > 0.3 ? 'ELEVATED' : 'NORMAL',
        impact: signals.feature_geopolitical_volatility > 0.6 ? 'HIGH' : signals.feature_geopolitical_volatility > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Biofuel Demand',
        key: 'biofuel_cascade',
        value: signals.feature_biofuel_cascade,
        percentage: Math.round((signals.feature_biofuel_cascade || 0) * 100),
        display_value: (signals.feature_biofuel_cascade || 0).toFixed(3),
        status: signals.feature_biofuel_cascade > 0.6 ? 'BULLISH' : signals.feature_biofuel_cascade > 0.3 ? 'NEUTRAL' : 'BEARISH',
        impact: signals.feature_biofuel_cascade > 0.6 ? 'HIGH' : signals.feature_biofuel_cascade > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Hidden Correlations',
        key: 'hidden_correlation',
        value: signals.feature_hidden_correlation,
        percentage: Math.round(Math.abs(signals.feature_hidden_correlation || 0) * 100),
        display_value: (signals.feature_hidden_correlation || 0).toFixed(3),
        status: Math.abs(signals.feature_hidden_correlation || 0) > 0.5 ? 'SIGNIFICANT' : Math.abs(signals.feature_hidden_correlation || 0) > 0.3 ? 'MODERATE' : 'MINIMAL',
        impact: Math.abs(signals.feature_hidden_correlation || 0) > 0.5 ? 'HIGH' : Math.abs(signals.feature_hidden_correlation || 0) > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Ethanol Impact',
        key: 'biofuel_ethanol',
        value: signals.feature_biofuel_ethanol,
        percentage: Math.round((signals.feature_biofuel_ethanol || 0) * 100),
        display_value: (signals.feature_biofuel_ethanol || 0).toFixed(3),
        status: signals.feature_biofuel_ethanol > 0.6 ? 'BULLISH' : signals.feature_biofuel_ethanol > 0.3 ? 'NEUTRAL' : 'BEARISH',
        impact: signals.feature_biofuel_ethanol > 0.6 ? 'HIGH' : signals.feature_biofuel_ethanol > 0.3 ? 'MEDIUM' : 'LOW'
      }
    ]

    return NextResponse.json({
      data_date: signals.date,
      signals: big8,
      composite_score: signals.big8_composite_score,
      market_regime: signals.market_regime,
      last_updated: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Big-8 signals error:', error)
    return NextResponse.json({ 
      error: error.message || 'Internal server error',
      details: 'Cannot fetch BigQuery Big 8 signals'
    }, { status: 500 })
  }
}