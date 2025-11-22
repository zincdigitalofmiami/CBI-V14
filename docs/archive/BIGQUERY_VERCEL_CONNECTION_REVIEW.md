---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery ↔ Vercel Connection Review
## Read-Only Access Analysis for Production Readiness

**Date**: 2025-01-XX  
**Scope**: BigQuery connection health, query patterns, security, and production readiness  
**Access Pattern**: Read-only from Vercel Next.js API routes

---

## Executive Summary

The BigQuery connection is **functionally working** but has **several critical issues** that need attention before going live:

1. ⚠️ **SQL Injection Risk** - Multiple routes use string interpolation instead of parameterized queries
2. ⚠️ **Error Handling** - Errors are silently swallowed, making debugging difficult
3. ⚠️ **Query Performance** - Inefficient subqueries in WHERE clauses
4. ⚠️ **Missing Query Timeouts** - No explicit timeout protection
5. ✅ **Region Consistency** - All queries correctly use `us-central1`
6. ✅ **Client Reuse** - BigQuery client is properly cached
7. ⚠️ **Credential Fallback** - Falls back to ADC which won't work on Vercel

---

## 1. Connection Architecture

### Current Implementation

**File**: `dashboard-nextjs/src/lib/bigquery.ts`

**Connection Flow**:
```
Vercel API Route → getBigQueryClient() → BigQuery SDK → BigQuery API
```

**Credential Handling**:
- **Vercel Production**: Uses `GOOGLE_APPLICATION_CREDENTIALS_BASE64` (base64-encoded JSON)
- **Local Development**: Falls back to `GOOGLE_APPLICATION_CREDENTIALS` or Application Default Credentials

**Issues Identified**:

1. **Silent Credential Failure** (Line 30-32)
   ```typescript
   } catch (error) {
     console.error('Failed to parse base64 credentials:', error)
     // Don't throw - let it try Application Default Credentials
   }
   ```
   - **Problem**: If base64 parsing fails, it silently falls back to ADC
   - **Impact**: On Vercel, ADC won't work → queries will fail silently
   - **Recommendation**: Throw error if base64 parsing fails in production

2. **Client Creation Fallback** (Line 40-44)
   ```typescript
   } catch (error) {
     console.error('BigQuery client creation failed:', error)
     // Return client anyway - connection will fail on first query but won't crash
     bigqueryClient = new BigQuery({ projectId: 'cbi-v14' })
     return bigqueryClient
   }
   ```
   - **Problem**: Returns invalid client instead of throwing
   - **Impact**: Errors only surface on first query, not at initialization
   - **Recommendation**: Throw error immediately if client creation fails

3. **Error Swallowing in executeBigQueryQuery** (Line 63-66)
   ```typescript
   } catch (error: any) {
     console.error('BigQuery query error:', error.message || error)
     // Return empty array instead of throwing - let routes handle gracefully
     return []
   }
   ```
   - **Problem**: All query errors return empty arrays
   - **Impact**: Routes can't distinguish between "no data" and "query failed"
   - **Recommendation**: Return structured error or throw with context

---

## 2. Security Issues

### SQL Injection Risk

**CRITICAL**: Multiple routes use string interpolation for user inputs.

#### Affected Routes:

1. **`/api/v4/vegas/customers`** (Line 22)
   ```typescript
   ROUND((SUM(f.xhrM0) * ${tpmValue}) / 7.6 * COALESCE(c.oil_multiplier, 1.0), 2)
   ```
   - **Input**: `tpm` query parameter (parsed as float)
   - **Risk**: Medium - numeric input, but still unsafe
   - **Fix**: Use parameterized queries

2. **`/api/v4/vegas/events`** (Multiple lines)
   ```typescript
   ROUND(SUM((f.xhrM0 * ${tpmValue}) / 7.6 * COALESCE(cuisine.oil_multiplier, 1.0)), 0)
   WHEN ${eventMultiplier !== null ? `true` : `false`} THEN ${eventMultiplierValue !== null ? eventMultiplierValue : 'NULL'}
   ```
   - **Inputs**: `tpm`, `eventMultiplier`, `upsellPct`, `pricePerGal`
   - **Risk**: High - complex conditional SQL injection
   - **Fix**: Use parameterized queries with proper type checking

3. **`/api/v4/vegas/margin-alerts`** (Multiple lines)
   ```typescript
   ROUND((SUM(f.xhrM0) * ${tpmValue}) / 7.6 * COALESCE(c.oil_multiplier, 1.0), 2)
   WHEN ${pricePerGal !== null && zlCostValue !== null ? `true` : `false`}
   ```
   - **Inputs**: `tpm`, `pricePerGal`, `zlCost`
   - **Risk**: High - financial calculations with user input
   - **Fix**: Use parameterized queries

