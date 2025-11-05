#!/usr/bin/env python3
"""
FREE Geocoding for Vegas Intel - Using OpenStreetMap Nominatim
NO API KEYS REQUIRED - 100% FREE
Rate Limit: 1 request/second (compliant)
"""

import requests
import time
from google.cloud import bigquery
from datetime import datetime
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class FreeGeocoder:
    """Free geocoding using OpenStreetMap Nominatim"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'CBI-Vegas-Intel/1.0 (business-intelligence@summitmarine.com)'
        }
        self.geocoded_count = 0
        self.failed_count = 0
    
    def geocode_address(self, address: str) -> tuple:
        """
        Geocode single address using FREE Nominatim API
        Returns: (lat, lng) or (None, None) if failed
        """
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us'  # Limit to USA
        }
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            # Rate limit compliance: 1 req/sec
            time.sleep(1.1)
            
            if response.ok and response.json():
                result = response.json()[0]
                lat = float(result['lat'])
                lng = float(result['lon'])
                self.geocoded_count += 1
                return lat, lng
            else:
                self.failed_count += 1
                return None, None
                
        except Exception as e:
            print(f"  ❌ Geocoding error: {e}")
            self.failed_count += 1
            return None, None
    
    def geocode_casinos(self):
        """Geocode all casinos from vegas_casinos table"""
        print("\n" + "="*60)
        print("🗺️  GEOCODING CASINOS (FREE - OpenStreetMap)")
        print("="*60)
        
        # Get casinos without coordinates
        query = f"""
        SELECT 
          glide_rowID,
          Name,
          L9K9x as location
        FROM `{PROJECT_ID}.{DATASET_ID}.vegas_casinos`
        ORDER BY Name
        """
        
        casinos = self.client.query(query).to_dataframe()
        total = len(casinos)
        
        print(f"Found {total} casinos to geocode")
        print(f"Estimated time: ~{total * 1.1 / 60:.1f} minutes")
        print("")
        
        updates = []
        
        for idx, row in casinos.iterrows():
            casino_name = row['Name']
            location = row['location']
            row_id = row['glide_rowID']
            
            # Build full address for geocoding
            if location and location != 'Multiple':
                address = f"{casino_name}, {location}"
            else:
                address = f"{casino_name}, Las Vegas, NV"
            
            print(f"[{idx+1}/{total}] Geocoding: {casino_name[:30]:30}...", end=" ")
            
            lat, lng = self.geocode_address(address)
            
            if lat and lng:
                print(f"✅ ({lat:.4f}, {lng:.4f})")
                updates.append({
                    'glide_rowID': row_id,
                    'lat': lat,
                    'lng': lng,
                    'geocoded_at': datetime.utcnow(),
                    'geocode_source': 'OSM_Nominatim',
                    'geocode_address': address
                })
            else:
                print(f"❌ Failed")
        
        # Save to BigQuery
        if updates:
            print(f"\n💾 Saving {len(updates)} geocoded locations to BigQuery...")
            self._update_casino_coordinates(updates)
        
        print(f"\n✅ Geocoding complete: {self.geocoded_count} success, {self.failed_count} failed")
    
    def geocode_restaurants(self):
        """Geocode restaurants by linking to their casino location"""
        print("\n" + "="*60)
        print("🗺️  GEOCODING RESTAURANTS (via Casino linkage)")
        print("="*60)
        
        # Strategy: Most restaurants are IN casinos, so we can inherit coordinates
        # For standalone restaurants, we'll geocode separately
        
        query = f"""
        SELECT 
          r.glide_rowID as restaurant_id,
          r.MHXYO as restaurant_name,
          r.`2Ca0T` as casino_link,
          c.Name as casino_name,
          c.lat as casino_lat,
          c.lng as casino_lng
        FROM `{PROJECT_ID}.{DATASET_ID}.vegas_restaurants` r
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.vegas_casinos` c
          ON r.`2Ca0T` = c.glide_rowID
        WHERE r.s8tNr = 'Open'
        ORDER BY r.MHXYO
        """
        
        restaurants = self.client.query(query).to_dataframe()
        total = len(restaurants)
        
        print(f"Found {total} restaurants")
        
        updates = []
        standalone_count = 0
        inherited_count = 0
        
        for idx, row in restaurants.iterrows():
            rest_name = row['restaurant_name']
            rest_id = row['restaurant_id']
            casino_lat = row.get('casino_lat')
            casino_lng = row.get('casino_lng')
            
            print(f"[{idx+1}/{total}] {rest_name[:40]:40}...", end=" ")
            
            # If restaurant is in a casino with coordinates, inherit them
            if casino_lat and casino_lng and pd.notna(casino_lat):
                lat, lng = float(casino_lat), float(casino_lng)
                print(f"✅ Inherited from casino ({lat:.4f}, {lng:.4f})")
                inherited_count += 1
                source = 'casino_inherited'
                address = row.get('casino_name', 'Unknown Casino')
            else:
                # Standalone restaurant - geocode directly
                address = f"{rest_name}, Las Vegas, NV"
                lat, lng = self.geocode_address(address)
                if lat and lng:
                    print(f"✅ Geocoded ({lat:.4f}, {lng:.4f})")
                    standalone_count += 1
                    source = 'OSM_Nominatim'
                else:
                    print(f"❌ Failed")
                    continue
            
            updates.append({
                'glide_rowID': rest_id,
                'lat': lat,
                'lng': lng,
                'geocoded_at': datetime.utcnow(),
                'geocode_source': source,
                'geocode_address': address
            })
        
        # Save to BigQuery
        if updates:
            print(f"\n💾 Saving {len(updates)} restaurant locations to BigQuery...")
            self._update_restaurant_coordinates(updates)
        
        print(f"\n✅ Restaurant geocoding complete:")
        print(f"   - {inherited_count} inherited from casinos")
        print(f"   - {standalone_count} geocoded standalone")
        print(f"   - {total - len(updates)} failed")
    
    def _update_casino_coordinates(self, updates: list):
        """Update casino table with coordinates"""
        # First, ensure columns exist
        try:
            alter_query = f"""
            ALTER TABLE `{PROJECT_ID}.{DATASET_ID}.vegas_casinos`
            ADD COLUMN IF NOT EXISTS lat FLOAT64,
            ADD COLUMN IF NOT EXISTS lng FLOAT64,
            ADD COLUMN IF NOT EXISTS geocoded_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS geocode_source STRING,
            ADD COLUMN IF NOT EXISTS geocode_address STRING
            """
            self.client.query(alter_query).result()
        except Exception as e:
            print(f"  Note: {e}")
        
        # Update each casino using parameterized query
        for update in updates:
            update_query = f"""
            UPDATE `{PROJECT_ID}.{DATASET_ID}.vegas_casinos`
            SET 
              lat = @lat,
              lng = @lng,
              geocoded_at = TIMESTAMP(@geocoded_at),
              geocode_source = @geocode_source,
              geocode_address = @geocode_address
            WHERE glide_rowID = @glide_rowID
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("lat", "FLOAT64", update['lat']),
                    bigquery.ScalarQueryParameter("lng", "FLOAT64", update['lng']),
                    bigquery.ScalarQueryParameter("geocoded_at", "STRING", update['geocoded_at'].isoformat()),
                    bigquery.ScalarQueryParameter("geocode_source", "STRING", update['geocode_source']),
                    bigquery.ScalarQueryParameter("geocode_address", "STRING", update['geocode_address']),
                    bigquery.ScalarQueryParameter("glide_rowID", "STRING", update['glide_rowID']),
                ]
            )
            
            self.client.query(update_query, job_config=job_config).result()
        
        print(f"✅ Updated {len(updates)} casinos in BigQuery")
    
    def _update_restaurant_coordinates(self, updates: list):
        """Update restaurant table with coordinates"""
        # First, ensure columns exist
        try:
            alter_query = f"""
            ALTER TABLE `{PROJECT_ID}.{DATASET_ID}.vegas_restaurants`
            ADD COLUMN IF NOT EXISTS lat FLOAT64,
            ADD COLUMN IF NOT EXISTS lng FLOAT64,
            ADD COLUMN IF NOT EXISTS geocoded_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS geocode_source STRING,
            ADD COLUMN IF NOT EXISTS geocode_address STRING
            """
            self.client.query(alter_query).result()
        except Exception as e:
            print(f"  Note: {e}")
        
        # Update each restaurant using parameterized query
        for update in updates:
            update_query = f"""
            UPDATE `{PROJECT_ID}.{DATASET_ID}.vegas_restaurants`
            SET 
              lat = @lat,
              lng = @lng,
              geocoded_at = TIMESTAMP(@geocoded_at),
              geocode_source = @geocode_source,
              geocode_address = @geocode_address
            WHERE glide_rowID = @glide_rowID
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("lat", "FLOAT64", update['lat']),
                    bigquery.ScalarQueryParameter("lng", "FLOAT64", update['lng']),
                    bigquery.ScalarQueryParameter("geocoded_at", "STRING", update['geocoded_at'].isoformat()),
                    bigquery.ScalarQueryParameter("geocode_source", "STRING", update['geocode_source']),
                    bigquery.ScalarQueryParameter("geocode_address", "STRING", update['geocode_address']),
                    bigquery.ScalarQueryParameter("glide_rowID", "STRING", update['glide_rowID']),
                ]
            )
            
            self.client.query(update_query, job_config=job_config).result()
        
        print(f"✅ Updated {len(updates)} restaurants in BigQuery")

import pandas as pd

def main():
    """Main geocoding execution"""
    print("="*60)
    print("FREE GEOCODING - VEGAS INTEL")
    print("Using: OpenStreetMap Nominatim (100% FREE)")
    print("Rate Limit: 1 req/sec (compliant)")
    print("="*60)
    
    geocoder = FreeGeocoder()
    
    # Step 1: Geocode casinos (foundation)
    geocoder.geocode_casinos()
    
    # Step 2: Geocode restaurants (inherit from casinos when possible)
    geocoder.geocode_restaurants()
    
    print("\n" + "="*60)
    print("🎉 GEOCODING COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("1. Verify coordinates in BigQuery")
    print("2. Build event scraper")
    print("3. Implement proximity calculations")
    print("4. Create heat map visualization")

if __name__ == "__main__":
    main()

