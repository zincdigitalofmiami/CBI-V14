import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

const MODEL_ID_3M = '4390624292220243648'
const MODEL_NAME_3M = 'cbi_v14_3m_final_20251029_0808'
const MAPE_3M = 2.68
const R2_3M = 0.9727

const PYTHON_BACKEND = process.env.PYTHON_BACKEND_URL || 'http://localhost:8080'

async function callVertexAIModel(modelId: string, features: Record<string, any>) {
  try {
    const response = await fetch(`${PYTHON_BACKEND}/api/vertex-predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_id: modelId, features }),
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
        current_price,
        forecast_3m as prediction,
        confidence_3m as confidence,
        signal_3m as signal,
        model_3m_id as model_id,
        run_timestamp,
        DATE_DIFF(CURRENT_DATE(), prediction_date, DAY) as days_old
      FROM \`cbi-v14.predictions.daily_forecasts\`
      ORDER BY run_timestamp DESC
      LIMIT 1
    `
    
    const forecastResult = await executeBigQueryQuery(forecastQuery)
    if (forecastResult.length === 0) {
      return NextResponse.json({
        horizon: '3m',
        error: 'No predictions available',
        message: 'Monthly prediction job has not run yet',
        next_run: '1st of next month @ 2 AM'
      }, { status: 503 })
    }

    const forecast = forecastResult[0]
    const prediction = forecast.prediction
    const currentPrice = forecast.current_price
    const change = prediction - currentPrice
    const changePct = (change / currentPrice) * 100

    return NextResponse.json({
      horizon: '3m',
      model_id: forecast.model_id || MODEL_ID_3M,
      model_name: MODEL_NAME_3M,
      prediction: Math.round(prediction * 100) / 100,
      current_price: Math.round(currentPrice * 100) / 100,
      predicted_change: Math.round(change * 100) / 100,
      predicted_change_pct: Math.round(changePct * 100) / 100,
      signal: forecast.signal || 'MONITOR',
      confidence: forecast.confidence || 0.85,
      confidence_metrics: {
        mape_percent: MAPE_3M,
        r2: R2_3M,
        mae: (MAPE_3M / 100) * currentPrice,
      },
      last_updated: forecast.run_timestamp,
      days_old: forecast.days_old,
      timestamp: new Date().toISOString(),
    })
  } catch (error: any) {
    console.error('3M error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
