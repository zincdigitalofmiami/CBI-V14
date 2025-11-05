import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // Query for events with proper multiplier calculation
    // Expected columns: event_traffic, base_daily_traffic, cuisine_intensity_factor
    // Formula: Multiplier = (Expected Event Traffic / Base Daily Traffic) × Cuisine Oil Intensity Factor
    const query = `
      WITH base_usage AS (
        -- Calculate base daily oil usage from fryer data
        -- Aggregate fryers: capacity × TPM ÷ 7 days, convert to gallons
        SELECT 
          SUM(fryer_capacity_lb * turns_per_month) / 7 / 7.6 as base_daily_gallons,
          50000 as base_daily_traffic  -- Normal Vegas daily traffic baseline
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_fryers\`
        WHERE is_active = true
      ),
      events_with_multipliers AS (
        SELECT 
          e.event_id as id,
          e.event_name as name,
          e.event_type as type,
          e.event_date as date,
          e.location,
          e.expected_attendance as event_traffic,
          bu.base_daily_traffic,
          e.cuisine_intensity_factor,
          -- Calculate multiplier: (event_traffic / base_traffic) × cuisine_factor
          LEAST(
            (e.expected_attendance / bu.base_daily_traffic) * e.cuisine_intensity_factor,
            5.0  -- Cap at 5x for conservatism (system caps, not raw math)
          ) as volume_multiplier,
          -- Calculate surge: base_gallons × multiplier
          bu.base_daily_gallons * LEAST(
            (e.expected_attendance / bu.base_daily_traffic) * e.cuisine_intensity_factor,
            5.0
          ) as surge_gallons_per_day,
          e.event_duration_days,
          -- Revenue calculation: surge × days × price_per_gallon
          bu.base_daily_gallons * LEAST(
            (e.expected_attendance / bu.base_daily_traffic) * e.cuisine_intensity_factor,
            5.0
          ) * e.event_duration_days * 8.20 as revenue_impact,
          COUNT(DISTINCT c.customer_id) as affected_customers,
          DATE_DIFF(e.event_date, CURRENT_DATE(), DAY) as days_until,
          -- Breakdown fields for display
          (e.expected_attendance / bu.base_daily_traffic) as traffic_ratio,
          e.cuisine_intensity_factor,
          bu.base_daily_gallons as base_daily_gallons
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_events\` e
        CROSS JOIN base_usage bu
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_customer_events\` ce
          ON e.event_id = ce.event_id
        LEFT JOIN \`cbi-v14.forecasting_data_warehouse.vegas_customers\` c
          ON ce.customer_id = c.customer_id
        WHERE e.event_date >= CURRENT_DATE()
          AND e.event_type IN ('F1 Race', 'Convention', 'Festival', 'Concert', 'Other')
        GROUP BY 
          e.event_id, e.event_name, e.event_type, e.event_date, e.location,
          e.expected_attendance, bu.base_daily_traffic, e.cuisine_intensity_factor,
          e.event_duration_days, bu.base_daily_gallons
        ORDER BY e.event_date ASC
        LIMIT 30
      )
      SELECT * FROM events_with_multipliers
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      // Fallback: Try simpler query if tables don't exist yet
      const simpleQuery = `
        SELECT 
          event_id as id,
          event_name as name,
          event_type as type,
          event_date as date,
          location,
          volume_multiplier,
          affected_customer_count as affected_customers,
          revenue_impact,
          DATE_DIFF(event_date, CURRENT_DATE(), DAY) as days_until
        FROM \`cbi-v14.forecasting_data_warehouse.vegas_events\`
        WHERE event_date >= CURRENT_DATE()
        ORDER BY event_date ASC
        LIMIT 30
      `
      const simpleResults = await executeBigQueryQuery(simpleQuery)
      if (simpleResults.length === 0) {
        return NextResponse.json([])
      }
      
      const events = simpleResults.map((row: any) => ({
        id: row.id,
        name: row.name,
        type: row.type || 'Other',
        date: row.date?.value || row.date,
        location: row.location || 'Las Vegas, NV',
        volume_multiplier: row.volume_multiplier || 1.0,
        affected_customers: row.affected_customers || 0,
        revenue_impact: row.revenue_impact || 0,
        days_until: row.days_until || 0,
        calculation_breakdown: null
      }))
      
      return NextResponse.json(events)
    }

    const events = results.map((row: any) => ({
      id: row.id,
      name: row.name,
      type: row.type || 'Other',
      date: row.date?.value || row.date,
      location: row.location || 'Las Vegas, NV',
      volume_multiplier: row.volume_multiplier || 1.0,
      affected_customers: row.affected_customers || 0,
      revenue_impact: row.revenue_impact || 0,
      days_until: row.days_until || 0,
      calculation_breakdown: {
        event_traffic: row.event_traffic || 0,
        base_daily_traffic: row.base_daily_traffic || 50000,
        traffic_ratio: row.traffic_ratio || 1.0,
        cuisine_intensity_factor: row.cuisine_intensity_factor || 1.0,
        base_daily_gallons: row.base_daily_gallons || 545,
        surge_gallons_per_day: row.surge_gallons_per_day || 0,
        event_duration_days: row.event_duration_days || 1,
        total_surge_gallons: (row.surge_gallons_per_day || 0) * (row.event_duration_days || 1),
        price_per_gallon: 8.20
      }
    }))

    return NextResponse.json(events)
  } catch (error: any) {
    if (error.message?.includes('not found') || error.message?.includes('does not exist')) {
      return NextResponse.json([])
    }
    console.error('Vegas events error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
