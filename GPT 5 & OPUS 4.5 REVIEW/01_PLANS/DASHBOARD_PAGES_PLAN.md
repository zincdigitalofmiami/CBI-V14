---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

**📋 BEST PRACTICES:** See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices including: no fake data, always check before creating, always audit after work, us-central1 only, no costly resources without approval, research best practices, research quant finance modeling.

# Dashboard & Pages Plan
**Project:** CBI-V14  
**Purpose:** Dashboard UI/UX and page structure planning  
**Status:** Active

---

## Dashboard Overview

### Purpose
Business intelligence dashboard for ZL (Soybean Oil) futures procurement decisions with private MES (Micro E-mini S&P 500) analytics page.

### Technology Stack
- **Frontend:** Next.js + React
- **Backend:** FastAPI (Python)
- **Database:** BigQuery
- **Hosting:** Vercel (frontend) + Cloud Run (API)
- **Auth:** Firebase Auth / Google Identity

---

## Page Structure

### 1. Dashboard (Home) `/`
**Purpose:** Daily procurement decisions for ZL futures

**Components:**
- Current ZL price & 24h change
- 7-day forecast (price + confidence intervals)
- Buy/Hold/Wait signal with reasoning
- Key drivers today (SHAP top 5)
- Regime indicator (Bull/Bear/Crisis)
- Performance metrics (MAPE, Sharpe)

**Data Sources:**
- `api.vw_dashboard_current_state`
- `predictions.daily_forecasts`
- `monitoring.model_performance`

### 2. Sentiment `/sentiment`
**Purpose:** Market mood and news intelligence

**Components:**
- News sentiment timeline (30 days)
- Trump policy tracker
- USDA report calendar
- China import trends
- Social media sentiment (Reddit/Twitter)
- Breaking news alerts

**Data Sources:**
- `raw_intelligence.news_sentiments`
- `market_data.social_intelligence`
- `market_data.policy_events`

### 3. Strategy `/strategy`
**Purpose:** Business intelligence and procurement strategy

**Components:**
- Calendar spread opportunities (ZL contracts)
- Crush margin analysis (ZL/ZS/ZM)
- Biofuel demand forecasts
- China import projections
- Optimal purchase timing
- Risk metrics (VaR, volatility)

**Data Sources:**
- `market_data.calendar_spreads`
- `market_data.crush_margins`
- `features.biofuel_policy`
- `market_data.china_imports`

### 4. Trade Intelligence `/trade`
**Purpose:** Geopolitical risk and trade policy

**Components:**
- Trump tariff tracker
- USMCA impact analysis
- Argentina crisis monitor
- Brazil harvest status
- Shipping costs (Baltic Dry Index)
- Currency impact (USD/CNY, USD/BRL)

**Data Sources:**
- `market_data.policy_events`
- `market_data.trade_intelligence`
- `market_data.shipping_logistics`
- `market_data.currency_data`

### 5. MES Private `/mes` 🔒
**Purpose:** Private micro E-mini S&P 500 analytics (HIDDEN PAGE)

**Access Control:**
- Restricted to: kirkmusick@gmail.com only
- BigQuery Row-Level Security enforced
- Not discoverable in navigation
- Direct URL access only

**Components:**
- MES price & 24h change
- Volume Profile (POC, VAH, VAL)
- Pivot Points (Daily/Weekly/Monthly)
- Fibonacci levels
- MS-EGARCH volatility forecast
- VIX correlation
- Fed/FOMC impact analysis
- Regime probabilities (Bull/Bear/Crash)

**Data Sources:**
- `api.vw_mes_private`
- `features.mes_volume_profile`
- `features.mes_pivots`
- `features.mes_fibonacci`
- `features.mes_garch_vol`
- `features.mes_ms_egarch_vol`

---

## UI/UX Guidelines

### Design Principles
1. **Data-First:** Numbers and charts, minimal decoration
2. **Mobile-Responsive:** Works on phone, tablet, desktop
3. **Fast Load:** <2 seconds to interactive
4. **Real-Time:** WebSocket updates for breaking news
5. **Professional:** Clean, Bloomberg-style aesthetic

