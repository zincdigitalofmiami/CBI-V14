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
        palm_price,
        zl_price_current,
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
    
    // Build Big 8 signals array - WITH ACTUAL PERCENTAGES FOR BAR HEIGHTS
    const big8 = [
      {
        name: 'Market Volatility',
        key: 'vix_stress',
        value: signals.feature_vix_stress,
        percentage: Math.round(signals.feature_vix_stress * 100), // 26%
        display_value: `${Math.round(signals.feature_vix_stress * 100)}%`,
        status: signals.feature_vix_stress > 0.6 ? 'CRITICAL' : signals.feature_vix_stress > 0.3 ? 'ELEVATED' : 'NORMAL',
        impact: signals.feature_vix_stress > 0.6 ? 'HIGH' : signals.feature_vix_stress > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Supply Pressure',
        key: 'harvest_pace',
        value: signals.feature_harvest_pace,
        percentage: Math.round(signals.feature_harvest_pace * 100), // 56%
        display_value: `${Math.round(signals.feature_harvest_pace * 100)}%`,
        status: signals.feature_harvest_pace > 0.7 ? 'BEARISH' : signals.feature_harvest_pace > 0.4 ? 'NEUTRAL' : 'BULLISH',
        impact: signals.feature_harvest_pace > 0.7 ? 'HIGH' : signals.feature_harvest_pace > 0.4 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'China Demand',
        key: 'china_imports',
        value: signals.china_soybean_imports_mt,
        percentage: Math.round(signals.china_soybean_imports_mt), // 0%
        display_value: `${signals.china_soybean_imports_mt.toFixed(1)} MT`,
        status: signals.china_soybean_imports_mt > 12 ? 'BULLISH' : signals.china_soybean_imports_mt > 1 ? 'NEUTRAL' : 'BEARISH',
        impact: signals.china_soybean_imports_mt > 12 ? 'HIGH' : signals.china_soybean_imports_mt > 1 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Trade War Risk',
        key: 'tariff_threat',
        value: signals.feature_tariff_threat,
        percentage: Math.round(signals.feature_tariff_threat * 100), // 20%
        display_value: `${Math.round(signals.feature_tariff_threat * 100)}%`,
        status: signals.feature_tariff_threat > 0.6 ? 'CRITICAL' : signals.feature_tariff_threat > 0.3 ? 'ELEVATED' : 'LOW',
        impact: signals.feature_tariff_threat > 0.6 ? 'HIGH' : signals.feature_tariff_threat > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Argentina Competition',
        key: 'argentina_tax',
        value: signals.argentina_export_tax,
        percentage: Math.round(signals.argentina_export_tax), // 0%
        display_value: `${signals.argentina_export_tax.toFixed(0)}% Tax`,
        status: signals.argentina_export_tax < 5 ? 'BEARISH' : signals.argentina_export_tax > 15 ? 'BULLISH' : 'NEUTRAL',
        impact: signals.argentina_export_tax < 5 ? 'HIGH' : signals.argentina_export_tax > 15 ? 'LOW' : 'MEDIUM'
      },
      {
        name: 'Industrial Demand',
        key: 'industrial_demand',
        value: signals.industrial_demand_index,
        percentage: Math.round(signals.industrial_demand_index * 100), // 49%
        display_value: `${Math.round(signals.industrial_demand_index * 100)}%`,
        status: signals.industrial_demand_index > 0.6 ? 'BULLISH' : signals.industrial_demand_index > 0.4 ? 'NEUTRAL' : 'BEARISH',
        impact: signals.industrial_demand_index > 0.6 ? 'HIGH' : signals.industrial_demand_index > 0.4 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'China Relations',
        key: 'china_relations',
        value: signals.feature_china_relations,
        percentage: Math.round(signals.feature_china_relations * 100), // 20%
        display_value: `${Math.round(signals.feature_china_relations * 100)}%`,
        status: signals.feature_china_relations > 0.6 ? 'BULLISH' : signals.feature_china_relations > 0.3 ? 'NEUTRAL' : 'BEARISH',
        impact: signals.feature_china_relations > 0.6 ? 'HIGH' : signals.feature_china_relations > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        name: 'Palm Substitution',
        key: 'palm_spread',
        value: Math.abs(signals.palm_price - signals.zl_price_current),
        percentage: Math.min(100, Math.round(Math.abs(signals.palm_price - signals.zl_price_current) * 2)), // Scale to %
        display_value: `$${Math.abs(signals.palm_price - signals.zl_price_current).toFixed(2)}`,
        status: Math.abs(signals.palm_price - signals.zl_price_current) < 10 ? 'BEARISH' : Math.abs(signals.palm_price - signals.zl_price_current) > 20 ? 'BULLISH' : 'NEUTRAL',
        impact: Math.abs(signals.palm_price - signals.zl_price_current) < 10 ? 'HIGH' : Math.abs(signals.palm_price - signals.zl_price_current) > 20 ? 'LOW' : 'MEDIUM'
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

