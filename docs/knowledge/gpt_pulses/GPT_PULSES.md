# GPT Pulses Catalogue

Curated AI-assisted insights for CBI-V14.  
Treat these as advisory patterns: adopt only after they pass through normal review, cost, and architecture guardrails.

---

## Index

1. Pulse 1 – BigQuery/Dataform guardrails (assertions, JOBS lineage, SRE-style rollbacks)
2. Pulse 2 – Databento pricing and dataset coverage (GLBX.MDP3, IFUS.IMPACT)
3. Pulse 3 – Climate anomalies, ENSO regimes, and drought outlook features
4. Pulse 4 – Regime calendar weighting pattern in BigQuery
5. Pulse 5 – High-signal research workflow (Google `site:` operator + X Lists)
6. Pulse 6 – Vercel “Require Verified Commits” for deployments
7. Pulse 7 – NOAA staples for climate + markets (GHCN-Daily, CPC soil moisture, CFSv2 outlooks)
8. Pulse 8 – Palm-oil geopolitics and Malaysian futures pressure
9. Pulse 9 – European diesel–Brent spread blowout and biofuels implications
10. Pulse 10 – Detecting and correcting signal-weighting drift across regimes

---

## Pulse 1 – BigQuery/Dataform guardrails (assertions, JOBS, SRE rollbacks)

**Theme:** Harden the BigQuery/Dataform data plane with built-in quality checks, lineage, and rollback habits.

### 1) Ship guardrails with Dataform assertions

- Use Dataform **assertions** so every run enforces basic data quality:
  - Null checks on key columns
  - Uniqueness constraints for primary keys
  - “No future dates” and domain-specific rules
- Example assertion:

```sql
-- definitions/ops/assert_no_future_dates.sqlx
config { type: "assertion", name: "assert_no_future_dates" }

select *
from ${ref("stg_orders")}
where order_date > current_date()
```

- Keep richer checks as standalone `sqlx` assertion files and wire them into the dependency tree. Failed assertions should **fail the run** so bad data never reaches gold tables.

### 2) Track lineage and cost with INFORMATION_SCHEMA.JOBS

- Use `INFORMATION_SCHEMA.JOBS*` views as the canonical **job audit and lineage** source:
  - Track bytes processed, timing, destination tables, and errors.
  - Attribute cost by `user_email` or job label.
- Examples:

```sql
-- Top spenders yesterday
select user_email, sum(total_bytes_processed) as bytes
from region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT
where creation_time >= timestamp_sub(current_timestamp(), interval 1 day)
group by 1
order by bytes desc;

-- Link a Dataform run to downstream tables via job_id
select job_id, statement_type, destination_table
from region-us.INFORMATION_SCHEMA.JOBS
where creation_time >= timestamp_sub(current_timestamp(), interval 1 day);
```

- Build a small dashboard on top of `JOBS_BY_PROJECT` for:
  - Bytes scanned and slot usage
  - Error rates and failing queries
  - High-cost or long-running pipelines

### 3) Borrow SRE playbooks for pipelines (backfills and rollbacks)

- Treat pipeline releases like app releases:
  - **Canary** changes into a narrow slice of data first.
  - Monitor SLO-style signals: timeliness, freshness, error rate.
  - **Roll back first, diagnose after** when a bad release is suspected.
- Keep backfills behind flags and document recovery steps:
  - How to revert materialized views/tables
  - How to replay a run from a safe checkpoint
  - How to restore “last good” table versions

### 4) Quick starter checklist for this project

- Add assertions to every “gold” table:
  - Null checks, uniqueness, freshness
  - 1–2 domain rules per table (e.g., no negative quantities, no future timestamps)
- Create a `jobs_audit` dashboard from `INFORMATION_SCHEMA.JOBS_BY_PROJECT`:
  - Bytes processed, errors, top queries, cost by label or owner.
- Define pipeline SLOs (for example):
  - “D+1 by 06:00 UTC, 99.5% of days”
  - Wire alerts to assertion failures and late runs.
- Standardize rollbacks:
  - Keep previous materialized versions (or `_previous` views)
  - Document a one-click or one-script revert for key datasets.

References:
- Dataform assertions: https://docs.cloud.google.com/dataform/docs/assertions
- BigQuery JOBS views: https://docs.cloud.google.com/bigquery/docs/information-schema-jobs
- SRE pipelines: https://sre.google/sre-book/data-processing-pipelines

---

## Pulse 2 – Databento pricing and dataset coverage (GLBX.MDP3, IFUS.IMPACT)

