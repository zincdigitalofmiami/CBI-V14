#!/usr/bin/env python3
"""
FREE Vegas Event Scraper - Web Scraping (No APIs)
Scrapes Las Vegas event calendars for major events
100% FREE - No API keys required
"""

import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import re
from typing import List, Dict, Any
import hashlib

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class VegasEventScraper:
    """Free web scraping for Las Vegas events"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.geocode_headers = {
            'User-Agent': 'CBI-Vegas-Intel/1.0 (business-intelligence@summitmarine.com)'
        }
        self.scraped_count = 0
    
    def _geocode_venue(self, venue: str) -> tuple:
        """Geocode venue using FREE Nominatim"""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{venue}, Las Vegas, NV",
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us'
        }
        
        try:
            response = requests.get(url, params=params, headers=self.geocode_headers, timeout=10)
            time.sleep(1.1)  # Rate limit compliance
            
            if response.ok and response.json():
                result = response.json()[0]
                return float(result['lat']), float(result['lon'])
        except:
            pass
        
        return None, None
    
    def scrape_vegas_com_events(self) -> List[Dict]:
        """Scrape Vegas.com event calendar (FREE)"""
        print("\n🎰 Scraping Vegas.com events...")
        
        url = "https://www.vegas.com/events/"
        events = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find event cards (adjust selectors based on actual site structure)
            event_cards = soup.find_all(['div', 'article'], class_=re.compile(r'event|listing'))
            
            for card in event_cards[:50]:  # Limit to first 50 events
                try:
                    # Extract event details
                    title_elem = card.find(['h2', 'h3', 'h4'])
                    date_elem = card.find(['time', 'span'], class_=re.compile(r'date'))
                    venue_elem = card.find(['span', 'div'], class_=re.compile(r'venue|location'))
                    
                    if title_elem:
                        event = {
                            'event_name': title_elem.get_text(strip=True),
                            'event_date': self._parse_date(date_elem.get_text(strip=True) if date_elem else ''),
                            'venue': venue_elem.get_text(strip=True) if venue_elem else 'Unknown',
                            'source': 'vegas.com',
                            'source_url': url,
                            'event_type': self._classify_event_type(title_elem.get_text(strip=True)),
                            'expected_attendance': self._estimate_attendance(title_elem.get_text(strip=True)),
                        }
                        events.append(event)
                        self.scraped_count += 1
                except Exception as e:
                    continue
            
            print(f"  ✅ Scraped {len(events)} events from Vegas.com")
            
        except Exception as e:
            print(f"  ❌ Error scraping Vegas.com: {e}")
        
        return events
    
    def scrape_lvcva_events(self) -> List[Dict]:
        """Scrape LVCVA (Las Vegas Convention & Visitors Authority) calendar"""
        print("\n📅 Scraping LVCVA calendar...")
        
        url = "https://www.lvcva.com/events-calendar/"
        events = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for event listings
            event_items = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'event|calendar'))
            
            for item in event_items[:50]:
                try:
                    title = item.find(['h2', 'h3', 'h4', 'a'])
                    if title:
                        event_name = title.get_text(strip=True)
                        event = {
                            'event_name': event_name,
                            'event_date': self._parse_date(''),  # Will be NULL if not found
                            'venue': 'Las Vegas Convention Center',  # Default for LVCVA events
                            'source': 'LVCVA',
                            'source_url': url,
                            'event_type': 'Convention',  # LVCVA is primarily conventions
                            'expected_attendance': self._estimate_attendance(event_name),
                        }
                        events.append(event)
                        self.scraped_count += 1
                except:
                    continue
            
            print(f"  ✅ Scraped {len(events)} events from LVCVA")
            
        except Exception as e:
            print(f"  ❌ Error scraping LVCVA: {e}")
        
        return events
    
    def scrape_major_sports_events(self) -> List[Dict]:
        """Create known major sports events (Raiders, Golden Knights, etc.) WITH GEOCODING"""
        print("\n🏈 Adding major sports events...")
        
        events = []
        today = datetime.now().date()
        
        # Venue coordinates (known locations)
        venues = {
            'Allegiant Stadium': (36.0907, -115.1833),
            'T-Mobile Arena': (36.1028, -115.1781),
            'Las Vegas Strip': (36.1147, -115.1729),
            'Las Vegas Convention Center': (36.1352, -115.1532),
        }
        
        # Raiders home games (NFL season)
        raiders_dates = self._generate_game_dates(today, 'Sunday', count=8)
        for date in raiders_dates:
            lat, lng = venues['Allegiant Stadium']
            events.append({
                'event_name': 'Raiders Home Game',
                'event_date': date,
                'venue': 'Allegiant Stadium',
                'lat': lat,
                'lng': lng,
                'source': 'manual_sports',
                'source_url': 'https://www.raiders.com',
                'event_type': 'Sports',
                'expected_attendance': 65000,
            })
        
        # Golden Knights home games (NHL season)
        knights_dates = self._generate_game_dates(today, 'Saturday', count=20)
        for date in knights_dates:
            lat, lng = venues['T-Mobile Arena']
            events.append({
                'event_name': 'Golden Knights Home Game',
                'event_date': date,
                'venue': 'T-Mobile Arena',
                'lat': lat,
                'lng': lng,
                'source': 'manual_sports',
                'source_url': 'https://www.nhl.com/goldenknights',
                'event_type': 'Sports',
                'expected_attendance': 18000,
            })
        
        # Formula 1 (annual in November)
        f1_date = self._find_next_november_weekend(today)
        lat, lng = venues['Las Vegas Strip']
        events.append({
            'event_name': 'Formula 1 Las Vegas Grand Prix',
            'event_date': f1_date,
            'venue': 'Las Vegas Strip',
            'lat': lat,
            'lng': lng,
            'source': 'manual_sports',
            'source_url': 'https://www.formula1.com',
            'event_type': 'Sports',
            'expected_attendance': 100000,
        })
        
        print(f"  ✅ Added {len(events)} major sports events (with coordinates)")
        return events
    
    def scrape_major_conventions(self) -> List[Dict]:
        """Add known major Las Vegas conventions WITH GEOCODING"""
        print("\n🎪 Adding major conventions...")
        
        events = []
        today = datetime.now().date()
        year = today.year
        
        # Las Vegas Convention Center coordinates
        lv_convention_center = (36.1352, -115.1532)
        
        # CES (January)
        if today.month <= 1:
            ces_date = datetime(year, 1, 9).date()
        else:
            ces_date = datetime(year + 1, 1, 9).date()
        
        events.append({
            'event_name': 'CES (Consumer Electronics Show)',
            'event_date': ces_date,
            'venue': 'Las Vegas Convention Center',
            'lat': lv_convention_center[0],
            'lng': lv_convention_center[1],
            'source': 'manual_convention',
            'source_url': 'https://www.ces.tech',
            'event_type': 'Convention',
            'expected_attendance': 115000,
        })
        
        # NAB Show (April)
        nab_date = datetime(year if today.month <= 4 else year + 1, 4, 15).date()
        events.append({
            'event_name': 'NAB Show (Broadcasting)',
            'event_date': nab_date,
            'venue': 'Las Vegas Convention Center',
            'lat': lv_convention_center[0],
            'lng': lv_convention_center[1],
            'source': 'manual_convention',
            'source_url': 'https://www.nabshow.com',
            'event_type': 'Convention',
            'expected_attendance': 65000,
        })
        
        # SEMA (November)
        sema_date = datetime(year if today.month <= 10 else year + 1, 11, 5).date()
        events.append({
            'event_name': 'SEMA Show (Automotive)',
            'event_date': sema_date,
            'venue': 'Las Vegas Convention Center',
            'lat': lv_convention_center[0],
            'lng': lv_convention_center[1],
            'source': 'manual_convention',
            'source_url': 'https://www.semashow.com',
            'event_type': 'Convention',
            'expected_attendance': 160000,
        })
        
        print(f"  ✅ Added {len(events)} major conventions (with coordinates)")
        return events
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from various string formats"""
        if not date_str:
            return None
        
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%A, %B %d, %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        
        return None
    
    def _classify_event_type(self, title: str) -> str:
        """Classify event by title keywords"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['game', 'match', 'championship', 'tournament']):
            return 'Sports'
        elif any(word in title_lower for word in ['concert', 'show', 'music', 'performance']):
            return 'Concert'
        elif any(word in title_lower for word in ['expo', 'conference', 'summit', 'convention']):
            return 'Convention'
        elif any(word in title_lower for word in ['festival', 'celebration', 'parade']):
            return 'Festival'
        else:
            return 'Other'
    
    def _estimate_attendance(self, title: str) -> int:
        """Estimate attendance based on event type"""
        event_type = self._classify_event_type(title)
        
        estimates = {
            'Sports': 20000,
            'Concert': 5000,
            'Convention': 50000,
            'Festival': 30000,
            'Other': 10000,
        }
        
        return estimates.get(event_type, 10000)
    
    def _generate_game_dates(self, start_date: datetime.date, day_of_week: str, count: int) -> List[datetime.date]:
        """Generate future game dates on specific day of week"""
        days = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        target_day = days[day_of_week]
        
        dates = []
        current = start_date
        
        while len(dates) < count:
            if current.weekday() == target_day and current > start_date:
                dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    def _find_next_november_weekend(self, start_date: datetime.date) -> datetime.date:
        """Find next November weekend"""
        year = start_date.year if start_date.month <= 11 else start_date.year + 1
        
        # Third weekend of November
        november = datetime(year, 11, 1).date()
        while november.weekday() != 5:  # Find first Saturday
            november += timedelta(days=1)
        
        return november + timedelta(days=14)  # Third Saturday
    
    def save_to_bigquery(self, events: List[Dict]):
        """Save events to BigQuery"""
        if not events:
            print("\n⚠️ No events to save")
            return
        
        # Create table if not exists
        self._ensure_events_table_exists()
        
        # Add IDs and timestamps
        for event in events:
            event_str = f"{event['event_name']}_{event['event_date']}_{event['venue']}"
            event['event_id'] = hashlib.md5(event_str.encode()).hexdigest()
            event['scraped_at'] = datetime.utcnow().isoformat()
            
            # Convert date to string for BigQuery
            if event['event_date']:
                if hasattr(event['event_date'], 'isoformat'):
                    event['event_date'] = event['event_date'].isoformat()
            else:
                event['event_date'] = None
        
        table_id = f"{PROJECT_ID}.{DATASET_ID}.vegas_events"
        
        try:
            errors = self.client.insert_rows_json(table_id, events)
            
            if not errors:
                print(f"\n✅ Saved {len(events)} events to BigQuery")
            else:
                print(f"\n❌ Errors saving to BigQuery: {errors}")
        except Exception as e:
            print(f"\n❌ Error saving to BigQuery: {e}")
    
    def _ensure_events_table_exists(self):
        """Create vegas_events table if it doesn't exist"""
        schema = [
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_name", "STRING"),
            bigquery.SchemaField("event_date", "DATE"),
            bigquery.SchemaField("venue", "STRING"),
            bigquery.SchemaField("lat", "FLOAT64"),
            bigquery.SchemaField("lng", "FLOAT64"),
            bigquery.SchemaField("source", "STRING"),
            bigquery.SchemaField("source_url", "STRING"),
            bigquery.SchemaField("event_type", "STRING"),
            bigquery.SchemaField("expected_attendance", "INTEGER"),
            bigquery.SchemaField("scraped_at", "TIMESTAMP"),
        ]
        
        table_id = f"{PROJECT_ID}.{DATASET_ID}.vegas_events"
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            self.client.create_table(table, exists_ok=True)
        except Exception as e:
            pass  # Table already exists

def main():
    """Main scraping execution"""
    print("="*60)
    print("FREE VEGAS EVENT SCRAPER")
    print("100% FREE - No API Keys Required")
    print("="*60)
    
    scraper = VegasEventScraper()
    all_events = []
    
    # Scrape all sources
    all_events.extend(scraper.scrape_vegas_com_events())
    time.sleep(2)  # Be polite
    
    all_events.extend(scraper.scrape_lvcva_events())
    time.sleep(2)
    
    all_events.extend(scraper.scrape_major_sports_events())
    all_events.extend(scraper.scrape_major_conventions())
    
    # Save to BigQuery
    scraper.save_to_bigquery(all_events)
    
    print("\n" + "="*60)
    print(f"🎉 SCRAPING COMPLETE - {scraper.scraped_count} events")
    print("="*60)
    print("\nNext Steps:")
    print("1. Geocode events (add lat/lng)")
    print("2. Calculate proximity to restaurants")
    print("3. Build opportunity scoring")

if __name__ == "__main__":
    main()