### Visual Style
- **Color Scheme:** Dark mode primary (navy/charcoal)
- **Accent Colors:** 
  - Green for bullish/buy signals
  - Red for bearish/sell signals
  - Yellow for warnings/alerts
- **Typography:** 
  - Headers: Inter, 700 weight
  - Body: Inter, 400 weight
  - Code/Numbers: JetBrains Mono
- **Charts:** Lightweight (Chart.js or Recharts)

### Components Library
- **Cards:** Shadow, rounded corners, padding
- **Tables:** Sortable, filterable, pagination
- **Charts:** Line, bar, candlestick, scatter
- **Alerts:** Toast notifications for breaking news
- **Loading:** Skeleton loaders, spinners

---

## API Endpoints

### Public ZL Endpoints
```
GET  /api/v1/dashboard/current     # Current state
GET  /api/v1/dashboard/forecast    # 7-day forecast
GET  /api/v1/sentiment/news        # Recent news
GET  /api/v1/strategy/spreads      # Calendar spreads
GET  /api/v1/trade/policy          # Trade policy events
```

### Private MES Endpoints (Auth Required)
```
GET  /api/v1/mes/current           # MES current state
GET  /api/v1/mes/volume-profile    # Volume Profile
GET  /api/v1/mes/pivots            # Pivot Points
GET  /api/v1/mes/fibonacci         # Fibonacci levels
GET  /api/v1/mes/volatility        # MS-EGARCH forecast
```

---

## Implementation Phases

### Phase 1: ZL Dashboard (Current)
- [x] Basic dashboard layout
- [x] ZL price display
- [x] Forecast visualization
- [ ] Sentiment page
- [ ] Strategy page
- [ ] Trade Intelligence page

### Phase 2: MES Integration
- [ ] MES private page
- [ ] Volume Profile charts
- [ ] Pivot Points display
- [ ] Fibonacci visualization
- [ ] MS-EGARCH volatility forecast
- [ ] Access control implementation

### Phase 3: Polish & Features
- [ ] Real-time WebSocket updates
- [ ] Mobile optimization
- [ ] Performance optimization
- [ ] Error handling & logging
- [ ] User preferences/settings

---

## Security & Access Control

### ZL Pages (Public within org)
- Accessible to all authenticated users
- No special permissions required

### MES Page (Private)
- **Access:** kirkmusick@gmail.com ONLY
- **Authentication:** Firebase Auth / Google SSO
- **Authorization:** Check email in middleware
- **BigQuery RLS:** Row-level security enforces data filtering
- **No Navigation Link:** Not shown in menu
- **Direct URL:** /mes (must be bookmarked)

### Implementation
```typescript
// middleware.ts
export function middleware(req: NextRequest) {
  const user = await getUser(req);
  if (req.nextUrl.pathname === '/mes') {
    if (user.email !== 'kirkmusick@gmail.com') {
      return NextResponse.redirect('/unauthorized');
    }
  }
}
```

---

## Data Refresh Strategy

### Real-Time (WebSocket)
- Breaking news alerts
- Price updates (every 1 min during market hours)

### Near Real-Time (Polling)
- Dashboard metrics (every 5 min)
- Sentiment scores (every 15 min)

### Batch Updates
- Daily forecasts (once per day at 6 AM ET)
- Model performance metrics (once per day)
- Historical data (nightly ETL)

---

## Performance Targets

- **Time to Interactive:** <2 seconds
- **First Contentful Paint:** <1 second
- **Largest Contentful Paint:** <2.5 seconds
- **API Response Time:** <500ms (p95)
- **Chart Rendering:** <100ms

---

## Monitoring & Analytics

### User Analytics
- Page views per user
- Time on page
- Click-through rates
- Feature usage

### System Metrics
- API response times
- Error rates
- Cache hit rates
- Query performance

### Business Metrics
- Forecast accuracy viewed
- Signal adoption rate
- MES page usage (private)

---

## Next Steps

1. Complete ZL sentiment page
2. Build strategy page
3. Implement Trade Intelligence page
4. Add MES private page with access control
5. Optimize mobile experience
6. Add WebSocket real-time updates

---

**Status:** Active development - ZL pages 60% complete, MES integration pending




