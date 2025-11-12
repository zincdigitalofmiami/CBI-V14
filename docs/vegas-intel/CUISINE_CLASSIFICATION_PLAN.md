# Vegas Intel - Cuisine Classification Implementation Plan
**Date:** November 5, 2025  
**Status:** 🎯 SYSTEMATIC CLASSIFICATION REQUIRED  
**Total Restaurants:** 142 open locations (ALL must be classified)

---

## 🚨 USER REQUIREMENT: CLASSIFY ALL 142 RESTAURANTS

**Critical Requirements:**
- Research and classify EVERY SINGLE restaurant (not just major ones)
- Parse restaurant names for cuisine indicators
- Research online for each restaurant when name is ambiguous
- Cannot get this wrong - directly affects revenue forecasting
- Each cuisine type has specific oil consumption multiplier

---

## Oil Consumption Multipliers (From Architecture)

### From Original Architecture Plan:
- **Club / Pool:** 1.8×
- **Steakhouse:** 1.2×
- **Bakery:** 0.6×
- **Dump & Refill:** 2.0×
- **Italian:** 1.5×
- **Chinese:** 1.4×
- **Sushi:** 0.3×

### Additional Multipliers Needed (Based on Restaurant Analysis):
- **Buffet:** 2.2× (HIGHEST - all cuisines, constant frying)
- **Fried Chicken Specialist:** 2.0× (primary protein fried)
- **Wings Specialist:** 2.0× (wings are main item)
- **Cajun / Creole:** 1.9× (heavy fried seafood)
- **Pub / Bar Food:** 1.7× (wings, fish & chips, apps)
- **Seafood / Fish & Chips:** 1.7× (fried fish, calamari)
- **BBQ:** 1.7× (fried sides, apps)
- **American Comfort:** 1.7× (heavy fried portions)
- **Burgers:** 1.6× (burgers + fries + apps)
- **Snack Bar:** 1.6× (bar food, fried items)
- **Arena Concessions:** 1.6× (hot dogs, fries, nachos)
- **American Diner:** 1.5× (standard American, moderate frying)
- **Cuban / Caribbean:** 1.5× (tostones, plantains, croquetas)
- **Banquet:** 1.5× (varied menu, moderate volume)
- **Production Kitchen:** 1.5× (high volume, varied)
- **Contemporary American:** 1.5× (modern American)
- **American Casual:** 1.5× (casual dining)
- **American Tavern:** 1.5× (tavern food)
- **Asian Fusion:** 1.4× (stir-fry heavy)
- **Japanese Yakitori:** 1.4× (includes karaage/fried)
- **Employee Dining:** 1.4× (cafeteria - varied)
- **Cheesesteak:** 1.4× (fries + fried toppings)
- **Club House / Golf:** 1.4× (American casual)
- **Mexican:** 1.3× (chips, some fried items)
- **French Bistro / Brasserie:** 1.3× (frites, moderate)
- **Deli:** 1.3× (sandwiches, some fried sides)
- **American Upscale:** 1.3× (refined but still apps)
- **Hotel Dining / Room Service:** 1.3× (varied menu)
- **Cafe:** 1.2× (light fare, minimal frying)
- **Pizza:** 1.1× (mostly pizza, minimal frying)

---

## Systematic Classification Approach

### Step 1: Parse Restaurant Names for Clear Indicators

**Obvious Cuisine Indicators in Names:**
- "Steakhouse" → Steakhouse (1.2×)
- "Buffet" → Buffet (2.2×)
- "Noodle" / "Noodles" → Chinese (1.4×)
- "Fish & Chips" → Fish & Chips (1.7×)
- "Burger" / "Burgr" → Burgers (1.6×)
- "Pool" → Pool/Club (1.8×)
- "Pub" → Pub (1.7×)
- "Pizza" → Pizza (1.1×)
- "Cafe" / "Cafeteria" → Cafe (1.2×)
- "EDR" / "Employee Dining" → Employee Dining (1.4×)
- "Banquet" / "Banquets" → Banquet (1.5×)
- "Kitchen" (Main/Production/Service) → Production Kitchen (1.5×)
- "Cheesesteak" → Cheesesteak (1.4×)
- "Bakery" / "Pastry" → Bakery (0.6×)
- "Bistro" → French Bistro (1.3×)
- "Brasserie" → French Brasserie (1.3×)
- "Deli" → Deli (1.3×)
- "BBQ" / "Barbecue" / "Smokey" → BBQ (1.7×)
- "Wing" / "Wings" → Wings (2.0×)
- "Chicken" (in name) → Fried Chicken (2.0×) or Burgers (1.6×)

### Step 2: Research Celebrity Chef Restaurants

**Gordon Ramsay Concepts:**
- Hell's Kitchen → Contemporary American (1.5×)
- Gordon Ramsay Steakhouse → Steakhouse (1.2×)
- Gordon Ramsay Pub → Pub (1.7×)
- Gordon Ramsay Burgr → Burgers (1.6×)

**Guy Fieri Concepts:**
- Flavortown → American Comfort (1.8×)
- Chicken Guy → Fried Chicken (2.0×)
- Guy Fieri → American Comfort (1.8×)