**Date:** November 25, 2025  
**Theme:** How current Databento pricing and futures/options datasets affect cost and coverage for this project.

### 1) Pricing / subscription snapshot

- As of 2025‑11‑25, the **Standard** plan is listed at **$199/month** for individuals/small teams.  
  - Includes live data plus a defined slice of historical access.
- Historical note (2025‑04‑16 announcement):
  - The Standard CME plan was listed around **$179/month** when the new plans were rolled out.
  - This coincided with a shift **away from purely usage-based live billing** toward tiered subscriptions.
- For US equities, the Standard plan at $199/month reportedly includes:
  - Live feed
  - **1 year** of L1 history
  - **1 month** of L2/L3 history
  - Anything beyond those windows is pay‑as‑you‑go.
- While that statement is equities-specific, it suggests **similar economics** may apply to other asset classes:
  - Subscription covers live + a baseline historical window.
  - Deeper or older history (especially full-depth order book) can become incremental cost.

**Why it matters here:**

- The move to subscription tiers changes the cost model:
  - Baseline live + some history is predictable (monthly).
  - Heavy full-history backfills, especially for L2/L3 or deep depth-of-book, should be explicitly planned and costed.
- We should monitor:
  - Future price changes (e.g., $179 → $199 progression).
  - Whether premium features (dedicated connectivity, redistribution rights, etc.) push us into higher tiers.

Key references:
- Pricing overview: https://databento.com/pricing
- New CME pricing plans: https://databento.com/blog/introducing-new-cme-pricing-plans
- Upcoming pricing changes: https://databento.com/blog/upcoming-changes-to-pricing-plans-in-january-2025

### 2) CME Globex MDP 3.0 (GLBX.MDP3) – coverage & features

- Dataset covers **all CME Group venues**:
  - CME, CBOT, NYMEX, COMEX futures, options, spreads, and combos.
- Event-based feed with **nanosecond timestamps**:
  - Captures bids, asks, trades, statistics, and depth updates.
- Supports multiple microstructure views:
  - Full order book (MBO)
  - Market-by-price (MBP)
  - Top-of-book (BBO) and summary schemas
- Relevance to this project:
  - GLBX.MDP3 is already our **primary futures data source** (ZL, ES, MES, etc.).
  - Tick-level and depth-of-book data enables:
    - Order-book imbalance features
    - Spread/arb signals between legs
    - Volatility + liquidity regime indicators

Key references:
- Dataset overview: https://databento.com/datasets/GLBX.MDP3
- Feed specifications: https://databento.com/docs/venues-and-datasets/glbx-mdp3
- Futures examples: https://databento.com/docs/examples/futures/futures-introduction

### 3) ICE Futures US iMpact (IFUS.IMPACT) – coverage & features

- Dataset covers ICE Futures US markets:
  - Soft commodities, metals, FX futures, and MSCI index futures.
- Based on ICE’s proprietary **iMpact** feed:
  - Futures and options on futures.
  - Schemas include **full order depth (FOD)** for futures and **MBP‑10** for options.
  - Microsecond timestamps, normalized to nanoseconds in Databento.
- Example of specific coverage:
  - Canola futures symbol “RS” under ICE Futures US is explicitly listed as covered.
- Relevance to this project:
  - Important if strategy extends to softs/FX/indices beyond CME/CBOT universe.
  - Enables cross‑exchange studies (e.g., canola vs soy complex) with similar microstructure granularity as GLBX.MDP3.

Key references:
- IFUS.IMPACT announcement: https://databento.com/blog/introducing-ice-futures-us
- Example instrument (RS1): https://databento.com/catalog/ifus/IFUS.IMPACT/futures/RS1
- Feed specifications: https://databento.com/docs/venues-and-datasets/ifus-impact

### 4) Practical implications for CBI‑V14

- **Cost management:**
  - Subscription gives predictable access to live data and a baseline of history.
  - Full-history depth (especially for L2/L3 or FOD/MBP‑10) should be treated as **explicit projects** with cost caps.
- **Data strategy:**
  - GLBX.MDP3 remains the canonical source for CME/CBOT/NYMEX/COMEX.
  - IFUS.IMPACT is the natural extension for ICE softs/FX/metals if/when those become in-scope.
- **Next possible step (optional):**
  - Build a small cost model for:
    - “Standard plan only” usage.
    - “Standard plan + full-history backfill for selected symbols.”
  - Tie it back to BigQuery cost dashboards and collection scripts so that high‑cost backfills are always visible and approved in advance.

---

## Pulse 3 – Climate anomalies, ENSO regimes, and drought outlook features

