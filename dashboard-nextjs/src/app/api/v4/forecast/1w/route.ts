import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

const MODEL_ID_1W = '3610713670704693248'
const MODEL_NAME_1W = 'cbi_v14_automl_pilot_1w_job'
const MAPE_1W = 2.02
const R2_1W = 0.9836

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

    if (!response.ok) {
      console.error(`Backend error: ${response.status}`)
      return null
    }

    const data = await response.json()
    return parseFloat(data.prediction)
  } catch (error) {
    console.error('Error calling backend:', error)
    return null
  }
}

export async function GET(request: NextRequest) {
  try {
    // Try daily_forecasts first (current production), fallback to monthly_vertex_predictions
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
      WHERE horizon = '1W'
        AND prediction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
      ORDER BY created_at DESC
      LIMIT 1
    `
    
    let forecastResult = await executeBigQueryQuery(forecastQuery)
    
    // Fallback to monthly table if daily_forecasts is empty
    if (forecastResult.length === 0) {
      const monthlyQuery = `
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
        FROM \`cbi-v14.predictions.monthly_vertex_predictions\`
        WHERE horizon = '1W'
        ORDER BY created_at DESC
        LIMIT 1
      `
      forecastResult = await executeBigQueryQuery(monthlyQuery)
    }
    
    if (forecastResult.length === 0) {
      return NextResponse.json({
        horizon: '1w',
        error: 'No predictions available',
        message: 'Models are still training or prediction job has not run yet',
        status: 'training'
      }, { status: 503 })
    }

    const forecast = forecastResult[0]
    
    // Get current price from latest soybean oil data
    const priceQuery = `
      SELECT close as current_price
      FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`
      ORDER BY time DESC
      LIMIT 1
    `
    const priceResult = await executeBigQueryQuery(priceQuery)
    if (!priceResult || priceResult.length === 0 || !priceResult[0]?.current_price) {
      return NextResponse.json({
        horizon: '1w',
        error: 'No current price data available',
        message: 'Cannot calculate price change without current price',
        status: 'no_price_data'
      }, { status: 503 })
    }
    const currentPrice = priceResult[0].current_price
    
    const prediction = forecast.predicted_price
    const change = prediction - currentPrice
    const changePct = (change / currentPrice) * 100

    return NextResponse.json({
      horizon: '1w',
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
        r2: R2_1W,
        mae: (forecast.mape / 100) * currentPrice,
      },
      prediction_date: forecast.prediction_date,
      target_date: forecast.target_date,
      last_updated: forecast.created_at,
      days_old: forecast.days_old,
      timestamp: new Date().toISOString(),
    })
  } catch (error: any) {
    console.error('1W forecast error:', error.message || error)
    return NextResponse.json(
      { 
        horizon: '1w',
        error: 'Forecast service unavailable',
        message: error.message || 'BigQuery connection or query failed',
        status: 'error'
      },
      { status: 503 }
    )
  }
}
