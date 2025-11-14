# Vegas Intel Page - START HERE
**Quick Reference Guide**  
**Last Updated:** November 5, 2025  
**Status:** ✅ PRODUCTION READY - Real Fryer Math Operational

---

## 🎯 Quick Status

**Vegas Intel Page:** ✅ COMPLETE & READY FOR DEPLOYMENT  
**Data Source:** Glide API (READ ONLY, 5,628 rows)  
**Calculations:** Real Fryer Math (408 fryers, 151 restaurants)  
**Revenue Potential:** $62,845 (calculated from real data)  
**Build Status:** ✅ SUCCESS (Next.js 15.5.6, 0 errors)

---

## 🚨 CRITICAL: GLIDE IS READ ONLY

**DO NOT TOUCH GLIDE - READ ONLY ACCESS ONLY**
- Glide = US Oil Solutions production system
- Our access = READ ONLY (query only)
- Data flows ONE WAY: Glide → BigQuery → Dashboard
- NEVER write to Glide under any circumstances

---

## 📁 Documentation Files (In Order of Importance)

**Start with these:**

1. **`00_START_HERE.md`** (this file) - Quick reference
2. **`IMPLEMENTATION_COMPLETE.md`** - Complete implementation summary with real fryer math examples
3. **`VEGAS_PAGE_STATUS.md`** - Current operational status

**Technical References:**

4. **`VEGAS_GLIDE_API_REFERENCE.md`** - All 8 APIs documented (LOCKED configuration)
5. **`VEGAS_DATA_SYNTHESIS_PLAN.md`** - How real data maps to forecasting model
6. **`GLIDE_DATA_SCHEMA_ANALYSIS.md`** - Column mappings and data dictionary

**Supporting Docs:**

7. **`HANDOFF_VEGAS_GLIDE_INTEGRATION_NOV5.md`** - Initial deployment guide
8. **`VEGAS_INTEL_SALES_PAGE_ARCHITECTURE.md`** - Original page design plan
9. **`README.md`** - Documentation index

---

## 🎉 What's Working Right Now

### Real Fryer Math (From Glide Data)

**Formula Implemented:**
```
BASE_WEEKLY_GALLONS = (capacity_lbs × 4 TPM) / 7.6 lbs/gal
EVENT_SURGE = BASE_WEEKLY × (event_days / 7) × multiplier
UPSELL_GALLONS = EVENT_SURGE × upsell_%
REVENUE = UPSELL_GALLONS × price/gal
```

**Example (Real Data):**
- Buffet: 8 fryers, 549 lbs capacity → 289 gal/week baseline
- Event surge (3 days, 2.0x): 248 gallons
- Upsell (68%): 169 gallons
- Revenue ($8.20/gal): **$1,384**

### All 5 Dashboard Components

1. **SalesIntelligenceOverview** - 151 customers, $62,845 revenue potential
2. **EventDrivenUpsell** - Top 20 opportunities (real fryer math)
3. **CustomerRelationshipMatrix** - Scored by fryer count (85/70/50/30)
4. **EventVolumeMultipliers** - Casino surge forecasts (1.3x - 3.4x)
5. **MarginProtectionAlerts** - Volume-based risk alerts

### All 5 API Routes

- `/api/v4/vegas/metrics` ✅
- `/api/v4/vegas/customers` ✅
- `/api/v4/vegas/events` ✅
- `/api/v4/vegas/upsell-opportunities` ✅
- `/api/v4/vegas/margin-alerts` ✅

All routes use REAL fryer data with smart defaults for Kevin to override.

---

## 🚀 Ready to Deploy

### Deploy Command

```bash
cd /Users/zincdigital/CBI-V14/dashboard-nextjs
vercel --prod
```

### Test Live Page

Visit: `https://cbi-dashboard.vercel.app/vegas`

**You should see:**
- 151 total customers
- $62,845 estimated revenue potential (real calculation!)
- Real restaurant names (Gordon Ramsay Pub, Buffet, etc.)
- Real fryer counts (1-8 fryers per restaurant)
- Revenue opportunities ranked by real fryer math

---

## 📊 Real Data Loaded (From Glide READ ONLY)

| Table | Rows | Purpose |
|-------|------|---------|
| vegas_restaurants | 151 | Restaurant master data |
| vegas_fryers | 421 | **Fryer capacity (FOUNDATION)** |
| vegas_casinos | 31 | Casino locations |
| vegas_export_list | 3,176 | Customer targeting |
| vegas_scheduled_reports | 28 | Performance data |
| vegas_shifts | 148 | Delivery schedules |
| vegas_shift_casinos | 440 | Casino shifts |
| vegas_shift_restaurants | 1,233 | Restaurant shifts |

**Total:** 5,628 rows (READ ONLY copy from Glide)

---

## 🔧 What Kevin Can Override

According to the architecture plan, Kevin has full control over:

- ✅ Event duration (default: 3 days)
- ✅ Event multiplier (default: 2.0x, range: 1.0-3.4x)
- ✅ Upsell % (default: 68%, range: 40-90%)
- ✅ Price/gal (default: $8.20)
- ✅ Tanker cost (default: $1,200)
- ✅ Labor cost (default: $180)
- ✅ Delivery cost (default: $0.45/gal)
- ✅ TPM - Turns Per Month (default: 4)

**Locked (From Dashboard):**
- 🔒 ZL Cost: $7.50/gal (from soybean oil forecast)

**Kevin's Workflow:**
1. See AI suggestions (based on real fryer math)
2. Edit any assumption
3. ROI recalculates live
4. Save scenario if profitable
5. Execute or adjust

---

## 💡 Real Example (From Current Data)

### Scenario: Buffet (8 Fryers)

**Real Fryer Data:**
- Fryer count: 8
- Total capacity: 549.61 lbs
- Weekly baseline: 289 gallons/week

**AI Calculation (Default Assumptions):**
- Event surge (3 days, 2.0x): 248 gallons
- Upsell (68%): 169 gallons
- Revenue ($8.20/gal): $1,386
- COGS ($7.50/gal): $1,268
- Delivery: $180
- **ROI: 0.96x** (BELOW 1.0 - NOT PROFITABLE)

**Kevin's Override:**
- Price: $8.20 → **$9.00** (Kevin edits)
- ROI: 0.96x → **1.05x** ✅ (NOW PROFITABLE)
- Margin: -4.5% → **+4.9%** ✅

**Kevin Saves:** "Buffet Premium Pricing" → Scenario Library

**Next Event:** Kevin loads "Buffet Premium Pricing" → All his edits restored → Execute

---

## 🎊 Summary

**VEGAS INTEL PAGE IS PRODUCTION READY**

✅ Real fryer math from 408 fryers  
✅ 151 restaurants with real names  
✅ $62,845 total revenue opportunity  
✅ Smart defaults + Kevin full control  
✅ 5 components operational  
✅ 5 API routes with real calculations  
✅ Production build successful  
✅ READ ONLY from Glide (safe)  

**Next Action:** Deploy to Vercel and test

---

## 🔗 Quick Links

**Run Ingestion (Refresh Data from Glide READ ONLY):**
```bash
cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion
python3 ingest_glide_vegas_data.py
```

**Verify Data:**
```bash
bq ls cbi-v14:forecasting_data_warehouse | grep vegas_
```

**Deploy:**
```bash
cd /Users/zincdigital/CBI-V14/dashboard-nextjs
vercel --prod
```

---

**📍 You are here:** Ready for deployment  
**📊 Data:** Real fryer math operational  
**🚀 Status:** PRODUCTION READY  
**🚨 Remember:** GLIDE IS READ ONLY







