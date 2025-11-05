#!/usr/bin/env python3
"""
Geocode events and calculate proximity to restaurants
100% FREE - Uses Nominatim + Haversine math
"""

import requests
import time
from google.cloud import bigquery
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class EventProximityCalculator:
    """Free geocoding and proximity calculations"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.headers = {
            'User-Agent': 'CBI-Vegas-Intel/1.0 (business-intelligence@summitmarine.com)'
        }
    
    def geocode_events(self):
        """Add lat/lng to events table"""
        print("\n" + "="*60)
        print("🗺️  GEOCODING EVENTS (FREE)")
        print("="*60)
        
        # First add columns if needed
        try:
            alter_query = f"""
            ALTER TABLE `{PROJECT_ID}.{DATASET_ID}.vegas_events`
            ADD COLUMN IF NOT EXISTS lat FLOAT64,
            ADD COLUMN IF NOT EXISTS lng FLOAT64
            """
            self.client.query(alter_query).result()
        except:
            pass
        
        # Get events without coordinates
        query = f"""
        SELECT event_id, event_name, venue
        FROM `{PROJECT_ID}.{DATASET_ID}.vegas_events`
        WHERE lat IS NULL
        """
        
        events = self.client.query(query).to_dataframe()
        total = len(events)
        
        print(f"Found {total} events to geocode")
        
        for idx, row in events.iterrows():
            event_name = row['event_name']
            venue = row['venue']
            event_id = row['event_id']
            
            # Build address
            address = f"{venue}, Las Vegas, NV"
            
            print(f"[{idx+1}/{total}] {event_name[:35]:35}...", end=" ")
            
            lat, lng = self._geocode_free(address)
            
            if lat and lng:
                print(f"✅ ({lat:.4f}, {lng:.4f})")
                
                # Update BigQuery
                update_query = f"""
                UPDATE `{PROJECT_ID}.{DATASET_ID}.vegas_events`
                SET lat = @lat, lng = @lng
                WHERE event_id = @event_id
                """
                
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("lat", "FLOAT64", lat),
                        bigquery.ScalarQueryParameter("lng", "FLOAT64", lng),
                        bigquery.ScalarQueryParameter("event_id", "STRING", event_id),
                    ]
                )
                
                self.client.query(update_query, job_config=job_config).result()
            else:
                print(f"❌ Failed")
        
        print(f"\n✅ Event geocoding complete")
    
    def create_proximity_functions(self):
        """Create BigQuery UDFs for proximity calculations"""
        print("\n" + "="*60)
        print("📐 CREATING PROXIMITY FUNCTIONS")
        print("="*60)
        
        # Haversine distance function
        haversine_sql = f"""
        CREATE OR REPLACE FUNCTION `{PROJECT_ID}.{DATASET_ID}.haversine_distance`(
          lat1 FLOAT64, lng1 FLOAT64,
          lat2 FLOAT64, lng2 FLOAT64
        ) 
        RETURNS FLOAT64
        LANGUAGE js AS r'''
          function toRadians(deg) {{
            return deg * (Math.PI / 180);
          }}
          
          var R = 6371; // Radius of Earth in km
          var dLat = toRadians(lat2 - lat1);
          var dLng = toRadians(lng2 - lng1);
          
          var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
                  Math.sin(dLng / 2) * Math.sin(dLng / 2);
          
          var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
          var distance = R * c;
          
          return distance;
        ''';
        """
        
        self.client.query(haversine_sql).result()
        print("  ✅ Created haversine_distance() function")
        
        # Proximity multiplier function
        proximity_mult_sql = f"""
        CREATE OR REPLACE FUNCTION `{PROJECT_ID}.{DATASET_ID}.proximity_multiplier`(
          distance_km FLOAT64
        )
        RETURNS FLOAT64 AS (
          CASE 
            WHEN distance_km < 0.5 THEN 2.5   -- Within 500m: MAX impact
            WHEN distance_km < 1.0 THEN 2.0   -- Within 1km: HIGH impact
            WHEN distance_km < 2.0 THEN 1.5   -- Within 2km: MEDIUM impact
            WHEN distance_km < 5.0 THEN 1.2   -- Within 5km: LOW impact
            ELSE 1.0                           -- Beyond 5km: NO impact
          END
        );
        """
        
        self.client.query(proximity_mult_sql).result()
        print("  ✅ Created proximity_multiplier() function")
    
    def create_event_restaurant_impact_view(self):
        """Create view matching events to nearby restaurants"""
        print("\n" + "="*60)
        print("🎯 CREATING EVENT-RESTAURANT IMPACT VIEW")
        print("="*60)
        
        view_sql = f"""
        CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.event_restaurant_impact` AS
        WITH event_restaurant_pairs AS (
          SELECT 
            e.event_id,
            e.event_name,
            e.event_date,
            e.venue as event_venue,
            e.event_type,
            e.expected_attendance,
            e.lat as event_lat,
            e.lng as event_lng,
            
            r.glide_rowID as restaurant_id,
            r.MHXYO as restaurant_name,
            r.lat as restaurant_lat,
            r.lng as restaurant_lng,
            
            -- Calculate distance
            `{PROJECT_ID}.{DATASET_ID}.haversine_distance`(
              e.lat, e.lng, r.lat, r.lng
            ) as distance_km,
            
            -- Get restaurant base consumption
            COUNT(f.glide_rowID) as fryer_count,
            ROUND(SUM(f.xhrM0), 2) as total_capacity_lbs,
            COALESCE(cm.oil_multiplier, 1.0) as cuisine_multiplier,
            cm.cuisine_type
            
          FROM `{PROJECT_ID}.{DATASET_ID}.vegas_events` e
          CROSS JOIN `{PROJECT_ID}.{DATASET_ID}.vegas_restaurants` r
          LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.vegas_fryers` f
            ON r.glide_rowID = f.`2uBBn`
          LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.vegas_cuisine_multipliers` cm
            ON r.glide_rowID = cm.glide_rowID
          WHERE 
            e.lat IS NOT NULL 
            AND r.lat IS NOT NULL
            AND r.s8tNr = 'Open'
            AND e.event_date >= CURRENT_DATE()
          GROUP BY 
            e.event_id, e.event_name, e.event_date, e.venue, e.event_type, 
            e.expected_attendance, e.lat, e.lng,
            r.glide_rowID, r.MHXYO, r.lat, r.lng,
            cm.oil_multiplier, cm.cuisine_type
        )
        SELECT 
          *,
          -- Proximity multiplier
          `{PROJECT_ID}.{DATASET_ID}.proximity_multiplier`(distance_km) as proximity_multiplier,
          
          -- Attendance-based surge multiplier
          CASE 
            WHEN expected_attendance >= 100000 THEN 3.5  -- F1, CES
            WHEN expected_attendance >= 50000 THEN 2.8   -- SEMA, NAB
            WHEN expected_attendance >= 20000 THEN 2.2   -- Raiders, medium conventions
            WHEN expected_attendance >= 10000 THEN 1.8   -- Golden Knights
            ELSE 1.3
          END as attendance_multiplier,
          
          -- Combined impact score (proximity × attendance)
          `{PROJECT_ID}.{DATASET_ID}.proximity_multiplier`(distance_km) *
          CASE 
            WHEN expected_attendance >= 100000 THEN 3.5
            WHEN expected_attendance >= 50000 THEN 2.8
            WHEN expected_attendance >= 20000 THEN 2.2
            WHEN expected_attendance >= 10000 THEN 1.8
            ELSE 1.3
          END as combined_impact_score,
          
          -- Base weekly gallons (4 TPM default, with cuisine multiplier)
          ROUND((total_capacity_lbs * 4) / 7.6 * cuisine_multiplier, 2) as weekly_base_gallons,
          
          -- Event surge gallons (3-day event default)
          ROUND(
            (total_capacity_lbs * 4) / 7.6 * cuisine_multiplier * 
            (3.0 / 7.0) *  -- 3-day event
            `{PROJECT_ID}.{DATASET_ID}.proximity_multiplier`(distance_km) *
            CASE 
              WHEN expected_attendance >= 100000 THEN 3.5
              WHEN expected_attendance >= 50000 THEN 2.8
              WHEN expected_attendance >= 20000 THEN 2.2
              WHEN expected_attendance >= 10000 THEN 1.8
              ELSE 1.3
            END,
            0
          ) as event_surge_gallons,
          
          -- Revenue opportunity (at $8.20/gal default)
          ROUND(
            (total_capacity_lbs * 4) / 7.6 * cuisine_multiplier * 
            (3.0 / 7.0) *
            `{PROJECT_ID}.{DATASET_ID}.proximity_multiplier`(distance_km) *
            CASE 
              WHEN expected_attendance >= 100000 THEN 3.5
              WHEN expected_attendance >= 50000 THEN 2.8
              WHEN expected_attendance >= 20000 THEN 2.2
              WHEN expected_attendance >= 10000 THEN 1.8
              ELSE 1.3
            END *
            0.68 *  -- 68% upsell success rate
            8.20,   -- Price per gallon
            0
          ) as revenue_opportunity,
          
          -- Days until event
          DATE_DIFF(DATE(event_date), CURRENT_DATE(), DAY) as days_until
          
        FROM event_restaurant_pairs
        WHERE distance_km < 10.0  -- Only events within 10km
        ORDER BY combined_impact_score DESC;
        """
        
        self.client.query(view_sql).result()
        print("  ✅ Created event_restaurant_impact view")
    
    def _geocode_free(self, address: str) -> tuple:
        """Geocode using free Nominatim"""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us'
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            time.sleep(1.1)  # Rate limit
            
            if response.ok and response.json():
                result = response.json()[0]
                return float(result['lat']), float(result['lon'])
        except:
            pass
        
        return None, None

def main():
    """Execute event geocoding and proximity calculations"""
    print("="*60)
    print("EVENT PROXIMITY INTELLIGENCE")
    print("100% FREE - Nominatim + Haversine Math")
    print("="*60)
    
    calc = EventProximityCalculator()
    
    # Step 1: Geocode events
    calc.geocode_events()
    
    # Step 2: Create proximity functions
    calc.create_proximity_functions()
    
    # Step 3: Create event-restaurant impact view
    calc.create_event_restaurant_impact_view()
    
    print("\n" + "="*60)
    print("🎉 PROXIMITY CALCULATIONS COMPLETE")
    print("="*60)
    print("\nCreated:")
    print("  - haversine_distance() UDF")
    print("  - proximity_multiplier() UDF")
    print("  - event_restaurant_impact view")

if __name__ == "__main__":
    main()

