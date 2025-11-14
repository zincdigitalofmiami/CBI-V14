# Phase 3: Geospatial Event Intelligence Implementation

**Status:** 🔴 NOT STARTED  
**Priority:** HIGH  
**Estimated Duration:** 3-4 weeks  
**Dependencies:** Glide API data + Google Maps API + OpenAI API

---

## Overview

Implement geographic heat mapping, event scraping, proximity-based calculations, and AI-powered messaging to match the target interface shown in reference screenshots.

---

## Component 1: Geographic Foundation

### 1.1 Add Geocoding to Existing Data

**Objective:** Convert text locations to lat/lng coordinates

**Tables to Update:**
```sql
-- Add coordinates to casinos
ALTER TABLE `cbi-v14.forecasting_data_warehouse.vegas_casinos`
ADD COLUMN lat FLOAT64,
ADD COLUMN lng FLOAT64,
ADD COLUMN geocoord GEOGRAPHY;

-- Add coordinates to restaurants  
ALTER TABLE `cbi-v14.forecasting_data_warehouse.vegas_restaurants`
ADD COLUMN lat FLOAT64,
ADD COLUMN lng FLOAT64,
ADD COLUMN geocoord GEOGRAPHY;

-- Add coordinates to events (when scraped)
ALTER TABLE `cbi-v14.forecasting_data_warehouse.vegas_events`
ADD COLUMN lat FLOAT64,
ADD COLUMN lng FLOAT64,
ADD COLUMN geocoord GEOGRAPHY;
```

**Geocoding Script:**
```python
# scripts/geocode_vegas_locations.py

from google.cloud import bigquery
import googlemaps
import os

PROJECT_ID = "cbi-v14"
GMAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

gmaps = googlemaps.Client(key=GMAPS_API_KEY)
client = bigquery.Client(project=PROJECT_ID)

def geocode_casinos():
    """Geocode all casinos"""
    query = """
    SELECT glide_rowID, Name, Location
    FROM `cbi-v14.forecasting_data_warehouse.vegas_casinos`
    WHERE lat IS NULL
    """
    
    casinos = client.query(query).to_dataframe()
    
    for _, row in casinos.iterrows():
        # Construct address
        address = f"{row['Name']}, {row['Location']}, Las Vegas, NV"
        
        # Geocode
        result = gmaps.geocode(address)
        
        if result:
            lat = result[0]['geometry']['location']['lat']
            lng = result[0]['geometry']['location']['lng']
            
            # Update BigQuery
            update_query = f"""
            UPDATE `cbi-v14.forecasting_data_warehouse.vegas_casinos`
            SET 
              lat = {lat},
              lng = {lng},
              geocoord = ST_GEOGPOINT({lng}, {lat})
            WHERE glide_rowID = '{row['glide_rowID']}'
            """
            
            client.query(update_query).result()
            print(f"✅ Geocoded: {row['Name']} -> ({lat}, {lng})")

if __name__ == "__main__":
    geocode_casinos()
```

---

## Component 2: Event Scraper

### 2.1 Event Data Sources

**Primary Sources:**
1. **Las Vegas Convention Calendar** - https://www.lvcva.com/calendar/
2. **Eventbrite API** - Las Vegas events
3. **Ticketmaster API** - Major concerts/shows
4. **Sports Schedules** - Raiders, Golden Knights, Aces
5. **Convention Center Bookings** - Public calendars