**Theme:** Turn large-scale climate signals into structured, region-level features for soybean oil intelligence.

### 1) CFSv2 seasonal anomaly fields (CPC)

- CPC’s CFSv2 seasonal anomaly product provides **precipitation and 2 m temperature anomalies** (and other fields) versus the 1991–2020 climatology.
- Fields are ensemble-based (e.g., 40 members) with **skill masks** highlighting regions where the model has historical forecast skill.
- Caveats:
  - These are **model-based anomaly forecasts**, not the official CPC seasonal outlooks.
  - Skill is strongly regional and lead-time dependent; treat low-skill regions with caution.

**Feature ideas:**

- Ingest gridded anomaly fields for key agricultural regions (Brazil, Argentina, U.S. soy belt).
- Spatially aggregate:
  - Mean precip anomaly (mm/day) over each region.
  - Mean T2m anomaly (°C) over each region.
- Build horizon-specific features:
  - `seasonal_precip_anom_3m`, `seasonal_precip_anom_6m`
  - `seasonal_t2m_anom_3m`, `seasonal_t2m_anom_6m`
- Store lead/initialization metadata so you can back-test “forecast vs realized” behavior.

Implementation sketch:

- Land CFSv2 anomaly grids into GCS as NetCDF/GRIB → convert to Parquet by region.
- In BigQuery, create a `weather.seasonal_anomalies` table keyed by `(date, region, horizon_months)`.
- Join into `features.*_ml_matrix` on `(date, region)` with explicit horizon columns.

Key references:
- CFSv2 seasonal anomalies: https://www.cpc.ncep.noaa.gov/products/CFSv2/CFSv2seasonal.shtml
- CFSv2 SST skill paper: https://link.springer.com/article/10.1007/s00382-013-1845-2

### 2) ENSO status and regime variables

- As of 2025‑11‑13, CPC reports a **La Niña Advisory**:
  - Below-average SSTs in the central/eastern equatorial Pacific.
  - La Niña favored to continue into boreal winter, with transition to ENSO-neutral most likely in Jan–Mar 2026.
- ENSO has well-documented **teleconnections** that shape precipitation/temperature patterns globally.

**Feature ideas:**

- Categorical regime:
  - `enso_state` ∈ {`la_nina`, `neutral`, `el_nino`}.
- Continuous indices:
  - Niño‑3.4 SST anomaly, ONI index, or similar.
- Gating features:
  - Interaction terms like `enso_la_nina * regional_precip_anom`.
  - Different model weights or submodels per ENSO state.

Implementation sketch:

- Maintain a small `climate.enso_history` table in BigQuery:
  - `date`, `enso_state`, `nino34_anom`, `oni_value`, etc.
- Join into feature tables by date, and consider:
  - Regime-specific calibration (e.g., different target distributions).
  - Feature masks where ENSO teleconnections are known to be weak.

Key reference:
- ENSO Diagnostic Discussion: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml

### 3) CPC Seasonal Drought Outlook – dryness risk flags

- CPC Seasonal Drought Outlook indicates where drought is expected to **persist**, **develop**, or **improve** over coming months.
- Text discussion highlights regions at risk of **deterioration** (e.g., southern Plains, southern tier, parts of the Atlantic seaboard).

**Feature ideas:**

- Region-level drought risk categorization:
  - `drought_outlook` ∈ {`development_likely`, `persistence_likely`, `improvement_likely`, `no_signal`}.
  - Binary `high_dryness_risk` flag for drought development/persistence in key crop regions.
- Interactions with weather anomalies:
  - Amplify the effect of negative precip anomalies when `high_dryness_risk = 1`.
  - Condition yield/production risk models on outlook category.

Implementation sketch:

- Build a lookup table `climate.drought_outlook_regions`:
  - `valid_from`, `valid_to`, `region_id`, `drought_category`, `high_dryness_risk`.
- Map USDA/NASS crop districts or custom soy regions onto these outlook regions.
- Join into soybean/soy-oil feature tables by `(date, region_id)` to emit:
  - `high_dryness_risk`
  - `drought_outlook_category`

Key reference:
- Seasonal Drought Outlook: https://www.cpc.ncep.noaa.gov/products/expert_assessment/sdo_summary.php

### 4) Recommended next steps

- Ingest and normalize:
  - CFSv2 anomaly grids → regional time series.
  - ENSO indices → `climate.enso_history`.
  - Seasonal drought outlooks → `climate.drought_outlook_regions`.
