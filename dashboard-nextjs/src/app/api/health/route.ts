import { NextResponse } from 'next/server'
import { testBigQueryConnection } from '@/lib/bigquery'

export async function GET() {
  try {
    const isBigQueryConnected = await testBigQueryConnection()

    if (!isBigQueryConnected) {
      return NextResponse.json(
        {
          status: 'degraded',
          message: 'BigQuery connection failed',
          timestamp: new Date().toISOString(),
        },
        { status: 503 }
      )
    }

    return NextResponse.json({
      status: 'healthy',
      message: 'CBI-V14 Dashboard API',
      version: 'v4',
      bigquery: 'connected',
      features: {
        vertex_ai_models: true,
        forecasts: ['1w', '1m', '3m', '6m'],
        model_types: ['boosted_v3', 'automl_v4'],
      },
      timestamp: new Date().toISOString(),
    })
  } catch (error: any) {
    return NextResponse.json(
      {
        status: 'error',
        message: error.message || 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    )
  }
}





