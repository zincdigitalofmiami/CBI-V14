import { NextResponse } from 'next/server'
import { getBigQueryClient } from '@/lib/bigquery'

export async function GET() {
  try {
    const client = getBigQueryClient();
    const query = `
      SELECT 
        published_at AS timestamp,
        headline,
        source,
        impact_score,
        category,
        entities,
        goldstein_scale,
        sentiment_tone
      FROM \`cbi-v14.intelligence.breaking_news\`
      WHERE published_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      ORDER BY impact_score DESC
      LIMIT 5
    `;
    
    const [rows] = await client.query(query);
    
    if (!rows || rows.length === 0) {
      return NextResponse.json({ 
        news: [],
        message: "No breaking news in last 24 hours"
      });
    }

    return NextResponse.json({ 
      news: rows.map(row => ({
        timestamp: row.timestamp.value,
        headline: row.headline,
        source: row.source,
        impact: row.impact_score,
        category: row.category,
        entities: row.entities,
        goldstein: row.goldstein_scale,
        sentiment: row.sentiment_tone
      })),
      last_updated: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Breaking news error:', error);
    return NextResponse.json({ 
      error: 'Failed to fetch breaking news',
      details: error.message 
    }, { status: 500 });
  }
}