- Add features to soybean/soy-oil pipelines:
  - Seasonal anomaly features per region/horizon.
  - ENSO regime variables and interactions.
  - Drought risk flags to gate anomaly impacts.
- Back-test:
  - MAPE / Sharpe improvement from adding each group.
  - Robustness across ENSO regimes and drought states.

---

## Pulse 4 – Regime calendar weighting pattern in BigQuery

**Theme:** Keep regime-dependent training weights explicit, auditable, and decoupled from feature generation.

### 1) Minimal schema

- `training.regime_calendar`
  - `date DATE`
  - `regime STRING` (e.g., `pre_2010`, `covid`, `post_pivot`)
  - `training_weight FLOAT64` (e.g., `0.6`, `1.0`, `1.4`)
- `features.daily_ml_matrix`
  - `date DATE` (primary join key)
  - `regime STRING` (from your regime logic)
  - many feature columns (`rsi_14`, `atr_14`, `vix_lvl`, …)
  - labels/targets (or store them in separate `training.*` tables)

### 2) BigQuery pattern – apply weights inline

- Keep **bias correction separate** from features/labels.
- Apply weights in the export query, not baked into features.

Pattern:

```sql
WITH spine AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY('2000-01-01', CURRENT_DATE())) AS date
),
weighted AS (
  SELECT
    f.date,
    f.regime,
    COALESCE(rc.training_weight, 1.0) AS w,
    (f.rsi_14 * COALESCE(rc.training_weight, 1.0))  AS rsi_14_w,
    (f.atr_14 * COALESCE(rc.training_weight, 1.0))  AS atr_14_w,
    (f.vix_lvl * COALESCE(rc.training_weight, 1.0)) AS vix_lvl_w,
    f.target_1w
  FROM spine s
  LEFT JOIN features.daily_ml_matrix f USING (date)
  LEFT JOIN training.regime_calendar rc USING (date)
)
SELECT *
FROM weighted
WHERE date BETWEEN '2005-01-01' AND '2025-11-24';
```

### 3) Authoring and governance

- **Single source of truth:** only `training.regime_calendar` controls weights.
- **Auditable diffs:** maintain via `MERGE` statements so changes are clearly tracked.
- **No joins at training time:** export one **ready-to-train** Parquet per horizon from BigQuery.
- **Feature parity:** during experimentation, keep both raw and weighted columns (e.g., `rsi_14` and `rsi_14_w`).

### 4) Typical workflows

- Change a regime’s emphasis:
  - Edit `training_weight`, re-export; Python training loop stays unchanged.
- AB compare:
  - Export one dataset with all weights = 1.0, another with tuned weights.
- Roll forward:
  - Append new dates to `regime_calendar` daily with default `1.0`, unless you define a new regime window.

---

## Pulse 5 – High-signal research workflow (Google `site:` operator + X Lists)

**Theme:** Keep research and social monitoring focused on trustworthy, high-signal sources.

### 1) Google `site:` operator for precision sourcing

- Restrict results to specific domains or paths:
  - `site:ft.com "soybean oil"`
  - `site:usda.gov WASDE`
  - `site:noaa.gov ENSO outlook`
- Paths work too:
  - `site:https://www.usda.gov/media blog`
- Notes:
  - `site:` does **not** return a full index count.
  - Ranking may be non-ordered and incomplete, but precision is usually high.

Copy-paste starter queries:

- Policy/research:
  - `site:congress.gov "renewable diesel"`
  - `site:fda.gov acrylamide`
- Markets:
  - `site:ec.europa.eu biodiesel quota`
  - `site:cmegroup.com ZL futures methodology`
- Weather:
  - `site:noaa.gov ENSO outlook`
  - `site:ncei.noaa.gov drought monitor`

References:
- Site operator docs: https://developers.google.com/search/docs/monitor-debug/search-operators/all-search-site
- Advanced Search UI: https://support.google.com/websearch/answer/35890

### 2) X (Twitter) Lists for noise-free timelines

- Lists are curated groups of accounts:
  - Viewing a List shows only those accounts’ posts.
  - Lists can be public or private; you can also follow others’ Lists.
- Limits (at time of writing):
  - Up to 1,000 Lists per account.
  - Up to 5,000 accounts per List.

Fast setup pattern:

- Create a List:
  - e.g., `USDA & Ag Policy`, `Soy Complex Macro`, `Vegas F&B Pulse`.
- Add sources:
  - USDA, CME Group, NOAA, local ag/weather services, reputable journalists/analysts.
- Daily workflow:
  - Check List timelines instead of the full home feed for a **focused**, low-noise view.

