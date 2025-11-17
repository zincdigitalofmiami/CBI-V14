# Weather Data Collection Status & Verification
**Date**: November 16, 2025  
**Status**: In Progress - Using Correct Endpoints

---

## ✅ VERIFIED API ENDPOINTS (From User)

### 1. INMET Brazil
- **Main API**: `https://apitempo.inmet.gov.br/estacao/{start}/{end}/{station_id}`
- **Token**: `https://apitempo.inmet.gov.br/token`
- **Stations List**: 
  - `https://apitempo.inmet.gov.br/estacoes`
  - `https://apitempo.inmet.gov.br/estacao/dados-estacao`
  - `https://apitempo.inmet.gov.br/estacoes/T/A/,,/A/`
  - `https://portal.inmet.gov.br/api/estacoes/automaticas`

### 2. Argentina SMN
- **Open Data**: `https://ssl.smn.gob.ar/dpd/descarga_opendata.php?file=observaciones/datohorario{station_id}.txt`

### 3. NOAA (US)
- **API Data**: `https://www.ncei.noaa.gov/cdo-web/api/v2/data`
- **API Docs**: `https://www.ncdc.noaa.gov/cdo-web/webservices/v2`
- **Status**: Getting 503 errors (service unavailable)

### 4. Additional Sources
- **Copernicus CDS**: `https://cds.climate.copernicus.eu/api`
- **NOAA NOMADS GFS**: `https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl`
- **Meteomatics**: `https://api.meteomatics.com`

---

## 📊 CURRENT STATUS

### Brazil Weather
- **Option 1**: INMET API (fixing with correct endpoint)
- **Option 2**: Google BigQuery NOAA data (✅ working, tested)

### US Midwest Weather
- **Option 1**: NOAA API (❌ 503 errors)
- **Option 2**: Google BigQuery NOAA data (✅ working alternative)

### Argentina Weather
- **Option 1**: SMN Open Data (implementing now)
- **Option 2**: Google BigQuery NOAA data (✅ working alternative)

---

## 🔄 NEXT STEPS

1. Fix INMET script with correct endpoint
2. Create Argentina SMN collection script
3. Use BigQuery as backup for all regions
