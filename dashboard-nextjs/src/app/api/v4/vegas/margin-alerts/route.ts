import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // Query for margin protection alerts
    const query = `
      SELECT 
        alert_id as id,
        customer_name,
        alert_type,
        severity,
        current_margin_pct as current_margin,
        risk_amount_usd as risk_amount,
        recommended_action,
        urgency
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_margin_alerts\`
      ORDER BY 
        CASE severity
          WHEN 'CRITICAL' THEN 1
          WHEN 'HIGH' THEN 2
          WHEN 'MEDIUM' THEN 3
          ELSE 4
        END,
        risk_amount_usd DESC
      LIMIT 20
    `
    
    const results = await executeBigQueryQuery(query)
    
    if (results.length === 0) {
      return NextResponse.json([])
    }

    const alerts = results.map((row: any) => ({
      id: row.id,
      customer_name: row.customer_name,
      alert_type: row.alert_type,
      severity: row.severity,
      current_margin: row.current_margin,
      risk_amount: row.risk_amount,
      recommended_action: row.recommended_action,
      urgency: row.urgency
    }))

    return NextResponse.json(alerts)
  } catch (error: any) {
    if (error.message?.includes('not found') || error.message?.includes('does not exist')) {
      return NextResponse.json([])
    }
    console.error('Vegas margin alerts error:', error)
    return NextResponse.json({ error: error.message || 'Internal server error' }, { status: 500 })
  }
}