**Scraper Architecture:**
```python
# cbi-v14-ingestion/scrape_vegas_events.py

import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

class VegasEventScraper:
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        
    def scrape_lvcva_calendar(self):
        """Scrape Las Vegas Convention & Visitors Authority calendar"""
        url = "https://www.lvcva.com/calendar/"
        
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        events = []
        for event_card in soup.find_all('div', class_='event-card'):
            event = {
                'event_name': event_card.find('h3').text.strip(),
                'event_date': self.parse_date(event_card.find('time').text),
                'venue': event_card.find('span', class_='venue').text.strip(),
                'expected_attendance': self.extract_attendance(event_card),
                'event_type': self.classify_event_type(event_card),
                'source': 'LVCVA',
                'scraped_at': datetime.utcnow()
            }
            events.append(event)
        
        return events
    
    def scrape_eventbrite(self):
        """Scrape Eventbrite for Las Vegas events"""
        # Use Eventbrite API
        api_key = os.getenv('EVENTBRITE_API_KEY')
        url = "https://www.eventbriteapi.com/v3/events/search/"
        
        params = {
            'location.address': 'Las Vegas, NV',
            'start_date.range_start': datetime.now().isoformat(),
            'start_date.range_end': (datetime.now() + timedelta(days=90)).isoformat(),
            'expand': 'venue,category'
        }
        
        headers = {'Authorization': f'Bearer {api_key}'}
        response = requests.get(url, params=params, headers=headers)
        
        events = []
        for event in response.json()['events']:
            events.append({
                'event_name': event['name']['text'],
                'event_date': event['start']['utc'],
                'venue': event['venue']['name'],
                'expected_attendance': event.get('capacity', 0),
                'event_type': event['category']['name'],
                'source': 'Eventbrite',
                'scraped_at': datetime.utcnow()
            })
        
        return events
    
    def load_to_bigquery(self, events):
        """Load scraped events to BigQuery"""
        table_id = 'cbi-v14.forecasting_data_warehouse.vegas_events_scraped'
        
        errors = self.client.insert_rows_json(table_id, events)
        
        if not errors:
            print(f"✅ Loaded {len(events)} events to BigQuery")
        else:
            print(f"❌ Errors: {errors}")

# Schedule: Run daily at 3 AM PT
```

### 2.2 Event Schema