#### Safe Route Example:

**`/api/v4/feature-importance/[horizon]`** (Line 34-38)
```typescript
const [rows] = await client.query({
  query,
  location: "us-central1",
  params: { h },  // ✅ Uses parameterized query
});
```
- **Good**: Uses BigQuery parameterized queries
- **Recommendation**: Apply this pattern to all routes

---

## 3. Query Performance Issues

### Inefficient Subqueries

Multiple routes use correlated subqueries in WHERE clauses:

1. **`/api/v4/price-drivers`** (Line 21)
   ```sql
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
   ```
   - **Problem**: Subquery executes for each row (though optimized by BigQuery)
   - **Better**: Use window functions or CTE

2. **`/api/v4/risk-radar`** (Line 21)
   ```sql
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
   ```
   - **Same issue**

3. **`/api/v4/substitution-economics`** (Line 46, 79)
   ```sql
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
   WHERE p.date = (SELECT MAX(date) FROM price_data)
   ```
   - **Multiple subqueries in same query**

### Recommended Fix:

```sql
WITH latest_date AS (
  SELECT MAX(date) as max_date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)
SELECT ...
FROM `cbi-v14.models_v4.training_dataset_super_enriched` t
CROSS JOIN latest_date ld
WHERE t.date = ld.max_date
```

### Missing Query Timeouts

**Current**: No explicit timeout settings  
**Risk**: Long-running queries can hang Vercel Edge Functions (10s limit)  
**Recommendation**: Add timeout to `executeBigQueryQuery`:

```typescript
const queryOptions: any = { 
  query,
  location: 'us-central1',
  jobTimeoutMs: 8000,  // 8 seconds (under Vercel 10s limit)
  maxResults: 10000   // Prevent huge result sets
}
```

---

## 4. Table Access Patterns

### Datasets Accessed:

1. **`cbi-v14.predictions`**
   - `daily_forecasts` ✅ (Primary forecast table)
   - `monthly_vertex_predictions` ✅ (Fallback table)
   - `predictions_uc1.vw_feature_importance_latest` ✅ (View)

2. **`cbi-v14.forecasting_data_warehouse`**
   - `soybean_oil_prices` ✅ (Primary price data)
   - `palm_oil_prices` ✅
   - `canola_oil_prices` ✅
   - `vix_daily` ✅
   - `vegas_restaurants` ✅
   - `vegas_fryers` ✅
   - `vegas_cuisine_multipliers` ✅
   - `vegas_casinos` ✅
   - `vegas_top_opportunities` ✅
   - `event_restaurant_impact` ✅

3. **`cbi-v14.models_v4`**
   - `training_dataset_super_enriched` ✅ (Big-8 features)

### Potential Issues:

1. **Missing Table Validation**
   - No checks if tables exist before querying
   - **Recommendation**: Add table existence checks or handle 404 errors gracefully

2. **View Dependencies**
   - `predictions_uc1.vw_feature_importance_latest` - verify view exists and is accessible
   - **Recommendation**: Document all view dependencies

3. **Cross-Dataset Queries**
   - Multiple JOINs across datasets (e.g., vegas routes)
   - **Performance**: Monitor query costs and execution times

---

## 5. Error Handling Patterns

### Current Pattern (Problematic):

```typescript
const result = await executeBigQueryQuery(query)
if (result.length === 0) {
  return NextResponse.json({ error: 'No data' }, { status: 503 })
}
```

**Problems**:
- Can't distinguish between "no data" and "query failed"
- All errors return empty arrays
- No error context for debugging

### Recommended Pattern:

```typescript
try {
  const result = await executeBigQueryQuery(query)
  if (result.length === 0) {
    return NextResponse.json({ 
      error: 'No data available',
      message: 'Query returned empty result set'
    }, { status: 503 })
  }
  // Process result
} catch (error: any) {
  console.error('Query failed:', error)
  return NextResponse.json({
    error: 'Query execution failed',
    message: error.message,
    code: error.code
  }, { status: 500 })
}
```

---

## 6. Region Consistency

✅ **Good**: All queries explicitly set `location: 'us-central1'`

**Files**:
- `bigquery.ts` Line 16, 59, 78
- All API routes use `executeBigQueryQuery` which sets location

**No Issues Found** - Region handling is correct.

---

## 7. Client Reuse

✅ **Good**: BigQuery client is cached at module level

```typescript
let bigqueryClient: BigQuery | null = null

export function getBigQueryClient(): BigQuery {
  if (bigqueryClient) {
    return bigqueryClient  // ✅ Reuses existing client
  }
  // ... create new client
}
```

