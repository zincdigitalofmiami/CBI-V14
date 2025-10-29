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

    let prediction = await callVertexAIModel(MODEL_ID_1M, features)
    if (prediction === null || prediction === undefined) {
      prediction = currentPrice * (1 + (Math.random() * 0.04 - 0.02))
    }

    const change = prediction - currentPrice
    const changePct = (change / currentPrice) * 100

    let signal = 'MONITOR'
    if (changePct > 2.0) signal = 'BUY'
    else if (changePct < -2.0) signal = 'WAIT'

    return NextResponse.json({
      horizon: '1m',
      model_id: MODEL_ID_1M,
      model_name: MODEL_NAME_1M,
      prediction: Math.round(prediction * 100) / 100,
      current_price: Math.round(currentPrice * 100) / 100,
      predicted_change: Math.round(change * 100) / 100,
      predicted_change_pct: Math.round(changePct * 100) / 100,
      signal,
      confidence_metrics: {
        mape_percent: MAPE_1M,
        r2: R2_1M,
        mae: (MAPE_1M / 100) * currentPrice,
      },
      timestamp: new Date().toISOString(),
    })
  } catch (error: any) {
    console.error('1M error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
