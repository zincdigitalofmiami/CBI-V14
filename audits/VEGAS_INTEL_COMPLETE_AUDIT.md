# Vegas Intel Complete System Audit
**Date:** November 5, 2025  
**Status:** Audit Complete - Ready for Implementation  
**Approach:** No paid APIs - All free/open-source solutions

---

## Audit Summary

### ✅ What We Have (Working)

**1. Data Foundation**
- ✅ 151 restaurants (with Glide rowIDs)
- ✅ 31 casinos (with REAL street addresses)
- ✅ 421 fryers (with capacity data)
- ✅ Cuisine multipliers (142 restaurants classified)
- ✅ Glide API ingestion (READ-ONLY, working)

**2. API Endpoints (5)**
- ✅ `/api/v4/vegas/metrics` - Sales overview
- ✅ `/api/v4/vegas/upsell-opportunities` - Opportunities
- ✅ `/api/v4/vegas/events` - Event multipliers
- ✅ `/api/v4/vegas/customers` - Customer matrix
- ✅ `/api/v4/vegas/margin-alerts` - Margin protection

**3. UI Components (5)**
- ✅ `SalesIntelligenceOverview.tsx`
- ✅ `EventDrivenUpsell.tsx`
- ✅ `EventVolumeMultipliers.tsx`
- ✅ `CustomerRelationshipMatrix.tsx`
- ✅ `MarginProtectionAlerts.tsx`

**4. Math/Calculations**
- ✅ Base formula: `(capacity × TPM × multiplier) / 7.6`
- ✅ Kevin override parameters working
- ✅ NULL handling for missing inputs
- ✅ ZL cost integration from Dashboard

**5. Infrastructure**
- ✅ Web scraper framework (`comprehensive_web_scraper.py`)
- ✅ BigQuery integration
- ✅ Next.js/Vercel deployment

---

### ❌ What's Missing (vs. Target Images)

**1. Geographic Intelligence**
- ❌ No geocoding (restaurants/casinos have addresses but no lat/lng)
- ❌ No geographic heat map visualization
- ❌ No proximity calculations between events and restaurants

**2. Event Intelligence**
- ❌ No event scraper (no real Vegas event data)
- ❌ No event database/table
- ❌ No event-to-restaurant matching
- ❌ No proximity-based impact scoring

**3. Opportunity Scoring**
- ❌ No composite opportunity scores (+47%, +37% style)
- ❌ No detailed analysis bullets
- ❌ No event context in descriptions

**4. AI Features**
- ❌ No AI message generation
- ❌ "AI gently" button is placeholder only
- ❌ No personalized outreach text

**5. Psychographics/Demographics**
- ❌ No customer segment data
- ❌ No tourist vs local classification
- ❌ No income/luxury scoring

---

## Sample Data Verification

### Casino Addresses (REAL DATA)
```
Mandalay Bay: "3950 S. Las Vegas BLVD, Las Vegas, NV 89119"
Main Street: "200 NORTH MAIN STREET, LAS VEGAS, NV 89101"
Suncoast: "9090 Alta Dr, Las Vegas, NV"
```
✅ **Geocodable:** These addresses can be geocoded using free services

### Current Table Schema Check
- No `lat`, `lng`, or `geocoord` columns in vegas_restaurants
- No `lat`, `lng`, or `geocoord` columns in vegas_casinos
- No `vegas_events` table exists

---

## Implementation Plan (FREE SOLUTIONS ONLY)

### Phase 1: Geocoding Foundation

**Solution: OpenStreetMap Nominatim (FREE)**
- Service: https://nominatim.openstreetmap.org/
- Rate Limit: 1 request/second (acceptable for 182 locations)
- No API key required
- Attribution: Required in UI

**Implementation:**
```python
# Free geocoding using Nominatim
import requests
import time

def geocode_address_free(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'CBI-Vegas-Intel/1.0 (contact@summitmarine.com)'
    }
    
    response = requests.get(url, params=params, headers=headers)
    time.sleep(1.1)  # Rate limit compliance
    
    if response.ok and response.json():
        result = response.json()[0]
        return float(result['lat']), float(result['lon'])
    return None, None
```

**Cost:** $0/month  
**Time to geocode 182 locations:** ~3.5 minutes

---

### Phase 2: Event Scraping (FREE)

**Sources (All Free):**
1. **Las Vegas Convention Calendar** - https://www.lvcva.com/calendar/
2. **Vegas.com Events** - https://www.vegas.com/events/
3. **City of Las Vegas Events** - https://www.lasvegasnevada.gov/
4. **Visit Las Vegas** - https://www.visitlasvegas.com/events/