```sql
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.vegas_events_scraped` (
  event_id STRING,
  event_name STRING,
  event_date TIMESTAMP,
  event_end_date TIMESTAMP,
  venue STRING,
  venue_address STRING,
  lat FLOAT64,
  lng FLOAT64,
  geocoord GEOGRAPHY,
  expected_attendance INT64,
  attendance_source STRING,  -- 'scraped', 'estimated', 'historical'
  event_type STRING,  -- 'Convention', 'Concert', 'Sports', 'Festival'
  event_category STRING,  -- 'Major', 'Regional', 'Local'
  source STRING,  -- 'LVCVA', 'Eventbrite', 'Ticketmaster'
  source_url STRING,
  scraped_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(event_date)
CLUSTER BY event_type, event_category;
```

---

## Component 3: Proximity-Based Math

### 3.1 Distance Calculations

**Formula:** Haversine distance between event and restaurant

```sql
-- Calculate distance between event and all restaurants
CREATE OR REPLACE FUNCTION `cbi-v14.forecasting_data_warehouse.haversine_distance`(
  lat1 FLOAT64, lng1 FLOAT64, 
  lat2 FLOAT64, lng2 FLOAT64
) RETURNS FLOAT64 AS (
  -- Returns distance in kilometers
  6371 * ACOS(
    COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * 
    COS(RADIANS(lng2) - RADIANS(lng1)) + 
    SIN(RADIANS(lat1)) * SIN(RADIANS(lat2))
  )
);
```

### 3.2 Proximity Multiplier

**Logic:** Events closer to restaurant = higher impact

```sql
CREATE OR REPLACE FUNCTION `cbi-v14.forecasting_data_warehouse.proximity_multiplier`(
  distance_km FLOAT64
) RETURNS FLOAT64 AS (
  CASE 
    WHEN distance_km < 0.5 THEN 2.5   -- Within 500m: MAX impact
    WHEN distance_km < 1.0 THEN 2.0   -- Within 1km: HIGH impact
    WHEN distance_km < 2.0 THEN 1.5   -- Within 2km: MEDIUM impact
    WHEN distance_km < 5.0 THEN 1.2   -- Within 5km: LOW impact
    ELSE 1.0                           -- Beyond 5km: NO impact
  END
);
```

### 3.3 Combined Impact Score

```sql
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.event_restaurant_impact` AS
WITH event_proximity AS (
  SELECT 
    e.event_id,
    e.event_name,
    e.event_date,
    e.expected_attendance,
    r.glide_rowID as restaurant_id,
    r.MHXYO as restaurant_name,
    
    -- Distance calculation
    `cbi-v14.forecasting_data_warehouse.haversine_distance`(
      e.lat, e.lng, r.lat, r.lng
    ) as distance_km,
    
    -- Proximity multiplier
    `cbi-v14.forecasting_data_warehouse.proximity_multiplier`(
      `cbi-v14.forecasting_data_warehouse.haversine_distance`(
        e.lat, e.lng, r.lat, r.lng
      )
    ) as proximity_multiplier,
    
    -- Attendance-based multiplier
    CASE 
      WHEN e.expected_attendance > 50000 THEN 3.0
      WHEN e.expected_attendance > 20000 THEN 2.5
      WHEN e.expected_attendance > 10000 THEN 2.0
      WHEN e.expected_attendance > 5000 THEN 1.5
      ELSE 1.2
    END as attendance_multiplier
    
  FROM `cbi-v14.forecasting_data_warehouse.vegas_events_scraped` e
  CROSS JOIN `cbi-v14.forecasting_data_warehouse.vegas_restaurants` r
  WHERE r.s8tNr = 'Open'
    AND e.event_date BETWEEN CURRENT_TIMESTAMP() AND TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
)
SELECT 
  *,
  -- Combined impact score
  proximity_multiplier * attendance_multiplier as combined_impact_score,
  
  -- Revenue opportunity calculation
  ROUND(
    (SELECT weekly_base_gallons 
     FROM `cbi-v14.forecasting_data_warehouse.vegas_restaurant_base_consumption`
     WHERE restaurant_id = ep.restaurant_id) 
    * proximity_multiplier 
    * attendance_multiplier 
    * 8.20,  -- Price per gallon
    2
  ) as estimated_revenue_opportunity
  
FROM event_proximity ep
WHERE distance_km < 5.0  -- Only include events within 5km
ORDER BY combined_impact_score DESC;
```

---

## Component 4: Heat Map Visualization

### 4.1 Frontend Component

```tsx
// dashboard-nextjs/src/components/vegas/EventHeatMap.tsx

'use client';

import { useEffect, useState } from 'react';
import { GoogleMap, LoadScript, HeatmapLayer } from '@react-google-maps/api';

interface HeatMapPoint {
  lat: number;
  lng: number;
  weight: number;
}

export function EventHeatMap() {
  const [heatmapData, setHeatmapData] = useState<HeatMapPoint[]>([]);
  
  useEffect(() => {
    async function loadHeatmapData() {
      const response = await fetch('/api/v4/vegas/heatmap-data');
      const data = await response.json();
      setHeatmapData(data);
    }
    loadHeatmapData();
  }, []);
  
  const center = { lat: 36.1699, lng: -115.1398 };  // Las Vegas center
  
  return (
    <LoadScript googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}>
      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '600px' }}
        center={center}
        zoom={12}
      >
        <HeatmapLayer
          data={heatmapData.map(point => ({
            location: new google.maps.LatLng(point.lat, point.lng),
            weight: point.weight
          }))}
          options={{
            radius: 20,
            opacity: 0.6,
            gradient: [
              'rgba(0, 255, 255, 0)',
              'rgba(0, 255, 255, 1)',
              'rgba(0, 191, 255, 1)',
              'rgba(0, 127, 255, 1)',
              'rgba(0, 63, 255, 1)',
              'rgba(0, 0, 255, 1)',
              'rgba(0, 0, 223, 1)',
              'rgba(0, 0, 191, 1)',
              'rgba(0, 0, 159, 1)',
              'rgba(0, 0, 127, 1)',
              'rgba(63, 0, 91, 1)',
              'rgba(127, 0, 63, 1)',
              'rgba(191, 0, 31, 1)',
              'rgba(255, 0, 0, 1)'
            ]
          }}
        />
      </GoogleMap>
    </LoadScript>
  );
}
```

### 4.2 Heat Map Data API

```typescript
// dashboard-nextjs/src/app/api/v4/vegas/heatmap-data/route.ts

import { NextResponse } from 'next/server';
import { executeBigQueryQuery } from '@/lib/bigquery';

export async function GET() {
  const query = `
    SELECT 
      lat,
      lng,
      combined_impact_score as weight
    FROM \`cbi-v14.forecasting_data_warehouse.event_restaurant_impact\`
    WHERE combined_impact_score > 1.5
  `;
  
  const results = await executeBigQueryQuery(query);
  
  return NextResponse.json(results);
}
```

---

## Component 5: AI-Powered Messaging

### 5.1 OpenAI Integration

```python
# scripts/generate_ai_messages.py

