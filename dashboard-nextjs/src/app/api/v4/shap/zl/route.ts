import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET() {
  try {
    // Mock SHAP data until real SHAP table exists in BigQuery
    const query = `
      SELECT 
        date,
        'RINs_momentum' as feature_name,
        RAND() * 20 - 10 as shap_value_cents
      FROM UNNEST(GENERATE_DATE_ARRAY(DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY), CURRENT_DATE())) as date
      
      UNION ALL
      
      SELECT 
        date,
        'Tariff_risk' as feature_name,
        RAND() * 15 - 8 as shap_value_cents
      FROM UNNEST(GENERATE_DATE_ARRAY(DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY), CURRENT_DATE())) as date
      
      UNION ALL
      
      SELECT 
        date,
        'Drought_zscore' as feature_name,
        RAND() * 12 - 5 as shap_value_cents
      FROM UNNEST(GENERATE_DATE_ARRAY(DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY), CURRENT_DATE())) as date
      
      UNION ALL
      
      SELECT 
        date,
        'Crush_margin' as feature_name,
        RAND() * 10 - 3 as shap_value_cents
      FROM UNNEST(GENERATE_DATE_ARRAY(DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY), CURRENT_DATE())) as date
    `;

    // Generate mock SHAP data
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 90);
    
    const data = [];
    const features = ['RINs_momentum', 'Tariff_risk', 'Drought_zscore', 'Crush_margin'];
    const ranges = [20, 15, 12, 10];
    const offsets = [-10, -8, -5, -3];
    
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split('T')[0];
      features.forEach((feature, idx) => {
        data.push({
          date: dateStr,
          feature_name: feature,
          shap_value_cents: Math.random() * ranges[idx] + offsets[idx]
        });
      });
    }

    return NextResponse.json({ 
      success: true,
      data,
      features,
      count: data.length,
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('SHAP API error:', error);
    return NextResponse.json({ 
      success: false, 
      error: error.message
    }, { status: 500 });
  }
}

