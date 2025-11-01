import { NextRequest, NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 3600  // 1 hour (events don't change often)

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const lookbackDays = parseInt(searchParams.get('lookback_days') || '365')
    const startDate = searchParams.get('start_date')
    const endDate = searchParams.get('end_date')
    
    // Build date filter
    let dateFilter = `event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL ${lookbackDays} DAY)`
    if (startDate && endDate) {
      dateFilter = `event_date BETWEEN '${startDate}' AND '${endDate}'`
    }
    
    // Get events
    const eventsQuery = `
      SELECT 
        event_date,
        event_title,
        event_type,
        description,
        price_change_pct
      FROM \`cbi-v14.forecasting_data_warehouse.legislation_events\`
      WHERE ${dateFilter}
      ORDER BY event_date DESC
    `
    
    // Get historical SHAP values for each event
    const shapQuery = `
      SELECT 
        as_of_timestamp,
        future_day,
        feature_name,
        business_label,
        shap_value,
        feature_change_pct
      FROM \`cbi-v14.forecasting_data_warehouse.shap_drivers\`
      WHERE DATE(as_of_timestamp) IN (
        SELECT DISTINCT event_date
        FROM \`cbi-v14.forecasting_data_warehouse.legislation_events\`
        WHERE ${dateFilter}
      )
      ORDER BY ABS(shap_value) DESC
    `
    
    let events = []
    let shapDrivers = []
    
    try {
      events = await executeBigQueryQuery(eventsQuery)
      shapDrivers = await executeBigQueryQuery(shapQuery)
    } catch (e) {
      // Tables may not exist yet
      console.warn('legislation_events or shap_drivers table not found')
    }
    
    // Match events with SHAP drivers and generate explanations
    const eventsWithExplanations = events.map((event: any) => {
      const eventDate = event.event_date
      const eventShap = shapDrivers.filter((s: any) => 
        s.as_of_timestamp && 
        s.as_of_timestamp.toISOString().startsWith(eventDate)
      ).slice(0, 3)  // Top 3 drivers
      
      const topDrivers = eventShap.map((s: any) => ({
        label: s.business_label || s.feature_name,
        change: s.feature_change_pct || 0
      }))
      
      const driverText = topDrivers
        .map(d => `${d.label} ${d.change > 0 ? '+' : ''}${d.change.toFixed(1)}%`)
        .join(', ')
      
      const priceDir = (event.price_change_pct || 0) > 0 ? 'rise' : 'drop'
      const explanation = `The ${priceDir} on ${eventDate} was due to ${event.event_title}: ${event.description || ''}. Drivers: ${driverText || 'N/A'}.`
      
      return {
        date: eventDate,
        event_title: event.event_title,
        event_type: event.event_type,
        price_change_pct: event.price_change_pct || 0,
        explanation,
        drivers: topDrivers
      }
    })
    
    return NextResponse.json(eventsWithExplanations, {
      headers: { 
        'Cache-Control': 's-maxage=3600, stale-while-revalidate=300' 
      }
    })
    
  } catch (error: any) {
    console.error('Chart events API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' },
      { status: 500 }
    )
  }
}

