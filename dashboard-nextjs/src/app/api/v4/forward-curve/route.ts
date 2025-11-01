import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient, executeBigQueryQuery } from '@/lib/bigquery'

export async function GET(request: NextRequest) {
  try {
    // Get historical prices (last 365 days for cleaner chart)
    const historicalQuery = `
      SELECT 
        DATE(time) as date,
        close as price,
        'historical' as type
      FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`
      WHERE time >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 365 DAY)
      ORDER BY time ASC
    `
    
    const historical = await executeBigQueryQuery(historicalQuery)
    
    // Get forecasts from agg_1m_latest (updated to use new table)
    const forecastQuery = `
      SELECT 
        future_day,
        DATE_ADD(CURRENT_DATE(), INTERVAL future_day DAY) as date,
        mean as price,
        q10 as confidence_lower,
        q90 as confidence_upper,
        'forecast' as type
      FROM \`cbi-v14.forecasting_data_warehouse.agg_1m_latest\`
      ORDER BY future_day ASC
    `
    
    const forecasts = await executeBigQueryQuery(forecastQuery)
    
    // Get current price for connecting historical to forecast
    const currentQuery = `
      SELECT 
        DATE(time) as date,
        close as price
      FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`
      ORDER BY time DESC
      LIMIT 1
    `
    
    const current = await executeBigQueryQuery(currentQuery)
    
    // Combine data
    const chartData = [
      ...historical.map((row: any) => ({
        date: row.date.value || row.date,
        price: parseFloat(row.price),
        type: 'historical'
      })),
      // Add current as bridge
      ...(current.length > 0 ? [{
        date: current[0].date.value || current[0].date,
        price: parseFloat(current[0].price),
        type: 'current'
      }] : []),
      // Add forecasts (from agg_1m_latest)
      ...forecasts.map((row: any) => ({
        date: row.date.value || row.date,
        price: parseFloat(row.price),
        q10: parseFloat(row.confidence_lower),
        q90: parseFloat(row.confidence_upper),
        future_day: row.future_day,
        type: 'forecast'
      }))
    ]
    
    // Check for current price before processing
    if (!current || current.length === 0 || !current[0]?.price) {
      return NextResponse.json({
        error: 'No current price data available',
        message: 'Cannot calculate forward curve without current price'
      }, { status: 503 })
    }
    const currentPrice = current[0].price
    
    // Calculate buy zones (where forecast shows price drop)
    const buyZones = []
    for (let i = 0; i < forecasts.length; i++) {
      const forecast = forecasts[i]
      
      if (parseFloat(forecast.price) < currentPrice * 0.98) { // 2% drop = buy zone
        buyZones.push({
          future_day: forecast.future_day,
          date: forecast.date.value || forecast.date,
          price: parseFloat(forecast.price),
          savingsPercent: ((currentPrice - parseFloat(forecast.price)) / currentPrice * 100).toFixed(2)
        })
      }
    }
    
    // Get chart events for overlay (optional)
    let chartEvents = []
    try {
      const eventsResponse = await fetch(`${request.nextUrl.origin}/api/chart-events?lookback_days=90`)
      if (eventsResponse.ok) {
        chartEvents = await eventsResponse.json()
      }
    } catch (e) {
      // Chart events may not be available yet
    }

    return NextResponse.json({
      chartData,
      buyZones,
      currentPrice: currentPrice,
      forecastCount: forecasts.length,
      chartEvents,  // Event overlays for annotations
      updated_at: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Forward curve error:', error)
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error',
        details: 'Cannot fetch forward curve data'
      },
      { status: 500 }
    )
  }
}