import { BigQuery, BigQueryOptions } from '@google-cloud/bigquery'

let bigqueryClient: BigQuery | null = null

/**
 * Get or create BigQuery client with proper credential handling
 * Works in both local development and Vercel production
 */
export function getBigQueryClient(): BigQuery {
  if (bigqueryClient) {
    return bigqueryClient
  }

  const options: BigQueryOptions = {
    projectId: process.env.GCP_PROJECT_ID || 'cbi-v14',
    location: 'us-central1', // Datasets are in us-central1 region
  }

  // Check if we have base64 encoded credentials (Vercel production)
  if (process.env.GOOGLE_APPLICATION_CREDENTIALS_BASE64) {
    try {
      const credentials = JSON.parse(
        Buffer.from(
          process.env.GOOGLE_APPLICATION_CREDENTIALS_BASE64,
          'base64'
        ).toString('utf-8')
      )
      options.credentials = credentials
    } catch (error) {
      console.error('Failed to parse base64 credentials:', error)
      // Don't throw - let it try Application Default Credentials
    }
  }
  // For local development, it will use GOOGLE_APPLICATION_CREDENTIALS env var
  // or Application Default Credentials

  try {
    bigqueryClient = new BigQuery(options)
    return bigqueryClient
  } catch (error) {
    console.error('BigQuery client creation failed:', error)
    // Return client anyway - connection will fail on first query but won't crash
    bigqueryClient = new BigQuery({ projectId: 'cbi-v14' })
    return bigqueryClient
  }
}

/**
 * Execute a BigQuery query with error handling
 */
export async function executeBigQueryQuery(query: string, location?: string): Promise<any[]> {
  try {
    const client = getBigQueryClient()
    const queryOptions: any = { query }
    // Explicitly set location to us-central1 to match our datasets
    if (location) {
      queryOptions.location = location
    } else {
      queryOptions.location = 'us-central1'
    }
    const [rows] = await client.query(queryOptions)
    return rows || []
  } catch (error: any) {
    console.error('BigQuery query error:', error.message || error)
    // Return empty array instead of throwing - let routes handle gracefully
    return []
  }
}

/**
 * Check if BigQuery client is properly configured
 */
export async function testBigQueryConnection(): Promise<boolean> {
  try {
    const client = getBigQueryClient()
    const [rows] = await client.query({ 
      query: 'SELECT 1 as test',
      location: 'us-central1'
    })
    return rows && rows.length > 0
  } catch (error: any) {
    console.error('BigQuery connection test failed:', error.message || error)
    return false
  }
}
