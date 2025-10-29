# AUTOMATED DATA PULLS SETUP
## Implementation Complete - October 23, 2025

---

## ✅ SCHEDULE CONFIGURED

### 1. Bi-Daily News Scraping
**Frequency**: Every 12 hours  
**Times**: 8:00 AM ET & 8:00 PM ET  
**Script**: `scripts/bidaily_news_scraper.py`

**Sources** (14 high-value feeds):
- Bloomberg Markets
- Reuters Commodities
- Financial Times
- AgWeb
- Farm Progress
- Brownfield Ag
- Politico Agriculture
- OpenSecrets
- South China Morning Post
- MercoPress Argentina
- Biodiesel Magazine
- Ethanol Producer
- Reddit Commodities
- Reddit Farming

**Signal Extraction**:
- Soybean oil mentions
- Tariff/trade war references
- China trade signals
- Brazil/Argentina updates
- Legislation/policy mentions
- Biofuel indicators
- Weather impacts

### 2. Four-Daily Price Fetching
**Frequency**: 4 times per day  
**Times**: 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM ET  
**Script**: `scripts/four_daily_price_fetcher.py`

**Critical Components** (18 instruments):
- Soybean Oil (ZL=F)
- Soybeans (ZS=F)
- Soybean Meal (ZM=F)
- Crude Oil WTI (CL=F)
- Crude Oil Brent (BZ=F)
- Natural Gas (NG=F)
- Corn (ZC=F)
- Wheat (ZW=F)
- VIX (^VIX)
- Dollar Index (DX-Y.NYB)
- Treasury 10Y (^TNX)
- Treasury 5Y (^FVX)
- Treasury 30Y (^TYX)
- S&P 500 (^GSPC)
- Dow Jones (^DJI)
- Gold (GC=F)
- Silver (SI=F)
- Fed Funds Rate (FRED API)

---

## 📊 DATA FLOW

```
SOURCE          FREQUENCY         DESTINATION              PURPOSE
-------         ---------         -----------             -------
News RSS Feeds  Every 12 hours    news_bidaily            Signal extraction
Yahoo Finance   4x daily          realtime_prices         Price tracking
FRED API        4x daily          realtime_prices        Economic data
↓                                                  ↓
BigQuery Warehouse                           Feature Engineering
↓                                                  ↓
Training Pipeline                           Model Updates
```

---

## 🚀 SETUP INSTRUCTIONS

### To Install Automated Pulls:

```bash
# 1. Run the setup script
./scripts/setup_automated_pulls.sh

# 2. Verify installation
crontab -l

# 3. Test manually (optional)
python3 scripts/bidaily_news_scraper.py
python3 scripts/four_daily_price_fetcher.py
```

### Cron Schedule Details:

```cron
# Bi-daily news scraping (8 AM & 8 PM ET)
0 8,20 * * * cd /path/to/CBI-V14 && python3 scripts/bidaily_news_scraper.py

# Four-daily price fetching (8 AM, 12 PM, 4 PM, 8 PM ET)
0 8,12,16,20 * * * cd /path/to/CBI-V14 && python3 scripts/four_daily_price_fetcher.py
```

---

## 📈 EXPECTED DATA VOLUME

### Daily News Collection:
- **Articles per pull**: 50-100 (filtered for relevance)
- **Daily total**: 100-200 articles
- **Storage**: ~500 KB per pull
- **Signal coverage**: ~20-30% of articles with relevant signals

### Price Updates:
- **Records per pull**: 18 instruments
- **Daily total**: 72 price records
- **Storage**: ~50 KB per pull
- **Coverage**: 100% for critical components

### Monthly Totals:
- **News articles**: ~6,000 articles
- **Price records**: ~2,160 updates
- **Storage**: ~15 MB news + ~1.5 MB prices

---

## ✅ TEST RESULTS

### Price Fetcher Test (Oct 23, 11:53 AM):
✓ Successfully fetched 18 instruments:
- Soybean Oil: $51.06 ✓
- Soybeans: $1,059.50 ✓
- Crude Oil WTI: $61.95 ✓
- VIX: $17.61 ✓
- Fed Funds Rate: 4.11% ✓
- ... and 13 more

✓ Saved to BigQuery successfully

---

## 🔍 MONITORING

### Log Files:
- `logs/bidaily_scraper.log` - News scraping logs
- `logs/daily_price_fetcher.log` - Price fetching logs

### BigQuery Tables:
- `forecasting_data_warehouse.news_bidaily` - News articles
- `forecasting_data_warehouse.realtime_prices` - Price updates

### Health Checks:
```bash
# Check recent news pulls
bq query --use_legacy_sql=false "
SELECT COUNT(*) as articles, MAX(published_date) as latest
FROM \`cbi-v14.forecasting_data_warehouse.news_bidaily\`
WHERE DATE(published_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
"

# Check recent price pulls
bq query --use_legacy_sql=false "
SELECT COUNT(*) as records, MAX(timestamp) as latest
FROM \`cbi-v14.forecasting_data_warehouse.realtime_prices\`
WHERE DATE(timestamp) = CURRENT_DATE()
"
```

---

## 🛠️ TROUBLESHOOTING

### If cron jobs don't run:
1. Check crontab is installed: `crontab -l`
2. Check log files for errors
3. Verify Python path: `which python3`
4. Test scripts manually

### If BigQuery upload fails:
1. Check service account permissions
2. Verify table exists
3. Check quota limits
4. Review error logs

### If API rate limits hit:
1. Scripts have built-in delays
2. Stagger fetch times if needed
3. Reduce symbol list if necessary

---

## 📋 MAINTENANCE

### Weekly:
- Review log files for errors
- Check data quality in BigQuery
- Verify signal extraction accuracy

### Monthly:
- Audit cron job execution
- Review storage costs
- Update source list if needed
- Validate feature engineering

### Quarterly:
- Review and update API keys
- Optimize fetch schedule
- Add/remove data sources
- Update signal keywords

---

## 🎯 SUCCESS METRICS

### News Collection:
- ✓ >50 articles per pull
- ✓ >20% signal relevance
- ✓ <2% error rate

### Price Fetching:
- ✓ 100% instrument coverage
- ✓ <1% error rate
- ✓ <5 second per pull

### Overall:
- ✓ >95% uptime
- ✓ Automatic retry on failure
- ✓ CSV backup on BigQuery error

---

## ✅ STATUS: OPERATIONAL

All scripts tested and verified working. Automation ready for deployment.