from openai import OpenAI
from google.cloud import bigquery

client_openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
client_bq = bigquery.Client(project='cbi-v14')

def generate_outreach_message(opportunity):
    """Generate personalized outreach message for event opportunity"""
    
    prompt = f"""
    You are a sales representative for a soybean oil supplier. 
    
    Generate a professional, concise outreach message for the following opportunity:
    
    Restaurant: {opportunity['restaurant_name']}
    Event: {opportunity['event_name']}
    Event Date: {opportunity['event_date']}
    Expected Attendance: {opportunity['expected_attendance']:,}
    Distance from Restaurant: {opportunity['distance_km']:.1f} km
    Estimated Revenue Opportunity: ${opportunity['revenue_opportunity']:,.2f}
    
    Message should:
    - Be friendly and professional
    - Mention the upcoming event
    - Highlight the opportunity to increase oil supply
    - Offer a specific action (call to schedule delivery)
    - Be under 150 words
    
    Do NOT use salesy language or excessive exclamation points.
    """
    
    response = client_openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional B2B sales assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )
    
    return response.choices[0].message.content
```

### 5.2 API Endpoint

```typescript
// dashboard-nextjs/src/app/api/v4/vegas/generate-message/route.ts

import { NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: Request) {
  const { opportunity } = await request.json();
  
  const prompt = `Generate a professional outreach message for:
  Restaurant: ${opportunity.restaurant_name}
  Event: ${opportunity.event_name}
  Revenue Opportunity: $${opportunity.revenue_opportunity}`;
  
  const completion = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [{ role: "user", content: prompt }],
    temperature: 0.7,
    max_tokens: 150,
  });
  
  return NextResponse.json({
    message: completion.choices[0].message.content
  });
}
```

---

## Component 6: Enhanced Opportunity Listings

### 6.1 Opportunity Score Calculation

```sql
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vegas_opportunity_scores` AS
WITH base_scores AS (
  SELECT 
    restaurant_id,
    restaurant_name,
    event_id,
    event_name,
    event_date,
    
    -- Revenue opportunity (normalized 0-100)
    LEAST(100, (estimated_revenue_opportunity / 1000) * 100) as revenue_score,
    
    -- Proximity score (normalized 0-100)
    CASE 
      WHEN distance_km < 0.5 THEN 100
      WHEN distance_km < 1.0 THEN 80
      WHEN distance_km < 2.0 THEN 60
      WHEN distance_km < 5.0 THEN 40
      ELSE 20
    END as proximity_score,
    
    -- Urgency score (days until event)
    CASE 
      WHEN DATE_DIFF(DATE(event_date), CURRENT_DATE(), DAY) <= 7 THEN 100
      WHEN DATE_DIFF(DATE(event_date), CURRENT_DATE(), DAY) <= 14 THEN 80
      WHEN DATE_DIFF(DATE(event_date), CURRENT_DATE(), DAY) <= 30 THEN 60
      WHEN DATE_DIFF(DATE(event_date), CURRENT_DATE(), DAY) <= 60 THEN 40
      ELSE 20
    END as urgency_score,
    
    -- Event size score
    CASE 
      WHEN expected_attendance > 50000 THEN 100
      WHEN expected_attendance > 20000 THEN 80
      WHEN expected_attendance > 10000 THEN 60
      WHEN expected_attendance > 5000 THEN 40
      ELSE 20
    END as event_size_score
    
  FROM `cbi-v14.forecasting_data_warehouse.event_restaurant_impact`
)
SELECT 
  *,
  -- Composite opportunity score (weighted average)
  ROUND(
    (revenue_score * 0.40) +      -- 40% weight on revenue
    (proximity_score * 0.25) +    -- 25% weight on proximity
    (urgency_score * 0.20) +      -- 20% weight on urgency
    (event_size_score * 0.15),    -- 15% weight on event size
  0) as opportunity_score,
  
  -- Percentage format for display
  CONCAT('+', CAST(ROUND(
    (revenue_score * 0.40) +
    (proximity_score * 0.25) +
    (urgency_score * 0.20) +
    (event_size_score * 0.15)
  ) AS STRING), '%') as opportunity_score_display
  
FROM base_scores
ORDER BY opportunity_score DESC;
```

### 6.2 Enhanced Listing Component

