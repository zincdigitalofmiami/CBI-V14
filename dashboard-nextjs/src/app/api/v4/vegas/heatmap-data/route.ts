import { NextResponse } from 'next/server'
import { executeBigQueryQuery } from '@/lib/bigquery'

export async function GET() {
  try {
    // NO FAKE DATA - Return empty until real event data available
    const query = `
      SELECT 
        NULL as lat,
        NULL as lng,
        NULL as weight,
        'none' as type,
        'No Data' as name
      LIMIT 0
    `
    
    const results = await executeBigQueryQuery(query)
    
    return NextResponse.json(results)
  } catch (error: any) {
    console.error('Heat map data error:', error)
    return NextResponse.json([])
  }
}

