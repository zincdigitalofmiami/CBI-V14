import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET() {
  try {
    // Fetch forecasts for all horizons from existing endpoints
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
    
    const [forecast1w, forecast1m, forecast3m, forecast6m] = await Promise.all([
      fetch(`${baseUrl}/api/v4/forecast/1w`).catch(() => null),
      fetch(`${baseUrl}/api/v4/forecast/1m`).catch(() => null),
      fetch(`${baseUrl}/api/v4/forecast/3m`).catch(() => null),
      fetch(`${baseUrl}/api/v4/forecast/6m`).catch(() => null),
    ]);

    const forecasts = [];
    
    // Process each horizon
    const horizons = [
      { res: forecast1w, horizon: '1w', days: 7 },
      { res: forecast1m, horizon: '1m', days: 30 },
      { res: forecast3m, horizon: '3m', days: 90 },
      { res: forecast6m, horizon: '6m', days: 180 },
    ];

    for (const { res, horizon, days } of horizons) {
      if (res && res.ok) {
        const data = await res.json();
        if (data.prediction && data.target_date) {
          forecasts.push({
            horizon,
            prediction: data.prediction,
            confidence_lower: data.confidence_lower || data.prediction * 0.95,
            confidence_upper: data.confidence_upper || data.prediction * 1.05,
            target_date: data.target_date,
            prediction_date: data.prediction_date,
            days_ahead: days,
          });
        }
      }
    }

    return NextResponse.json({
      success: true,
      forecasts,
      count: forecasts.length,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    console.error('Forecasts API error:', error);
    return NextResponse.json({
      success: false,
      error: error.message,
      forecasts: [],
    }, { status: 500 });
  }
}