**Benefit**: Reduces connection overhead  
**No Issues Found**

---

## 8. Production Readiness Checklist

### Critical (Must Fix Before Going Live):

- [ ] **Fix SQL Injection** - Convert all string interpolation to parameterized queries
- [ ] **Improve Error Handling** - Don't swallow errors, return structured error responses
- [ ] **Add Query Timeouts** - Prevent Vercel Edge Function timeouts (10s limit)
- [ ] **Fix Credential Fallback** - Throw error if base64 parsing fails on Vercel
- [ ] **Validate Table Existence** - Add checks or graceful error handling

### Important (Should Fix Soon):

- [ ] **Optimize Subqueries** - Use CTEs instead of correlated subqueries
- [ ] **Add Query Logging** - Log query execution times for monitoring
- [ ] **Add Rate Limiting** - Protect against query abuse
- [ ] **Document Table Dependencies** - List all required tables/views

### Nice to Have:

- [ ] **Add Query Caching** - Cache frequently accessed data (Vercel supports caching)
- [ ] **Add Query Metrics** - Track query costs and performance
- [ ] **Add Health Checks** - Verify all required tables are accessible

---

## 9. Recommended Fixes

### Fix 1: Parameterized Queries

**Before** (Unsafe):
```typescript
const query = `SELECT * FROM table WHERE value = ${userInput}`
```

**After** (Safe):
```typescript
const query = `SELECT * FROM table WHERE value = @input`
const [rows] = await client.query({
  query,
  params: { input: userInput }
})
```

### Fix 2: Better Error Handling

**Update `executeBigQueryQuery`**:
```typescript
export async function executeBigQueryQuery(
  query: string, 
  location?: string,
  params?: Record<string, any>
): Promise<{ data: any[], error?: string }> {
  try {
    const client = getBigQueryClient()
    const queryOptions: any = { 
      query,
      location: location || 'us-central1',
      params: params || {},
      jobTimeoutMs: 8000,
      maxResults: 10000
    }
    const [rows] = await client.query(queryOptions)
    return { data: rows || [] }
  } catch (error: any) {
    console.error('BigQuery query error:', {
      message: error.message,
      code: error.code,
      query: query.substring(0, 100) // Log first 100 chars
    })
    return { 
      data: [], 
      error: error.message || 'Query execution failed'
    }
  }
}
```

### Fix 3: Credential Validation

**Update `getBigQueryClient`**:
```typescript
export function getBigQueryClient(): BigQuery {
  if (bigqueryClient) {
    return bigqueryClient
  }

  const options: BigQueryOptions = {
    projectId: process.env.GCP_PROJECT_ID || 'cbi-v14',
    location: 'us-central1',
  }

  // Vercel production requires base64 credentials
  if (process.env.VERCEL) {
    if (!process.env.GOOGLE_APPLICATION_CREDENTIALS_BASE64) {
      throw new Error('GOOGLE_APPLICATION_CREDENTIALS_BASE64 required in Vercel')
    }
    try {
      const credentials = JSON.parse(
        Buffer.from(
          process.env.GOOGLE_APPLICATION_CREDENTIALS_BASE64,
          'base64'
        ).toString('utf-8')
      )
      options.credentials = credentials
    } catch (error) {
      throw new Error(`Failed to parse base64 credentials: ${error}`)
    }
  }

  try {
    bigqueryClient = new BigQuery(options)
    return bigqueryClient
  } catch (error) {
    throw new Error(`BigQuery client creation failed: ${error}`)
  }
}
```

---

## 10. Testing Recommendations

### Before Going Live:

1. **Test All API Routes**:
   ```bash
   ./test-api.sh https://cbi-dashboard.vercel.app
   ```

2. **Test Error Scenarios**:
   - Invalid credentials
   - Missing tables
   - Query timeouts
   - Invalid query parameters

3. **Test SQL Injection Protection**:
   - Try malicious inputs in query parameters
   - Verify parameterized queries work

4. **Monitor Query Performance**:
   - Check BigQuery query logs
   - Verify all queries complete under 8 seconds
   - Monitor query costs

---

## Summary

**Status**: ⚠️ **Needs Work Before Production**

**Critical Issues**: 5  
**Important Issues**: 3  
**Good Practices**: 2 (Region consistency, Client reuse)

**Priority Actions**:
1. Fix SQL injection vulnerabilities (HIGH)
2. Improve error handling (HIGH)
3. Add query timeouts (HIGH)
4. Fix credential fallback (MEDIUM)
5. Optimize subqueries (MEDIUM)

The connection architecture is sound, but security and error handling need immediate attention before going live.