**Scraping Approach:**
```python
# Beautiful Soup web scraping (FREE)
from bs4 import BeautifulSoup
import requests

def scrape_vegas_events():
    """Scrape free event calendars"""
    url = "https://www.vegas.com/events/"
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    
    events = []
    for event_card in soup.find_all('div', class_='event-listing'):
        # Extract event details from HTML
        # ...
    return events
```

**Cost:** $0/month  
**Update Frequency:** Daily scraping

---

### Phase 3: Mapping Visualization (FREE)

**Solution: Leaflet.js + OpenStreetMap (FREE)**
- Library: Leaflet.js (open source)
- Tiles: OpenStreetMap (free, requires attribution)
- Heat Map Plugin: Leaflet.heat (free)

**Implementation:**
```typescript
// Free mapping with Leaflet
import L from 'leaflet';
import 'leaflet.heat';

const map = L.map('map').setView([36.1699, -115.1398], 12);

// Free OSM tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Heat map layer
const heat = L.heatLayer(heatPoints, {
  radius: 25,
  blur: 15,
  maxZoom: 17,
}).addTo(map);
```

**Cost:** $0/month  
**Attribution:** Required in UI footer

---

### Phase 4: AI Messaging (FREE/LIMITED)

**Solution: OpenAI Free Tier + Fallback Templates**
- OpenAI Free Trial: $5 credit (500-1000 messages)
- After trial: Template-based generation (free)

**Hybrid Approach:**
```python
# Try OpenAI, fallback to templates
def generate_message(opportunity):
    try:
        # OpenAI GPT-3.5-turbo (cheapest)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except:
        # Fallback to template
        return f"""Hi {customer_name},

With the upcoming {event_name} on {event_date}, we anticipate a {surge_pct}% increase in oil demand at your location.

We'd like to discuss a proactive delivery to ensure you're fully stocked.

Best,
US Oil Solutions Team"""
```

**Cost:** ~$0/month (free templates) or ~$5-10/month (OpenAI)

---

### Phase 5: Proximity Calculations (FREE)

**Solution: Haversine Distance (Pure Math)**
```python
from math import radians, cos, sin, asin, sqrt

def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate distance between two points (km)"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    
    return km

def proximity_multiplier(distance_km):
    """Event impact based on distance"""
    if distance_km < 0.5: return 2.5    # 500m: MAX
    if distance_km < 1.0: return 2.0    # 1km: HIGH
    if distance_km < 2.0: return 1.5    # 2km: MEDIUM
    if distance_km < 5.0: return 1.2    # 5km: LOW
    return 1.0                           # 5km+: NONE
```

**Cost:** $0/month (pure math)

---

## Implementation Order

### Week 1: Foundation
1. ✅ Add lat/lng columns to BigQuery tables
2. ✅ Run free geocoding script (Nominatim)
3. ✅ Verify geocoding accuracy (spot check 10 locations)
4. ✅ Create proximity calculation functions

### Week 2: Event Intelligence
5. ✅ Build event scraper (Vegas.com + LVCVA)
6. ✅ Create vegas_events table
7. ✅ Set up daily scraping schedule (Cloud Scheduler)
8. ✅ Build event-restaurant matching logic

### Week 3: Mapping & Scoring
9. ✅ Implement Leaflet.js heat map
10. ✅ Build proximity-based scoring system
11. ✅ Create opportunity score calculations
12. ✅ Add detailed analysis bullets

### Week 4: AI & Polish
13. ✅ Integrate AI message generation (hybrid approach)
14. ✅ Build enhanced opportunity cards
15. ✅ End-to-end testing
16. ✅ Deploy to production

---

## Cost Summary (FREE APPROACH)

| Component | Solution | Monthly Cost |
|-----------|----------|--------------|
| Geocoding | Nominatim (OSM) | $0 |
| Event Data | Web Scraping | $0 |
| Mapping | Leaflet + OSM | $0 |
| Proximity Math | Haversine | $0 |
| AI Messages | Templates (+ optional OpenAI) | $0-10 |
| **TOTAL** | | **$0-10/month** |

**vs. Paid Approach:** $72-152/month savings

---

## Next Steps

1. ✅ Review this audit
2. ✅ Get approval for free solutions
3. ✅ Start with geocoding (3.5 minutes runtime)
4. ✅ Build event scraper (1 day)
5. ✅ Implement heat map (1 day)
6. ✅ Complete full implementation

---

**Audit Completed:** November 5, 2025  
**Ready to Proceed:** YES  
**Estimated Completion:** 4 weeks  
**Total Cost:** $0/month (100% free)