References:
- About Lists: https://help.x.com/en/using-x/x-lists
- Troubleshooting Lists: https://help.x.com/en/using-x/x-lists-not-working

---

## Pulse 6 – Vercel “Require Verified Commits” for deployments

**Theme:** Tighten deployment security by only allowing cryptographically signed commits to reach Vercel.

### 1) What Vercel added

- As of 2025‑11‑24, Vercel supports a **“Require Verified Commits”** option for GitHub-connected projects.
- When enabled under:
  - Vercel Dashboard → Project → Settings → Git → “Require Verified Commits”
  - Any deployment triggered by a non‑verified GitHub commit is automatically **cancelled**.
- Verification relies on GitHub’s commit-signature mechanisms:
  - GPG, SSH, or S/MIME signatures that GitHub marks as “Verified”.

Key references:
- Vercel changelog: https://vercel.com/changelog/deployments-can-now-require-cryptographically-verified-commits
- Vercel Git settings: https://vercel.com/docs/project-configuration/git-settings
- GitHub commit signatures: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification

### 2) Why this matters for CBI‑V14

- Strengthens the deployment chain:
  - Only commits signed by trusted keys can promote to production (or preview, if configured).
  - Reduces risk of unauthorized or spoofed commits triggering deployments.
- Aligns with a **defense-in-depth** posture:
  - Pairs with branch protection rules, required reviews, and status checks.
  - Useful for any environment where financial models or data pipelines are exposed via Vercel.

### 3) Practical setup checklist

- Team readiness:
  - Ensure all commit authors have signing configured (GPG/SSH) and see “Verified” badges on GitHub commits.
  - Document how to generate and register keys per developer.
- Vercel configuration:
  - Start with a staging or preview project.
  - Enable “Require Verified Commits” and confirm deployments succeed only from signed commits.
- Rollout plan:
  - Communicate clearly that unsigned commits will not deploy.
  - Once stable in staging, enable for the main production project.

### 4) How to integrate into your workflow

- Local Git:
  - Set `commit.gpgsign=true` (or SSH signing equivalent) in global/local Git config.
  - Make signing the default rather than opt-in.
- Observability:
  - When a deployment is cancelled due to an unverified commit, treat it like a failed check.
  - Optionally, add internal docs linking this pulse so future contributors understand the failure mode quickly.

---

## Pulse 7 – NOAA staples for climate + markets (GHCN-Daily, CPC soil moisture, CFSv2 outlooks)

**Theme:** Build a clean, multi-timescale climate layer using three NOAA workhorses.

### 1) GHCN-Daily – station-level weather history

- What:
  - Global station-level daily observations (e.g., `TMAX`, `TMIN`, `PRCP`) with station metadata (ID, latitude/longitude, elevation).
  - Quality-controlled and updated daily via NCEI.
- Why:
  - Provides robust historicals for:
    - Temperature/precipitation anomalies
    - Heating/cooling degree days (HDD/CDD)
    - Event studies around extremes (heat waves, flood events)
- Where:
  - NCEI GHCN-Daily landing page and README.
  - Also mirrored in some cloud ecosystems (e.g., BigQuery public datasets).

Integration sketch:

- Maintain a `weather.ghcn_daily` table keyed by `(station_id, date)` with:
  - `tmax_c`, `tmin_c`, `prcp_mm`, and quality flags.
  - Join to regions (e.g., crop districts) via a station-to-region mapping table.
- Derive features:
  - Rolling anomalies vs station normals.
  - Region-aggregated HDD/CDD for demand/yield models.

Reference:
- GHCN-Daily: https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily

### 2) CPC Soil Moisture (NLDAS-based)

- What:
  - U.S. soil moisture totals, anomalies, and percentiles.
  - Derived from land-surface models within the North American Land Data Assimilation System (NLDAS).
- Why:
  - Direct proxy for:
    - Agricultural stress and drought conditions.
    - Yield and production risk in key crop regions.
- Where:
  - CPC soil moisture monitoring pages and documentation.
  - Additional context and maps via Drought.gov tooling.

Integration sketch:

- Build a `climate.soil_moisture_nldas` table keyed by `(date, region_id)`:
  - Store totals, anomalies, and percentiles.
  - `region_id` could be state, crop district, or a custom soy region polygon.
- Derive features:
  - `soil_moisture_pctile` and `soil_moisture_anom` per region.
  - Interaction terms with precip and temperature anomalies.

References:
- CPC soil moisture: https://www.cpc.ncep.noaa.gov/products/Soilmst_Monitoring/US/Soilmst/Soilmst.shtml
- Drought.gov soil moisture products: https://www.drought.gov/data-maps-tools/cpc-soil-moisture

