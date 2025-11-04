import { NextResponse } from 'next/server'
import { testBigQueryConnection } from '@/lib/bigquery'

export async function GET() {
  try {
    const isBigQueryConnected = await testBigQueryConnection()

    return NextResponse.json({
      status: isBigQueryConnected ? 'healthy' : 'degraded',
      message: 'CBI-V14 Dashboard API',
      version: 'v4',
      bigquery: isBigQueryConnected ? 'connected' : 'disconnected',
      features: {
        vertex_ai_models: true,
        forecasts: ['1w', '1m', '3m', '6m'],
        model_types: ['boosted_v3', 'automl_v4'],
      },
      timestamp: new Date().toISOString(),
      note: isBigQueryConnected ? 'All systems operational' : 'BigQuery connection failed - check credentials'
    })
  } catch (error: any) {
    return NextResponse.json(
      {
        status: 'error',
        message: error.message || 'Unknown error',
        bigquery: 'unknown',
        timestamp: new Date().toISOString(),
      },
      { status: 503 }
    )
  }
}
