import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    // Get forecast
    const forecastQuery = `
      SELECT 
        future_day,
        mean,
        q10,
        q90
      FROM \`cbi-v14.forecasting_data_warehouse.agg_1m_latest\`
      ORDER BY future_day
    `
    
    // Get 1W signals
    const signalsQuery = `
      SELECT 
        as_of_timestamp,
        signal_name,
        signal_value
      FROM \`cbi-v14.forecasting_data_warehouse.signals_1w\`
      WHERE as_of_timestamp = (
        SELECT MAX(as_of_timestamp) 
        FROM \`cbi-v14.forecasting_data_warehouse.signals_1w\`
      )
    `
    
    // Get legislation events (if table exists)
    let legislationQuery = `
      SELECT 
        event_date,
        event_title,
        event_type,
        description
      FROM \`cbi-v14.forecasting_data_warehouse.legislation_events\`
      WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
      ORDER BY event_date DESC
      LIMIT 10
    `
    
    const forecast = await executeBigQueryQuery(forecastQuery)
    const signals = await executeBigQueryQuery(signalsQuery)
    
    let policy = []
    try {
      policy = await executeBigQueryQuery(legislationQuery)
    } catch (e) {
      // Table may not exist yet
      logger.warning('legislation_events table not found')
    }
    
    return NextResponse.json({
      forecast,
      signals,
      policy
    }, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Strategy API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' },
      { status: 500 }
    )
  }
}

