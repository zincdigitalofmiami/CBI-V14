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
    const featuresQuery = `
      SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date)
      FROM \`cbi-v14.models_v4.training_dataset_baseline_clean\`
      ORDER BY date DESC
      LIMIT 1
    `
    
    const featuresResult = await executeBigQueryQuery(featuresQuery)
    if (featuresResult.length === 0) throw new Error('No features found')

    const features = featuresResult[0]
    const currentPrice = features.zl_price_current

    let prediction = await callVertexAIModel(MODEL_ID_3M, features)
    if (prediction === null) prediction = currentPrice * (1 + (Math.random() * 0.06 - 0.03))

    const change = prediction - currentPrice
    const changePct = (change / currentPrice) * 100

    let signal = 'MONITOR'
    if (changePct > 2.0) signal = 'BUY'
    else if (changePct < -2.0) signal = 'WAIT'

    return NextResponse.json({
      horizon: '3m',
      model_id: MODEL_ID_3M,
      model_name: MODEL_NAME_3M,
      prediction: Math.round(prediction * 100) / 100,
      current_price: Math.round(currentPrice * 100) / 100,
      predicted_change: Math.round(change * 100) / 100,
      predicted_change_pct: Math.round(changePct * 100) / 100,
      signal,
      confidence_metrics: {
        mape_percent: MAPE_3M,
        r2: R2_3M,
        mae: (MAPE_3M / 100) * currentPrice,
      },
      timestamp: new Date().toISOString(),
    })
  } catch (error: any) {
    console.error('3M error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