### 3) CFSv2 seasonal outlooks – global climate forecasts

- What:
  - Global seasonal anomaly forecasts (e.g., 2 m temperature, precipitation) from the CFSv2 model.
  - Issued as multi-member ensembles from recent initial conditions.
- Why:
  - Forward-looking climate signals for:
    - Medium-range hedging and demand planning.
    - Anticipating ENSO-linked pattern shifts.
- Where:
  - CPC CFSv2 body/overview pages.
  - Current T2m anomaly panels and related products on CPC’s site.

Integration sketch:

- Snapshot CFSv2 monthly T2m/precip anomaly panels at a regular cadence (e.g., daily or weekly).
- Convert to region-level time series:
  - `cfs_t2m_anom_lead1`, `cfs_t2m_anom_lead3`
  - `cfs_prcp_anom_lead1`, `cfs_prcp_anom_lead3`
  - Optionally include ensemble spread as a confidence proxy.
- Join into feature tables alongside realized GHCN-Daily and soil-moisture features to compare forecast vs actual.

References:
- CFSv2 seasonal forecast overview: https://www.cpc.ncep.noaa.gov/products/CFSv2/CFSv2_body.html
- Example T2m anomaly panels: https://www.cpc.ncep.noaa.gov/products/CFSv2/htmls/euT2me3Mon.html

### 4) Fast integration ideas for this stack

- Historical layer:
  - Pull GHCN-Daily into curated storage with full station metadata for joins.
- Hydro/soil features:
  - Sample CPC soil moisture percentiles/anomalies into soybean/soy-oil regions.
- Forward signals:
  - Build rolling CFSv2 anomaly features (lead-month, lead-3 mean, ensemble spread) tied into the existing climate/ENSO/drought feature family from Pulse 3.

---

## Pulse 8 – Palm-oil geopolitics and Malaysian futures pressure

**Theme:** Track structural and market stress in the palm-oil complex as a key driver of soybean-oil dynamics.

### 1) Riau Province protests and plantation seizures (Indonesia)

- Situation:
  - Thousands of growers and residents in Riau Province protested against the seizure of palm-oil plantations by the government’s forestry task force.
  - The task force, backed by military and legal personnel, is reclaiming plantations deemed to be operating illegally on forest land.
  - Roughly **3.7 million hectares** of plantations have been seized across Indonesia.
  - About half of that area has been transferred to state-run **Agrinas Palma Nusantara**, which is now described as the world’s largest palm-oil company by land area.
  - In Riau’s capital, Pekanbaru, ≈2,800 protesters were met with ≈1,300 security personnel as they demanded transparency and legal recourse.
- Why it matters:
  - Riau is a major palm-oil producing region; social and regulatory conflict here can ripple through global supply chains.
  - Large-scale land seizures and consolidation into a state-run entity raise:
    - Governance and transparency risks.
    - Potential for disruptions, policy shifts, and shifts in bargaining power along the value chain.

Signals to monitor:

- Frequency and scale of further seizures or legal challenges.
- Any impacts on:
  - FFB collection, milling throughput, and export flows.
  - Labor conditions, smallholder access, and local logistics in Riau and neighboring provinces.
- Policy moves around forest compliance, sustainability standards, and export regulations.

Reference:
- Reuters coverage: https://www.reuters.com/sustainability/thousands-protest-against-state-takeover-palm-oil-plantations-indonesias-riau-2025-11-20

### 2) Malaysian palm-oil futures under pressure

- Market context:
  - Malaysian palm-oil futures recently edged lower, driven mainly by:
    - Weaker rival edible oils (soybean, sunflower), which encourage buyers to switch away from palm.
    - Softer export data and weaker-than-expected demand.
    - Rising production and inventories in Malaysia.
  - Despite the pullback, the market is reportedly still on track for a **second weekly gain**, suggesting underlying resilience.
- Why it matters:
  - Price action reflects a tug-of-war between:
    - Demand-side pressure (exports, competition from rival oils).
    - Supply-side forces (production, inventories, and potential policy shocks).
  - Combined with Indonesian regulatory/social risks, this can:
    - Tighten or loosen the global palm-oil balance.
    - Change relative pricing vs soybean oil, impacting spreads and substitution behavior.

Signals to monitor:

- Export breakdowns by destination (e.g., China, India, EU) and changes in buying patterns.
- Inventory levels and production forecasts from Malaysian authorities and industry bodies.
- Cross-asset pricing:
  - Palm vs soybean oil spreads (your “Crystal Ball” corridor).
  - Crude oil/biofuel-linked demand signals.