**Other Celebrity:**
- Giada → Italian (1.5×)
- Nobu → Sushi (0.3×)
- Bobby's Burger (Bobby Flay) → Burgers (1.6×)
- Bazaar Mar (José Andrés) → Spanish Seafood (1.7×)
- Martha Stewart - Bedford → American Upscale (1.3×)
- Vanderpump (Lisa Vanderpump) → American Upscale (1.3×)
- Dominique Ansel → French Bakery (0.6×)

### Step 3: Classify Based on Geographic/Cultural Names

**Italian Names:**
- Amalfi → Italian (1.5×)
- Giada → Italian (1.5×)
- Superfrico → Italian (1.5×)
- Caramello → Italian Bakery (0.6×)

**Chinese/Asian Names:**
- Beijing Noodle → Chinese (1.4×)
- California Noodle House → Chinese (1.4×)
- Wuhu Noodle → Chinese (1.4×)
- Tomo Noodles → Chinese (1.4×)
- Mok Bar → Asian Fusion (1.4×)
- Ondori → Japanese Yakitori (1.4×)

**Mexican Names:**
- El Burro Borracho → Mexican (1.3×)
- Gonzalez y Gonzalez → Mexican (1.3×)
- Mi Casa → Mexican (1.3×)
- Su Casa → Mexican (1.3×)
- Tortazo → Mexican (1.3×)

**Cuban:**
- Havana 1957 → Cuban (1.5×)

**French:**
- Brasserie B → French Brasserie (1.3×)
- Bistro 57 → French Bistro (1.3×)

**Spanish:**
- Bazaar Mar → Spanish Seafood (1.7×)

**Cajun:**
- Darla's Southern Cajun Bistro → Cajun (1.9×)

### Step 4: Classify Remaining Ambiguous Names

**Need Individual Research:**
- Lanai Express → Hawaiian/Asian? Need research
- MRKT → Modern American/Asian Fusion? Need research
- Mermaid - Zone 4 → Asian? Need research
- Hash House A Go-Go → American Comfort (known LV restaurant)
- Jason Aldean's Kitchen + Bar → American Casual (country theme)
- Smokey Joe's → BBQ (name indicates)
- Tony Roma's → BBQ Ribs (known chain)
- Yolo - Independent → Need research

---

## Implementation Steps

### Step 1: Complete Classification (IN PROGRESS)
- [ ] Get all 142 restaurants with IDs
- [ ] Classify by name patterns (80% done)
- [ ] Research ambiguous names (10 restaurants)
- [ ] Verify all celebrity chef concepts
- [ ] Double-check multiplier assignments

### Step 2: Create BigQuery Table
```sql
CREATE TABLE \`cbi-v14.forecasting_data_warehouse.vegas_cuisine_multipliers\`
(
  glide_rowID STRING,
  restaurant_name STRING,
  cuisine_type STRING,
  oil_multiplier FLOAT64,
  classification_source STRING,
  created_at TIMESTAMP
);
```

### Step 3: Update API Routes with Cuisine Multipliers
```sql
WITH restaurant_capacity_with_cuisine AS (
  SELECT 
    r.glide_rowID,
    r.MHXYO as restaurant_name,
    COUNT(f.glide_rowID) as fryer_count,
    SUM(f.xhrM0) as total_capacity_lbs,
    c.cuisine_type,
    c.oil_multiplier,
    -- Apply cuisine multiplier to base calculation
    ROUND((SUM(f.xhrM0) * 4) / 7.6 * c.oil_multiplier, 2) as adjusted_weekly_gallons
  FROM vegas_restaurants r
  LEFT JOIN vegas_fryers f ON r.glide_rowID = f.`2uBBn`
  LEFT JOIN vegas_cuisine_multipliers c ON r.glide_rowID = c.glide_rowID
  WHERE r.s8tNr = 'Open'
  GROUP BY r.glide_rowID, r.MHXYO, c.cuisine_type, c.oil_multiplier
)
SELECT * FROM restaurant_capacity_with_cuisine;
```

---

## Status: NEED TO COMPLETE ALL 142 CLASSIFICATIONS

**Progress:**
- ✅ Identified 142 open restaurants
- ✅ Created oil multiplier system (22 cuisine types)
- 🔄 Classified ~120 restaurants (85%)
- ⏳ Need to classify remaining ~22 restaurants
- ⏳ Need to verify all classifications
- ⏳ Need to create BigQuery table
- ⏳ Need to update API routes with cuisine multipliers

**Blocking Issue:**
- Must complete classification of ALL 142 restaurants before implementing
- Cannot proceed with partial data - user was emphatic about this
- Need individual research for ambiguous restaurant names

---

## Next Action Required

I need to:
1. Get complete list of all 142 restaurants with IDs
2. Go through EACH ONE systematically
3. Research any ambiguous names online
4. Complete the classification table
5. Load into BigQuery
6. Update API routes

**This is a critical dependency for accurate forecasting math.**

---

**Status:** Classification 85% complete - need to finish remaining 22 restaurants before proceeding







