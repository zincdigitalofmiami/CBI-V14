import { NextRequest, NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { 
      biofuel_mandate_pct, 
      tariff_change_pct, 
      trade_deal_impact 
    } = body
    
    // This is a simplified simulator - in production would use actual model
    // For now, return placeholder response with calculated impacts
    
    const simulationResult = {
      base_forecast: {
        D7: 0.48,
        D14: 0.49,
        D30: 0.50
      },
      adjusted_forecast: {
        D7: 0.48 + (biofuel_mandate_pct || 0) * 0.001,
        D14: 0.49 + (biofuel_mandate_pct || 0) * 0.001,
        D30: 0.50 + (biofuel_mandate_pct || 0) * 0.001 - (tariff_change_pct || 0) * 0.0005
      },
      impacts: {
        biofuel: biofuel_mandate_pct || 0,
        tariff: tariff_change_pct || 0,
        trade: trade_deal_impact || 0
      },
      timestamp: new Date().toISOString()
    }
    
    return NextResponse.json(simulationResult, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Policy simulator API error:', error)
    return NextResponse.json(
      { error: error.message || 'Simulation failed' }, 
      { status: 500 }
    )
  }
}

