import { NextRequest, NextResponse } from 'next/server'
import { executeBigQueryQuery, getBigQueryClient } from '@/lib/bigquery'

export const revalidate = 300  // Unified 5min cache

export async function GET() {
  try {
    const query = `
      SELECT 
        config_key,
        config_value,
        description,
        updated_at,
        updated_by
      FROM \`cbi-v14.forecasting_data_warehouse.vegas_calculation_config\`
      ORDER BY config_key
    `
    
    const rows = await executeBigQueryQuery(query)
    
    return NextResponse.json(rows, {
      headers: { 
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60' 
      }
    })
    
  } catch (error: any) {
    console.error('Vegas config API error:', error)
    return NextResponse.json(
      { error: error.message || 'BQ query failed' }, 
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { config_key, config_value, description } = body
    
    if (!config_key || config_value === undefined) {
      return NextResponse.json(
        { error: 'config_key and config_value required' },
        { status: 400 }
      )
    }
    
    const client = getBigQueryClient()
    const query = `
      MERGE \`cbi-v14.forecasting_data_warehouse.vegas_calculation_config\` T
      USING (SELECT 
        @config_key as config_key,
        @config_value as config_value,
        @description as description,
        CURRENT_TIMESTAMP() as updated_at,
        @updated_by as updated_by
      ) S
      ON T.config_key = S.config_key
      WHEN MATCHED THEN
        UPDATE SET
          config_value = S.config_value,
          description = S.description,
          updated_at = S.updated_at,
          updated_by = S.updated_by
      WHEN NOT MATCHED THEN
        INSERT (config_key, config_value, description, updated_at, updated_by)
        VALUES (S.config_key, S.config_value, S.description, S.updated_at, S.updated_by)
    `
    
    const job = await client.query({
      query,
      params: {
        config_key,
        config_value: String(config_value),
        description: description || '',
        updated_by: 'api'  // TODO: Get from auth
      },
      location: 'us-central1'
    })
    
    await job.result()
    
    return NextResponse.json({ success: true, message: 'Config updated' })
    
  } catch (error: any) {
    console.error('Vegas config update error:', error)
    return NextResponse.json(
      { error: error.message || 'Update failed' },
      { status: 500 }
    )
  }
}

