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
      WHERE time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
      ORDER BY time ASC
    `
    
    const historical = await executeBigQueryQuery(historicalQuery)
    
    // Get forecasts from monthly predictions
    const forecastQuery = `
      SELECT 
        horizon,
        target_date as date,
        predicted_price as price,
        confidence_lower,
        confidence_upper,
        mape,
        'forecast' as type
      FROM \`cbi-v14.predictions.monthly_vertex_predictions\`
      ORDER BY target_date ASC
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
      // Add forecasts
      ...forecasts.map((row: any) => ({
        date: row.date.value || row.date,
        price: parseFloat(row.price),
        confidence_lower: parseFloat(row.confidence_lower),
        confidence_upper: parseFloat(row.confidence_upper),
        mape: parseFloat(row.mape),
        horizon: row.horizon,
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
          horizon: forecast.horizon,
          date: forecast.date.value || forecast.date,
          price: parseFloat(forecast.price),
          savingsPercent: ((currentPrice - parseFloat(forecast.price)) / currentPrice * 100).toFixed(2)
        })
      }
    }

    return NextResponse.json({
      chartData,
      buyZones,
      currentPrice: currentPrice,
      forecastCount: forecasts.length,
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


