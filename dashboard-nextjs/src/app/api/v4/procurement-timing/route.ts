import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get historical prices with VIX overlay for procurement timing analysis
    const timingQuery = `
      WITH price_vix_data AS (
        SELECT 
          DATE(s.time) as date,
          s.close as zl_price,
          v.close as vix_level,
          -- Calculate 20-day moving average
          AVG(s.close) OVER (ORDER BY DATE(s.time) ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as ma_20,
          -- Calculate volatility
          STDDEV(s.close) OVER (ORDER BY DATE(s.time) ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as volatility_20,
          -- VIX regime classification
          CASE 
            WHEN v.close > 30 THEN 'CRISIS'
            WHEN v.close > 25 THEN 'HIGH_FEAR'
            WHEN v.close > 20 THEN 'ELEVATED'
            WHEN v.close > 15 THEN 'NORMAL'
            ELSE 'COMPLACENT'
          END as vix_regime,
          -- Price momentum
          (s.close - LAG(s.close, 5) OVER (ORDER BY DATE(s.time))) / NULLIF(LAG(s.close, 5) OVER (ORDER BY DATE(s.time)), 0) * 100 as momentum_5d
        FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\` s
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vix_daily\` v
          ON DATE(s.time) = v.date
        WHERE s.symbol = 'ZL'
          AND DATE(s.time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY)
        ORDER BY DATE(s.time)
      ),
      
      forecast_data AS (
        SELECT 
          prediction_date,
          horizon,
          predicted_price,
          confidence_lower,
          confidence_upper,
          CASE horizon
            WHEN '1W' THEN DATE_ADD(prediction_date, INTERVAL 7 DAY)
            WHEN '1M' THEN DATE_ADD(prediction_date, INTERVAL 30 DAY)
            WHEN '3M' THEN DATE_ADD(prediction_date, INTERVAL 90 DAY)
            WHEN '6M' THEN DATE_ADD(prediction_date, INTERVAL 180 DAY)
          END as target_date
        FROM \`cbi-v14.predictions.daily_forecasts\`
        WHERE prediction_date = CURRENT_DATE()
      ),
      
      opportunity_windows AS (
        SELECT 
          date,
          zl_price,
          vix_level,
          vix_regime,
          momentum_5d,
          ma_20,
          volatility_20,
          -- Opportunity scoring
          CASE 
            WHEN vix_level > 25 AND zl_price < ma_20 * 0.98 THEN 'STRONG_BUY'
            WHEN vix_level > 20 AND zl_price < ma_20 * 0.99 THEN 'BUY'
            WHEN vix_level < 15 AND zl_price > ma_20 * 1.02 THEN 'WAIT'
            WHEN momentum_5d < -3 AND vix_level > 18 THEN 'BUY_DIP'
            ELSE 'MONITOR'
          END as opportunity_signal,
          -- Risk score (0-100)
          LEAST(100, GREATEST(0, 
            (vix_level * 2) + 
            (ABS(momentum_5d) * 1.5) + 
            (volatility_20 * 10)
          )) as risk_score,
          -- Confidence based on VIX and volatility
          CASE 
            WHEN vix_level > 25 THEN 'HIGH'
            WHEN vix_level > 18 THEN 'MEDIUM'
            ELSE 'LOW'
          END as signal_confidence
        FROM price_vix_data
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
      )
      
      SELECT 
        o.*,
        f.predicted_price,
        f.confidence_lower,
        f.confidence_upper,
        f.horizon,
        f.target_date,
        -- Calculate potential savings
        CASE 
          WHEN o.opportunity_signal IN ('STRONG_BUY', 'BUY', 'BUY_DIP') 
          THEN GREATEST(0, f.predicted_price - o.zl_price)
          ELSE 0
        END as potential_savings
      FROM opportunity_windows o
      CROSS JOIN forecast_data f
      WHERE f.horizon = '1M'  -- Use 1M forecast for procurement timing
      ORDER BY o.date DESC
    `
    
    const result = await executeBigQueryQuery(timingQuery)
    if (result.length === 0) {
      return NextResponse.json({
        error: 'No timing data available',
        message: 'Price and VIX data not synchronized'
      }, { status: 503 })
    }

    // Process data for visualization
    const currentData = result[0]
    const historicalData = result.slice(0, 60) // Last 60 days

    // Calculate opportunity windows
    const opportunities = historicalData.map(row => ({
      date: row.date,
      price: row.zl_price,
      vix: row.vix_level,
      vix_regime: row.vix_regime,
      signal: row.opportunity_signal,
      risk_score: row.risk_score,
      confidence: row.signal_confidence,
      potential_savings: row.potential_savings,
      momentum: row.momentum_5d,
      ma_20: row.ma_20
    }))

    // Current market assessment
    const currentOpportunity = {
      signal: currentData.opportunity_signal,
      confidence: currentData.signal_confidence,
      risk_score: currentData.risk_score,
      vix_level: currentData.vix_level,
      vix_regime: currentData.vix_regime,
      current_price: currentData.zl_price,
      forecast_price: currentData.predicted_price,
      potential_savings: currentData.potential_savings,
      days_to_target: 30, // 1M horizon
      recommendation: generateRecommendation(currentData)
    }

    return NextResponse.json({
      current_opportunity: currentOpportunity,
      historical_opportunities: opportunities,
      forecast_data: {
        predicted_price: currentData.predicted_price,
        confidence_lower: currentData.confidence_lower,
        confidence_upper: currentData.confidence_upper,
        target_date: currentData.target_date
      },
      vix_analysis: {
        current_level: currentData.vix_level,
        regime: currentData.vix_regime,
        fear_index: Math.min(100, currentData.vix_level * 3.33), // Scale to 0-100
        market_stress: currentData.vix_level > 25 ? 'EXTREME' : 
                      currentData.vix_level > 20 ? 'HIGH' : 
                      currentData.vix_level > 15 ? 'MODERATE' : 'LOW'
      },
      last_updated: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Procurement timing error:', error)
    return NextResponse.json({ 
      error: error.message || 'Internal server error'
    }, { status: 500 })
  }
}

function generateRecommendation(data: any): string {
  const vix = data.vix_level
  const signal = data.opportunity_signal
  const savings = data.potential_savings
  
  if (signal === 'STRONG_BUY' && vix > 25) {
    return `STRONG BUY OPPORTUNITY: Market fear (VIX ${vix.toFixed(1)}) creating $${savings.toFixed(2)} savings window. High volatility = procurement advantage.`
  } else if (signal === 'BUY' && savings > 1) {
    return `BUY SIGNAL: Current dip offers $${savings.toFixed(2)} potential savings vs forecast. Execute purchases in next 7-14 days.`
  } else if (signal === 'BUY_DIP' && data.momentum_5d < -3) {
    return `BUY THE DIP: Price momentum down ${Math.abs(data.momentum_5d).toFixed(1)}% with elevated VIX. Contrarian opportunity.`
  } else if (signal === 'WAIT' && vix < 15) {
    return `WAIT SIGNAL: Low volatility (VIX ${vix.toFixed(1)}) and elevated prices. Better opportunities likely ahead.`
  } else {
    return `MONITOR: Mixed signals. VIX ${vix.toFixed(1)}, momentum ${data.momentum_5d.toFixed(1)}%. Maintain normal purchasing schedule.`
  }
}



