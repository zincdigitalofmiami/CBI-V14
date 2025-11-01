import { NextResponse } from 'next/server'
import { revalidateTag, revalidatePath } from 'next/cache'

// Admin-only cache invalidation endpoint
// Called after predictor job writes to BigQuery to ensure live freshness
export async function POST(request: Request) {
  try {
    // Optional: Add admin authentication here
    // const authHeader = request.headers.get('authorization')
    // if (authHeader !== `Bearer ${process.env.ADMIN_SECRET}`) {
    //   return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    // }

    // Revalidate all forecast-related API routes
    revalidateTag('forecast')
    revalidateTag('volatility')
    revalidateTag('strategy')
    revalidateTag('vegas')
    
    // Also revalidate specific paths
    revalidatePath('/api/forecast')
    revalidatePath('/api/volatility')
    revalidatePath('/api/strategy')
    revalidatePath('/api/vegas')
    revalidatePath('/api/v4/forward-curve')

    return NextResponse.json({ 
      success: true, 
      message: 'Cache invalidated successfully',
      timestamp: new Date().toISOString()
    })
    
  } catch (error: any) {
    console.error('Cache invalidation error:', error)
    return NextResponse.json(
      { error: error.message || 'Cache invalidation failed' }, 
      { status: 500 }
    )
  }
}