```tsx
// dashboard-nextjs/src/components/vegas/EnhancedOpportunityCard.tsx

interface OpportunityCardProps {
  opportunity: {
    restaurant_name: string;
    event_name: string;
    opportunity_score: number;
    revenue_opportunity: number;
    distance_km: number;
    days_until: number;
    event_type: string;
    analysis_bullets: string[];
  };
}

export function EnhancedOpportunityCard({ opportunity }: OpportunityCardProps) {
  const [aiMessage, setAiMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  async function generateMessage() {
    setLoading(true);
    const response = await fetch('/api/v4/vegas/generate-message', {
      method: 'POST',
      body: JSON.stringify({ opportunity })
    });
    const data = await response.json();
    setAiMessage(data.message);
    setLoading(false);
  }
  
  return (
    <div className="card">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold">{opportunity.event_name}</h3>
          <p className="text-sm text-text-secondary">{opportunity.restaurant_name}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-success">
            +{opportunity.opportunity_score}%
          </div>
          <div className="text-sm text-text-tertiary">opportunity</div>
        </div>
      </div>
      
      {/* Price Point */}
      <div className="bg-card-elevated p-3 rounded mb-4">
        <div className="text-3xl font-mono font-bold">
          ${opportunity.revenue_opportunity.toLocaleString()}
        </div>
        <div className="text-sm text-text-tertiary">estimated revenue</div>
      </div>
      
      {/* Analysis Bullets */}
      <div className="space-y-2 mb-4">
        {opportunity.analysis_bullets.map((bullet, idx) => (
          <div key={idx} className="flex items-start gap-2">
            <span className="text-primary mt-1">✓</span>
            <p className="text-sm text-text-secondary">{bullet}</p>
          </div>
        ))}
      </div>
      
      {/* AI Message */}
      {aiMessage && (
        <div className="bg-card-elevated p-4 rounded mb-4 border-l-4 border-primary">
          <p className="text-sm italic">{aiMessage}</p>
        </div>
      )}
      
      {/* Actions */}
      <div className="flex gap-2">
        <button 
          onClick={generateMessage}
          disabled={loading}
          className="btn-primary flex-1"
        >
          {loading ? 'Generating...' : 'AI gently'}
        </button>
        <button className="btn-secondary">Download</button>
        <button className="btn-secondary">Enhance</button>
      </div>
    </div>
  );
}
```

---

## Implementation Timeline

| Week | Component | Deliverables |
|------|-----------|--------------|
| 1 | Geospatial Foundation | Geocoding script, database schema updates |
| 1-2 | Event Scraper | LVCVA + Eventbrite scrapers, BigQuery pipeline |
| 2 | Proximity Math | Distance calculations, impact scoring |
| 3 | Heat Map Visualization | Google Maps integration, frontend component |
| 3-4 | AI Messaging | OpenAI integration, message generation |
| 4 | Enhanced Listings | Opportunity scoring, enhanced UI |

---

## Cost Estimates

**Monthly Operational Costs:**
- Google Maps API: $50-100/month (geocoding + visualization)
- OpenAI API: $20-50/month (GPT-4 messages)
- Eventbrite API: Free tier (500 events/month)
- BigQuery Storage: +$2/month (additional event data)
- **Total: $72-152/month**

**One-Time Development:**
- Geocoding initial dataset: $5 (one-time)
- Development time: 80-100 hours

---

## Success Metrics

- [ ] All 142 restaurants geocoded
- [ ] Event scraper running daily
- [ ] Heat map displaying 90-day event forecast
- [ ] Proximity calculations within 5km radius
- [ ] AI messages generated in <3 seconds
- [ ] Opportunity scores calculated for all event/restaurant pairs
- [ ] UI matches reference design

---

## Next Steps

1. **Approval:** Get client sign-off on feature set and budget
2. **API Keys:** Obtain Google Maps, OpenAI, Eventbrite credentials
3. **Geocoding:** Run initial geocoding of existing restaurants/casinos
4. **Event Scraper:** Deploy first version targeting LVCVA calendar
5. **Prototype:** Build heat map visualization MVP
6. **Testing:** Validate proximity calculations with known events

---

**Document Status:** DRAFT - Awaiting Approval  
**Created:** November 5, 2025  
**Owner:** CBI-V14 Development Team







