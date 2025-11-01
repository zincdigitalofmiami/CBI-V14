import { NextRequest, NextResponse } from 'next/server'
import { getBigQueryClient } from '@/lib/bigquery'

// No cache - dynamic explanations

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { future_day, prediction_change_pct, prediction_id } = body
    
    if (!future_day || prediction_change_pct === undefined) {
      return NextResponse.json(
        { error: 'future_day and prediction_change_pct required' },
        { status: 400 }
      )
    }
    
    // Query top 2-3 SHAP contributors
    const query = `
      SELECT 
        feature_name,
        business_label,
        shap_value,
        feature_change_pct,
        interpretation,
        direction
      FROM \`cbi-v14.forecasting_data_warehouse.shap_drivers\`
      WHERE future_day = @future_day
        AND as_of_timestamp = (
          SELECT MAX(as_of_timestamp) 
          FROM \`cbi-v14.forecasting_data_warehouse.shap_drivers\`
          WHERE future_day = @future_day
        )
      ORDER BY ABS(shap_value) DESC
      LIMIT 3
    `
    
    // Use parameterized query with @future_day placeholder
    const client = getBigQueryClient()
    const queryWithParams = query.replace('@future_day', String(future_day))
    const [rows] = await client.query({
      query: queryWithParams,
      location: 'us-central1'
    })
    const shapDrivers = rows
    
    // Deterministic template formatting
    if (shapDrivers.length === 0) {
      // Fallback to deterministic rules
      if (Math.abs(prediction_change_pct) > 15) {
        return NextResponse.json({
          explanation: `⚠️ 1W DIVERGENCE: Short-term reversal risk (${prediction_change_pct > 0 ? '+' : ''}${prediction_change_pct.toFixed(1)}%)`
        })
      }
      
      return NextResponse.json({
        explanation: `📈 Stable: ${Math.abs(prediction_change_pct).toFixed(1)}% change`
      })
    }
    
    // Format with top drivers
    const driverText = shapDrivers
      .map((d: any) => `${d.business_label || d.feature_name} ${d.feature_change_pct > 0 ? '+' : ''}${(d.feature_change_pct || 0).toFixed(1)}%`)
      .join(', ')
    
    const explanation = `Price ${prediction_change_pct > 0 ? '+' : ''}${prediction_change_pct.toFixed(1)}% (D+${future_day}). Driver: ${driverText}.`
    
    return NextResponse.json({
      explanation,
      drivers: shapDrivers.map((d: any) => ({
        label: d.business_label || d.feature_name,
        change: d.feature_change_pct || 0,
        interpretation: d.interpretation,
        direction: d.direction
      }))
    })
    
  } catch (error: any) {
    console.error('Explain API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' },
      { status: 500 }
    )
  }
}

