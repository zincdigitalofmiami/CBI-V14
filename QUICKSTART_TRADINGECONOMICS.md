# TradingEconomics Scraper - Quick Start Guide

## ⚡ 3-Minute Setup

### Step 1: Test the Scraper (1 minute)

```bash
cd /Users/zincdigital/CBI-V14
python3 cbi-v14-ingestion/tradingeconomics_scraper.py
```

**Expected output:**
```
Starting TradingEconomics hourly scraping cycle
Scraping https://tradingeconomics.com/commodity/palm-oil
Successfully scraped ... → palm_oil_prices
Loaded X rows to palm_oil_prices
Scraping cycle complete
```

### Step 2: Install Hourly Cron Job (30 seconds)

```bash
./setup_te_scraper_cron.sh
```

**What this does:**
- Installs cron job to run every hour on the hour
- Logs to `/tmp/tradingeconomics_scraper.log`

### Step 3: Verify Cron Installation (30 seconds)

```bash
crontab -l | grep tradingeconomics
```

**Should see:**
```
0 * * * * cd /Users/zincdigital/CBI-V14 && /usr/bin/python3 cbi-v14-ingestion/tradingeconomics_scraper.py >> /tmp/tradingeconomics_scraper.log 2>&1
```

### Step 4: Monitor Logs (1 minute)

```bash
tail -f /tmp/tradingeconomics_scraper.log
```

Press `Ctrl+C` to stop watching.

---

## ✅ Success Checks (After 24 Hours)

### Check 1: Palm Oil Data

```bash
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='cbi-v14'); query = 'SELECT COUNT(*) as cnt FROM \`cbi-v14.forecasting_data_warehouse.palm_oil_prices\`'; print(client.query(query).to_dataframe())"
```

**Expected:** Count > 0

### Check 2: FX Rates

```bash
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='cbi-v14'); query = 'SELECT COUNT(*) as cnt FROM \`cbi-v14.forecasting_data_warehouse.currency_data\` WHERE source_name=\"TradingEconomics\"'; print(client.query(query).to_dataframe())"
```

**Expected:** Count > 0

### Check 3: Economic Indicators

```bash
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='cbi-v14'); query = 'SELECT COUNT(*) as cnt FROM \`cbi-v14.forecasting_data_warehouse.economic_indicators\` WHERE source_name=\"TradingEconomics\"'; print(client.query(query).to_dataframe())"
```

**Expected:** Count > 0

---

## 🚨 Troubleshooting

### Problem: "No module named 'bs4'"

**Solution:**
```bash
pip3 install beautifulsoup4 requests pandas
```

### Problem: "google.cloud.bigquery not found"

**Solution:**
```bash
pip3 install google-cloud-bigquery
```

### Problem: Cron not running

**Solution:**
```bash
# Re-run setup script
./setup_te_scraper_cron.sh

# Or add manually:
crontab -e
# Add line: 0 * * * * cd /Users/zincdigital/CBI-V14 && /usr/bin/python3 cbi-v14-ingestion/tradingeconomics_scraper.py >> /tmp/tradingeconomics_scraper.log 2>&1
```

---

## 📊 What Data You're Getting

### Hourly:
- ✅ Palm oil prices (FCPO, rapeseed, sunflower)
- ✅ Soybean oil prices
- ✅ FX rates (USD/MYR, USD/BRL, USD/CNY, etc.)
- ✅ Crude oil prices
- ✅ Economic indicators

### Daily (once per day from monthly sources):
- ✅ MPOB palm oil fundamentals (when monthly data updates)
- ✅ Malaysia/Indonesia production/stocks/exports

---

## 💰 Cost

**Total:** $0.00/month (completely free)

---

## 🎯 Next Steps

After 24 hours of data collection:

1. **Calculate soy-palm spread** (Phase 2)
2. **Train LightGBM with palm features** (Phase 3)
3. **Visualize in Vite dashboard** (Phase 4)

---

**Questions?** Check `/tmp/tradingeconomics_scraper.log` for errors.

**Success?** You should see palm oil data appearing in BigQuery within 1-2 hours!

