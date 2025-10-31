-- Step 2: Create comprehensive FX view with all 4 pairs + 30d z-scores
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_fx_all` AS
WITH fx AS (
  SELECT
    date,
    CONCAT(from_currency,'/',to_currency) AS pair,
    rate
  FROM `cbi-v14.forecasting_data_warehouse.currency_data`
  WHERE (from_currency, to_currency) IN (('USD','ARS'),('USD','MYR'),('USD','BRL'),('USD','CNY'))
),
p AS (
  SELECT
    date,
    MAX(IF(pair='USD/ARS', rate, NULL)) AS fx_usd_ars,
    MAX(IF(pair='USD/MYR', rate, NULL)) AS fx_usd_myr,
    MAX(IF(pair='USD/BRL', rate, NULL)) AS fx_usd_brl,
    MAX(IF(pair='USD/CNY', rate, NULL)) AS fx_usd_cny
  FROM fx 
  GROUP BY date
),
z AS (
  SELECT
    date,
    fx_usd_ars,
    fx_usd_myr,
    fx_usd_brl,
    fx_usd_cny,
    (fx_usd_ars - AVG(fx_usd_ars) OVER win) / NULLIF(STDDEV(fx_usd_ars) OVER win, 0) AS fx_usd_ars_30d_z,
    (fx_usd_myr - AVG(fx_usd_myr) OVER win) / NULLIF(STDDEV(fx_usd_myr) OVER win, 0) AS fx_usd_myr_30d_z,
    (fx_usd_brl - AVG(fx_usd_brl) OVER win) / NULLIF(STDDEV(fx_usd_brl) OVER win, 0) AS fx_usd_brl_30d_z,
    (fx_usd_cny - AVG(fx_usd_cny) OVER win) / NULLIF(STDDEV(fx_usd_cny) OVER win, 0) AS fx_usd_cny_30d_z
  FROM p
  WINDOW win AS (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)
)
SELECT * FROM z;