Key references:
- NST coverage of recent futures moves: https://www.nst.com.my/business/corporate/2025/11/1319603/palm-dips-weaker-rival-oils-softer-exports-still-set-second
- Finimize summaries of palm-oil price drivers:
  - https://finimize.com/content/malaysian-palm-oil-prices-fall-on-rising-output-and-global-competition
  - https://finimize.com/content/palm-oil-futures-slip-as-asian-markets-diverge

### 3) How to plug this into your system

- Qualitative → quantitative mapping:
  - Maintain a small `geo.palm_risk_events` table with:
    - `event_date`, `country`, `region`, `event_type` (e.g., protest, seizure, policy_change), `severity_score`, `source_link`.
  - Encode Riau and similar events as time-stamped risk pulses feeding your palm/soy complex.
- Spread and correlation work:
  - Track palm vs soybean oil price spreads in BigQuery.
  - Overlay event markers and futures-pressure episodes for regime and scenario analysis.
- Scenario inputs:
  - Use these geopolitical and market-stress indicators as:
    - Inputs to scenario dashboards.
    - Gating variables in stress-testing modules for biofuel and edible-oil value chains.

---

## Pulse 9 – European diesel–Brent spread blowout and biofuels implications

**Theme:** Distillate cracks are surging while crude stays muted—signalling structural stress that can propagate into biofuels and vegetable oils.

### 1) What’s happening

- Diesel vs Brent spread:
  - The gap between diesel and Brent crude has jumped to around **$34/barrel**, the highest since September 2023.
  - Northwest Europe diesel prices briefly reached ≈**$845/tonne**, up from ≈$628/tonne a month earlier.
- Divergence with crude:
  - Brent crude is down ~3% even as diesel premiums rise, highlighting a disconnect:
    - Crude relatively soft.
    - Distillates (diesel) acutely tight.

Primary drivers discussed in coverage:

- Supply shocks and sanctions:
  - Sanctions and restrictions on key Russian exporters (e.g., Rosneft, Lukoil) affecting refined product flows into Europe.
- Refining bottlenecks:
  - Outages/turnarounds in Europe and the Middle East affecting diesel yields.
- Inventory tightness:
  - Lower stocks in key hubs (e.g., ARA: Amsterdam–Rotterdam–Antwerp) heightening vulnerability as winter demand approaches.

References:
- FT diesel spread coverage: https://www.ft.com/content/684c70a8-91de-4b4b-9148-b42d48559d1d
- OPIS diesel crack analysis: https://www.opis.com/resources/energy-market-news-from-opis/europe-diesel-crack-hits-two-year-high-on-supply-fears
- Kpler on persistent tightness: https://www.kpler.com/blog/fading-speculative-attention-masks-persistent-diesel-tightness-ct2fr

### 2) Why it matters for this project

- For transport/logistics and energy-intensive users:
  - Input costs (diesel) can spike quickly, squeezing margins and undermining hedges.
  - Structural tightness in European distillates raises the risk profile into winter.
- For soybean oil / biofuels intelligence:
  - Elevated diesel cracks can:
    - Pull incremental demand toward biodiesel/HVO and other alternative transport fuels.
    - Shift feedstock economics if diesel-derived margins justify higher biofuel blending.
  - This can feed back into:
    - Vegetable-oil demand.
    - Upstream feedstock pricing and margin structures.

### 3) Signals and triggers to monitor

- Sanctions / policy:
  - New or tightened sanctions on Russian oil firms and refined products.
  - EU regulatory changes or import bans affecting diesel flows.
- Physical market indicators:
  - Refinery outages/turnarounds in Europe/Middle East that hit diesel output.
  - ARA and wider Atlantic-basin inventory levels for distillates.
- Market structure:
  - Time spreads and cracks in diesel vs Brent.
  - Freight/tanker constraints affecting product re-routing.

### 4) How to plug into your system

- Quant layer:
  - Track a `diesel_brent_spread` time series in BigQuery (e.g., USD/barrel).
  - Tag periods of extreme spread (e.g., top decile) as events/regimes.
- Scenario and risk dashboards:
  - Surface a “distillate stress” indicator alongside your soy/palm/biofuel metrics.
  - Use event flags when distillate cracks are in extreme territory as:
    - Inputs to procurement timing tools.
    - Context when interpreting biofuel and vegetable-oil price moves.

---

## Pulse 10 – Detecting and correcting signal-weighting drift across regimes

