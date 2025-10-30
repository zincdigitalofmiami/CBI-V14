import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

const MODEL_ID_1M = '3156316301270450176'
const MODEL_NAME_1M = 'cbi_v14_1m_FINAL_20251029_1147'
const MAPE_1M = 1.98
const R2_1M = 0.983

const PYTHON_BACKEND = process.env.PYTHON_BACKEND_URL || 'http://localhost:8080'

async function callVertexAIModel(modelId: string, features: Record<string, any>) {
  try {
    const response = await fetch(`${PYTHON_BACKEND}/api/vertex-predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_id: modelId,
        features,
      }),
    })

    if (!response.ok) return null
    const data = await response.json()
    return parseFloat(data.prediction)
  } catch (error) {
    console.error('Error calling backend:', error)
    return null
  }
}

export async function GET(request: NextRequest) {
  try {
    // PHASE 5: Read from BigQuery ONLY (never call Vertex AI directly)
    const forecastQuery = `
      SELECT 
        predicted_price,
        confidence_lower,
        confidence_upper,
        mape,
        model_id,
        model_name,
        prediction_date,
        target_date,
        created_at,
        DATE_DIFF(CURRENT_DATE(), prediction_date, DAY) as days_old
      FROM \`cbi-v14.predictions.daily_forecasts\`
      WHERE horizon = '1M'
      ORDER BY created_at DESC
      LIMIT 1
    `
    
    const forecastResult = await executeBigQueryQuery(forecastQuery)
    if (forecastResult.length === 0) {
      return NextResponse.json({
        horizon: '1m',
        error: 'No predictions available',
        message: 'Monthly prediction job has not run yet',
        next_run: '1st of next month @ 2 AM'
      }, { status: 503 })
    }

    const forecast = forecastResult[0]
    
    // Get current price
    const priceQuery = `
      SELECT close as current_price
      FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`
      ORDER BY time DESC
      LIMIT 1
    `
    const priceResult = await executeBigQueryQuery(priceQuery)
    if (!priceResult || priceResult.length === 0 || !priceResult[0]?.current_price) {
      return NextResponse.json({
        error: 'No current price data available',
        message: 'Cannot calculate price change without current price'
      }, { status: 503 })
    }
    const currentPrice = priceResult[0].current_price
    
    const prediction = forecast.predicted_price
    const change = prediction - currentPrice
    const changePct = (change / currentPrice) * 100

    return NextResponse.json({
      horizon: '1m',
      model_id: forecast.model_id,
      model_name: forecast.model_name,
      prediction: Math.round(prediction * 100) / 100,
      current_price: Math.round(currentPrice * 100) / 100,
      predicted_change: Math.round(change * 100) / 100,
      predicted_change_pct: Math.round(changePct * 100) / 100,
      confidence_lower: Math.round(forecast.confidence_lower * 100) / 100,
      confidence_upper: Math.round(forecast.confidence_upper * 100) / 100,
      signal: changePct > 2 ? 'BUY' : changePct < -2 ? 'WAIT' : 'MONITOR',
      confidence_metrics: {
        mape_percent: forecast.mape,
        r2: R2_1M,
        mae: (forecast.mape / 100) * currentPrice,
      },
      prediction_date: forecast.prediction_date,
      target_date: forecast.target_date,
      last_updated: forecast.created_at,
      days_old: forecast.days_old,
      timestamp: new Date().toISOString(),
    })
  } catch (error: any) {
    console.error('1M error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
