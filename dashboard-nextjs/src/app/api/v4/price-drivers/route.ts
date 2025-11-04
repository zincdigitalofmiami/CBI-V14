import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get latest Big-8 features (only columns that actually exist)
    const featuresQuery = `
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
    
    const featuresResult = await executeBigQueryQuery(featuresQuery)
    if (featuresResult.length === 0) {
      return NextResponse.json({
        error: 'No feature data available',
        message: 'Big-8 feature table is empty or stale'
      }, { status: 503 })
    }

    // Get current price from actual price table
    const priceQuery = `
      SELECT close as current_price
      FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`
      ORDER BY time DESC
      LIMIT 1
    `
    const priceResult = await executeBigQueryQuery(priceQuery)
    if (priceResult.length === 0 || !priceResult[0]?.current_price) {
      return NextResponse.json({
        error: 'No price data available',
        message: 'Current price not found - cannot calculate dollar impacts'
      }, { status: 503 })
    }

    const features = featuresResult[0]
    const currentPrice = priceResult[0].current_price

    // Build drivers using ONLY real feature values from Big-8
    // No random math - use actual feature values scaled to dollar impact
    const drivers = [
      {
        id: 'vix_stress',
        name: 'Market Volatility (VIX)',
        technical_name: 'feature_vix_stress',
        current_value: features.feature_vix_stress,
        impact_score: Math.abs(features.feature_vix_stress),
        dollar_impact: features.feature_vix_stress * currentPrice,
        direction: features.feature_vix_stress > 0.5 ? 'BEARISH' : features.feature_vix_stress > 0.3 ? 'NEUTRAL' : 'BULLISH',
        explanation: features.feature_vix_stress > 0.7 ? 'Extreme market volatility' :
                    features.feature_vix_stress > 0.5 ? 'Elevated volatility' :
                    features.feature_vix_stress > 0.3 ? 'Normal volatility' :
                    'Low volatility',
        confidence: features.feature_vix_stress > 0.6 ? 'HIGH' : features.feature_vix_stress > 0.3 ? 'MEDIUM' : 'LOW'
      },
      {
        id: 'harvest_pace',
        name: 'Harvest Supply Pressure',
        technical_name: 'feature_harvest_pace',
        current_value: features.feature_harvest_pace,
        impact_score: Math.abs(features.feature_harvest_pace),
        dollar_impact: -features.feature_harvest_pace * currentPrice, // Negative impact
        direction: features.feature_harvest_pace > 0.5 ? 'BEARISH' : 'BULLISH',
        explanation: features.feature_harvest_pace > 0.7 ? 'Fast harvest pace increasing supply' :
                    features.feature_harvest_pace > 0.5 ? 'Normal harvest pace' :
                    'Slow harvest pace',
        confidence: features.feature_harvest_pace > 0.6 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'china_relations',
        name: 'China Relations Impact',
        technical_name: 'feature_china_relations',
        current_value: features.feature_china_relations,
        impact_score: Math.abs(features.feature_china_relations),
        dollar_impact: features.feature_china_relations * currentPrice,
        direction: features.feature_china_relations > 0.3 ? 'BULLISH' : features.feature_china_relations < -0.3 ? 'BEARISH' : 'NEUTRAL',
        explanation: features.feature_china_relations > 0.5 ? 'Strong China demand' :
                    features.feature_china_relations > 0.3 ? 'Positive China relations' :
                    features.feature_china_relations < -0.3 ? 'Negative China relations' :
                    'Neutral China relations',
        confidence: Math.abs(features.feature_china_relations) > 0.5 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'tariff_threat',
        name: 'Trade War Risk',
        technical_name: 'feature_tariff_threat',
        current_value: features.feature_tariff_threat,
        impact_score: Math.abs(features.feature_tariff_threat),
        dollar_impact: features.feature_tariff_threat * currentPrice,
        direction: features.feature_tariff_threat > 0.5 ? 'BEARISH' : 'NEUTRAL',
        explanation: features.feature_tariff_threat > 0.7 ? 'High trade war risk' :
                    features.feature_tariff_threat > 0.5 ? 'Elevated trade tensions' :
                    'Low trade risk',
        confidence: features.feature_tariff_threat > 0.6 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'geopolitical_volatility',
        name: 'Geopolitical Risk',
        technical_name: 'feature_geopolitical_volatility',
        current_value: features.feature_geopolitical_volatility,
        impact_score: Math.abs(features.feature_geopolitical_volatility),
        dollar_impact: features.feature_geopolitical_volatility * currentPrice,
        direction: features.feature_geopolitical_volatility > 0.5 ? 'BEARISH' : 'NEUTRAL',
        explanation: features.feature_geopolitical_volatility > 0.7 ? 'High geopolitical risk' :
                    features.feature_geopolitical_volatility > 0.5 ? 'Elevated geopolitical tensions' :
                    'Normal geopolitical conditions',
        confidence: features.feature_geopolitical_volatility > 0.6 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'biofuel_cascade',
        name: 'Biofuel Demand',
        technical_name: 'feature_biofuel_cascade',
        current_value: features.feature_biofuel_cascade,
        impact_score: Math.abs(features.feature_biofuel_cascade),
        dollar_impact: features.feature_biofuel_cascade * currentPrice,
        direction: features.feature_biofuel_cascade > 0.5 ? 'BULLISH' : 'NEUTRAL',
        explanation: features.feature_biofuel_cascade > 0.7 ? 'Strong biofuel demand' :
                    features.feature_biofuel_cascade > 0.5 ? 'Healthy biofuel demand' :
                    'Normal biofuel demand',
        confidence: features.feature_biofuel_cascade > 0.6 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'hidden_correlation',
        name: 'Hidden Correlations',
        technical_name: 'feature_hidden_correlation',
        current_value: features.feature_hidden_correlation,
        impact_score: Math.abs(features.feature_hidden_correlation),
        dollar_impact: features.feature_hidden_correlation * currentPrice,
        direction: Math.abs(features.feature_hidden_correlation) > 0.5 ? 'SIGNIFICANT' : 'MINIMAL',
        explanation: Math.abs(features.feature_hidden_correlation) > 0.7 ? 'Strong hidden correlations' :
                    Math.abs(features.feature_hidden_correlation) > 0.5 ? 'Moderate correlations' :
                    'Minimal correlations',
        confidence: Math.abs(features.feature_hidden_correlation) > 0.6 ? 'HIGH' : 'MEDIUM'
      },
      {
        id: 'biofuel_ethanol',
        name: 'Ethanol Impact',
        technical_name: 'feature_biofuel_ethanol',
        current_value: features.feature_biofuel_ethanol,
        impact_score: Math.abs(features.feature_biofuel_ethanol),
        dollar_impact: features.feature_biofuel_ethanol * currentPrice,
        direction: features.feature_biofuel_ethanol > 0.5 ? 'BULLISH' : 'NEUTRAL',
        explanation: features.feature_biofuel_ethanol > 0.7 ? 'Strong ethanol demand' :
                    features.feature_biofuel_ethanol > 0.5 ? 'Healthy ethanol demand' :
                    'Normal ethanol demand',
        confidence: features.feature_biofuel_ethanol > 0.6 ? 'HIGH' : 'MEDIUM'
      }
    ]

    // Sort by absolute impact score
    drivers.sort((a, b) => Math.abs(b.impact_score) - Math.abs(a.impact_score))

    return NextResponse.json({
      data_date: features.date,
      current_price: currentPrice,
      total_drivers: drivers.length,
      net_dollar_impact: drivers.reduce((sum, d) => sum + d.dollar_impact, 0),
      drivers: drivers.slice(0, 8),
      market_regime: features.market_regime,
      big8_composite_score: features.big8_composite_score,
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