**Theme:** Catch and fix regime-driven weighting drift in your models before it degrades out-of-sample performance, especially when training happens on the Mac and dashboards only see mirrored outputs.

### 1) What “weighting drift” is

- Models learn feature weights under a specific **regime** (market structure, volatility, policy, liquidity).
- As data rolls forward:
  - Feature scale, variance, and cross-correlations shift.
  - Incremental updates over-emphasize the most recent regime.
- Symptoms:
  - Rising MAPE/RMSE on true out-of-sample windows.
  - Unstable SHAP ranks and “great on last month, poor on last quarter”.
  - Flip-flopping feature importance across short windows.

### 2) Quick fix before retraining – post-ingestion rebalancing

High-level pattern:

1. **Freeze the model.**
   - Use the current checkpoint; do not retrain yet.
2. **Lock data slices by regime.**
   - Example buckets for ZL:
     - `pre_2010`, `2010_2015_qe`, `2016_2019_tariffs`, `2020_2022_covid_liquidity`, `2023_2025_biofuel_saf`.
3. **Standardize per regime, not globally.**
   - Fit scalers within each regime and store them with metadata.
4. **Compute regime weights.**
   - Target: equal effective mass across regimes at evaluation.
   - Simple start: `w_r = 1.0 / n_r` (equal-mass).
   - Upgrade: `w_r = 1.0 / (RMSE_r + ε)` from a quick baseline model.
5. **Apply weights in evaluation.**
   - For tree/linear models: pass `sample_weight` for validation/eval.
   - For neural nets: multiply loss by `w[i]` or use weighted samplers.
6. **Compare error surfaces.**
   - Check:
     - MAPE/RMSE by horizon.
     - Regime parity (max/min error across regimes).
     - SHAP rank stability.

If the weighted evaluation lowers and flattens the error surface (better parity, more stable SHAP), that’s strong evidence of weighting drift—only then retrain with weights baked in.

### 3) Minimal implementation pattern (Mac M4, local-first)

- Data prep:
  - Tag `regime_id` per row.
  - For each regime `r`, fit a scaler on `X_cols` for that slice.
  - Save scalers to `/TrainingData/features/_scalers/{symbol}/{regime}.json` with `fit_date` and versioning.
- Weight vector:
  - Start with `w_r = 1.0 / n_r`.
  - Optionally refine with inverse-RMSE weights from a quick baseline (e.g., LightGBM or linear model).
- Eval harness:
  - Build a **locked validation set** stratified by regime × month.
  - Run frozen model:
    - A) without weights → `metrics_A`
    - B) with sample weights → `metrics_B`
  - If `MAPE_B < MAPE_A` and regime error spread shrinks, proceed to retrain with weights.

### 4) Training with weights (but reversible)

- Linear/tree models:
  - Use `sample_weight` in training.
  - Ensure cross-validation folds are stratified by `regime_id`.
- Neural networks (PyTorch/LSTM/etc.):
  - Multiply loss by `w[i]` in each batch.
  - Or use a `WeightedRandomSampler` to rebalance mini-batches.
- Reversibility:
  - Keep configs so you can flip back to unweighted training for A/B comparisons.

### 5) Guardrails to add now

- **Checkpoint parity panel:**
  - After each update, run the frozen model on a fixed parity dataset.
  - Track MAPE deltas; alert if jump > threshold (e.g., +0.4% absolute).
- **SHAP rank stability:**
  - Track Kendall τ rank correlation for the top-10 features week-over-week.
  - Large swings are a drift signal.
- **Scaler registry:**
  - Never silently replace global scalers.
  - Attach `scaler_version`, `regime_id`, and `fit_date` to exported feature Parquet files.
- **Leakage sanity check:**
  - Run permutation importance on the validation slice.
  - If previously strong macro features collapse to noise suddenly, investigate joins/regimes/scalers.

Suggested starting thresholds:

- 7d horizon MAPE:
  - Target ≤ 2.5–3.0%; flag if +0.4% absolute week-over-week.
- Regime error ratio (max/min):
  - Target ≤ 1.35 post-weighting (vs ~1.8–2.2 unweighted).
- SHAP rank τ for top-10:
  - Target ≥ 0.6 week-over-week.

### 6) TL;DR playbook

1. Freeze model.
2. Rebalance via regime-aware scalers + sample weights (post-ingestion).
3. Compare error surfaces and SHAP stability.
4. If improved, retrain with regime weights and stratified folds.
5. Wire parity/SHAP-stability monitors into the Mac M4 training loop and mirror minimal metrics to BigQuery for dashboard visibility.

