import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get latest Big 8 signals from training dataset
    const signalsQuery = `
      SELECT 
        feature_vix_stress,
        feature_harvest_pace,
        feature_china_relations,
        feature_tariff_threat,
        china_soybean_imports_mt,
        argentina_export_tax,
        industrial_demand_index,
        palm_soy_spread,
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
    
    // Build Big 8 signals array
    const big8 = [
      {
        name: 'Market Volatility',
        key: 'vix_stress',
        value: signals.feature_vix_stress,
        status: signals.feature_vix_stress > 0.6 ? 'CRITICAL' : signals.feature_vix_stress > 0.3 ? 'ELEVATED' : 'NORMAL',
        impact: signals.feature_vix_stress > 0.6 ? 'HIGH' : signals.feature_vix_stress > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Supply Pressure',
        key: 'harvest_pace',
        value: signals.feature_harvest_pace,
        status: signals.feature_harvest_pace > 0.7 ? 'BEARISH' : signals.feature_harvest_pace > 0.4 ? 'NEUTRAL' : 'BULLISH',
        impact: signals.feature_harvest_pace > 0.7 ? 'HIGH' : signals.feature_harvest_pace > 0.4 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'China Demand',
        key: 'china_imports',
        value: signals.china_soybean_imports_mt,
        status: signals.china_soybean_imports_mt > 12 ? 'BULLISH' : signals.china_soybean_imports_mt > 8 ? 'NEUTRAL' : 'BEARISH',
        impact: signals.china_soybean_imports_mt > 12 ? 'HIGH' : signals.china_soybean_imports_mt > 8 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Trade War Risk',
        key: 'tariff_threat',
        value: signals.feature_tariff_threat,
        status: signals.feature_tariff_threat > 0.6 ? 'CRITICAL' : signals.feature_tariff_threat > 0.3 ? 'ELEVATED' : 'LOW',
        impact: signals.feature_tariff_threat > 0.6 ? 'HIGH' : signals.feature_tariff_threat > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Argentina Competition',
        key: 'argentina_tax',
        value: signals.argentina_export_tax,
        status: signals.argentina_export_tax < 5 ? 'BEARISH' : signals.argentina_export_tax > 15 ? 'BULLISH' : 'NEUTRAL',
        impact: signals.argentina_export_tax < 5 ? 'HIGH' : signals.argentina_export_tax > 15 ? 'LOW' : 'MEDIUM'
      },
      {
        name: 'Industrial Demand',
        key: 'industrial_demand',
        value: signals.industrial_demand_index,
        status: signals.industrial_demand_index > 0.6 ? 'BULLISH' : signals.industrial_demand_index > 0.4 ? 'NEUTRAL' : 'BEARISH',
        impact: signals.industrial_demand_index > 0.6 ? 'HIGH' : signals.industrial_demand_index > 0.4 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'China Relations',
        key: 'china_relations',
        value: signals.feature_china_relations,
        status: signals.feature_china_relations > 0.6 ? 'BULLISH' : signals.feature_china_relations > 0.3 ? 'NEUTRAL' : 'BEARISH',
        impact: signals.feature_china_relations > 0.6 ? 'HIGH' : signals.feature_china_relations > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Palm Substitution',
        key: 'palm_spread',
        value: signals.palm_soy_spread,
        status: signals.palm_soy_spread < 10 ? 'BEARISH' : signals.palm_soy_spread > 20 ? 'BULLISH' : 'NEUTRAL',
        impact: signals.palm_soy_spread < 10 ? 'HIGH' : signals.palm_soy_spread > 20 ? 'LOW' : 'MEDIUM'
      }
    ]

    return NextResponse.json({
      signals: big8,
      data_date: signals.date,
      updated_at: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Big 8 signals error:', error)
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error',
        details: 'Cannot fetch BigQuery Big 8 signals'
      },
      { status: 500 }
    )
  }
}

