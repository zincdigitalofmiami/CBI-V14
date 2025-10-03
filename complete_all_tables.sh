#!/bin/bash
echo "Creating ALL pipeline tables..."

# 1. GEOPOLITICAL & TRADE RELATIONS
bq mk -t cbi-v13:raw.china_trade_relations date:DATE,tariff_rate:FLOAT64,quota_volume:FLOAT64,trade_war_status:STRING
bq mk -t cbi-v13:raw.us_china_phase_deals date:DATE,agreement_status:STRING,impact_score:FLOAT64
bq mk -t cbi-v13:raw.brazil_china_agreements date:DATE,trade_volume:FLOAT64,preference_status:STRING
bq mk -t cbi-v13:raw.india_import_policies date:DATE,palm_duty:FLOAT64,soy_duty:FLOAT64
bq mk -t cbi-v13:raw.indonesia_export_policies date:DATE,palm_export_tax:FLOAT64,quota:FLOAT64
bq mk -t cbi-v13:raw.malaysia_export_policies date:DATE,palm_export_tax:FLOAT64,production:FLOAT64

# 2. BIOFUELS & ENERGY COMPLEX
bq mk -t cbi-v13:raw.rfs_mandates date:DATE,rvo_volume:FLOAT64,d4_rin_price:FLOAT64
bq mk -t cbi-v13:raw.biodiesel_blending_rates date:DATE,b20_mandate:FLOAT64,b30_mandate:FLOAT64,b100_demand:FLOAT64
bq mk -t cbi-v13:raw.saf_aviation_fuel date:DATE,saf_demand:FLOAT64,saf_premium:FLOAT64
bq mk -t cbi-v13:raw.renewable_diesel_capacity date:DATE,capacity_mgpy:FLOAT64,utilization_rate:FLOAT64
bq mk -t cbi-v13:raw.carbon_credit_markets date:DATE,credit_price:FLOAT64,volume_traded:FLOAT64
bq mk -t cbi-v13:raw.crude_oil_correlation date:DATE,wti_price:FLOAT64,correlation_coefficient:FLOAT64
bq mk -t cbi-v13:raw.natural_gas_prices date:DATE,henry_hub:FLOAT64,ttf_europe:FLOAT64

# 3. LOBBYING & POLICY INTELLIGENCE
bq mk -t cbi-v13:raw.farm_bill_negotiations date:DATE,subsidy_level:FLOAT64,crop_insurance_changes:STRING
bq mk -t cbi-v13:raw.nopa_lobbying_positions date:DATE,issue:STRING,position:STRING,lobbying_spend:FLOAT64
bq mk -t cbi-v13:raw.usda_policy_changes date:DATE,policy_area:STRING,change_description:STRING
bq mk -t cbi-v13:raw.epa_regulations date:DATE,regulation_name:STRING,status:STRING,compliance_cost:FLOAT64
bq mk -t cbi-v13:raw.congressional_ag_committee date:DATE,member:STRING,position:STRING,vote:STRING
bq mk -t cbi-v13:raw.state_biofuel_mandates date:DATE,state:STRING,mandate_level:FLOAT64,lcfs_price:FLOAT64

# 4. GLOBAL SUPPLY CHAIN
bq mk -t cbi-v13:raw.brazil_planted_area date:DATE,hectares:FLOAT64,yield_estimate:FLOAT64
bq mk -t cbi-v13:raw.brazil_weather_complete date:DATE,region:STRING,rainfall:FLOAT64,temperature:FLOAT64
bq mk -t cbi-v13:raw.brazil_harvest_progress date:DATE,percent_complete:FLOAT64,weekly_pace:FLOAT64
bq mk -t cbi-v13:raw.brazil_logistics date:DATE,br163_freight:FLOAT64,santos_queue:INT64,paranagua_capacity:FLOAT64
bq mk -t cbi-v13:raw.brazil_farmer_selling date:DATE,percent_sold:FLOAT64,average_price:FLOAT64
bq mk -t cbi-v13:raw.argentina_everything date:DATE,production:FLOAT64,exports:FLOAT64,fx_rate:FLOAT64
bq mk -t cbi-v13:raw.paraguay_uruguay date:DATE,combined_production:FLOAT64,export_volume:FLOAT64
bq mk -t cbi-v13:raw.ukraine_production date:DATE,sunflower_production:FLOAT64,grain_exports:FLOAT64
bq mk -t cbi-v13:raw.canada_canola date:DATE,production:FLOAT64,crush_volume:FLOAT64

# 5. CHINA - THE PRICE SETTER
bq mk -t cbi-v13:raw.china_sow_herd_size date:DATE,herd_size_millions:FLOAT64,yoy_change:FLOAT64
bq mk -t cbi-v13:raw.china_asf_status date:DATE,outbreak_count:INT64,provinces_affected:INT64
bq mk -t cbi-v13:raw.china_reserve_releases date:DATE,volume_released:FLOAT64,commodity:STRING
bq mk -t cbi-v13:raw.china_crushing_margins date:DATE,margin_yuan_per_ton:FLOAT64
bq mk -t cbi-v13:raw.china_port_inventory date:DATE,inventory_mmt:FLOAT64,days_supply:FLOAT64
bq mk -t cbi-v13:raw.china_economic_data date:DATE,gdp_growth:FLOAT64,pork_consumption:FLOAT64

# 6. US DOMESTIC MARKET
bq mk -t cbi-v13:raw.usda_wasde_complete date:DATE,crop:STRING,production:FLOAT64,exports:FLOAT64,ending_stocks:FLOAT64
bq mk -t cbi-v13:raw.crop_progress_reports date:DATE,state:STRING,crop:STRING,planted_pct:FLOAT64,condition:STRING
bq mk -t cbi-v13:raw.nass_production_estimates date:DATE,state:STRING,yield_bushels:FLOAT64,production_bushels:FLOAT64
bq mk -t cbi-v13:raw.fsa_prevented_planting date:DATE,state:STRING,prevented_acres:FLOAT64,reason:STRING
bq mk -t cbi-v13:raw.export_sales_weekly date:DATE,destination:STRING,commodity:STRING,current_sales:FLOAT64
bq mk -t cbi-v13:raw.export_inspections date:DATE,commodity:STRING,destination:STRING,volume_mt:FLOAT64
bq mk -t cbi-v13:raw.crush_weekly date:DATE,soybeans_crushed:FLOAT64,oil_produced:FLOAT64,meal_produced:FLOAT64
bq mk -t cbi-v13:raw.stocks_quarterly date:DATE,commodity:STRING,on_farm:FLOAT64,off_farm:FLOAT64

# 7. PROCESSING & LOGISTICS
bq mk -t cbi-v13:raw.adm_operations date:DATE,plant_location:STRING,status:STRING,capacity_utilization:FLOAT64
bq mk -t cbi-v13:raw.bunge_operations date:DATE,plant_location:STRING,crush_capacity:FLOAT64,oil_yield:FLOAT64
bq mk -t cbi-v13:raw.cargill_operations date:DATE,plant_location:STRING,maintenance_type:STRING,duration_days:FLOAT64
bq mk -t cbi-v13:raw.louis_dreyfus date:DATE,market_position:STRING,volume_contracted:FLOAT64
bq mk -t cbi-v13:raw.rail_freight_rates date:DATE,origin:STRING,destination:STRING,rate_per_car:FLOAT64
bq mk -t cbi-v13:raw.barge_rates date:DATE,river_segment:STRING,rate_per_ton:FLOAT64,queue_days:FLOAT64
bq mk -t cbi-v13:raw.truck_availability date:DATE,region:STRING,availability_index:FLOAT64,spot_rate:FLOAT64
bq mk -t cbi-v13:raw.storage_capacity date:DATE,location:STRING,total_capacity:FLOAT64,current_usage:FLOAT64

# 8. WEATHER - GLOBAL COMPREHENSIVE
bq mk -t cbi-v13:raw.noaa_complete date:DATE,region:STRING,temp_max:FLOAT64,temp_min:FLOAT64,precip_mm:FLOAT64
bq mk -t cbi-v13:raw.ecmwf_models date:DATE,region:STRING,forecast_precip:FLOAT64,forecast_temp:FLOAT64
bq mk -t cbi-v13:raw.brazil_inmet date:DATE,state:STRING,rainfall_mm:FLOAT64,temp_celsius:FLOAT64
bq mk -t cbi-v13:raw.argentina_smn date:DATE,province:STRING,rainfall_mm:FLOAT64,frost_risk:BOOL
bq mk -t cbi-v13:raw.enso_status date:DATE,nino_index:FLOAT64,phase:STRING,forecast_3month:STRING
bq mk -t cbi-v13:raw.soil_moisture date:DATE,region:STRING,moisture_pct:FLOAT64,drought_category:STRING
bq mk -t cbi-v13:raw.precipitation_outlooks date:DATE,region:STRING,prob_above:FLOAT64,prob_normal:FLOAT64,prob_below:FLOAT64

# 9. FINANCIAL FLOWS
bq mk -t cbi-v13:raw.cftc_cot_reports date:DATE,contract:STRING,managed_money_long:INT64,managed_money_short:INT64
bq mk -t cbi-v13:raw.ice_positions date:DATE,contract:STRING,open_interest:INT64,volume:INT64
bq mk -t cbi-v13:raw.options_flow date:DATE,strike:FLOAT64,expiry:DATE,put_volume:INT64,call_volume:INT64
bq mk -t cbi-v13:raw.index_fund_rolls date:DATE,old_month:STRING,new_month:STRING,volume_rolled:INT64
bq mk -t cbi-v13:raw.managed_money_positions date:DATE,net_position:INT64,position_change:INT64
bq mk -t cbi-v13:raw.commercial_hedging date:DATE,hedger_type:STRING,long_hedges:INT64,short_hedges:INT64

# 10. ALTERNATIVE DATA
bq mk -t cbi-v13:raw.satellite_crop_health date:DATE,region:STRING,ndvi_index:FLOAT64,crop_stage:STRING
bq mk -t cbi-v13:raw.vessel_tracking date:DATE,vessel_name:STRING,origin:STRING,destination:STRING,tonnage:FLOAT64
bq mk -t cbi-v13:raw.google_trends date:DATE,search_term:STRING,search_volume:INT64
bq mk -t cbi-v13:raw.social_sentiment date:DATE,platform:STRING,sentiment_score:FLOAT64,mention_count:INT64

# 11. SUBSTITUTE PRODUCTS
bq mk -t cbi-v13:raw.palm_oil_complete date:DATE,malaysia_production:FLOAT64,indonesia_production:FLOAT64,price_myr:FLOAT64
bq mk -t cbi-v13:raw.sunflower_oil date:DATE,ukraine_production:FLOAT64,russia_production:FLOAT64,price_usd:FLOAT64
bq mk -t cbi-v13:raw.rapeseed_oil date:DATE,eu_production:FLOAT64,canada_production:FLOAT64,price_eur:FLOAT64
bq mk -t cbi-v13:raw.corn_oil date:DATE,us_production:FLOAT64,ethanol_coproduct:FLOAT64,price_usd:FLOAT64
bq mk -t cbi-v13:raw.cottonseed_oil date:DATE,us_production:FLOAT64,regional_crush:FLOAT64,price_usd:FLOAT64

# 12. FOOD INDUSTRY DEMAND
bq mk -t cbi-v13:raw.restaurant_sales date:DATE,sales_index:FLOAT64,traffic_index:FLOAT64,oil_usage_estimate:FLOAT64
bq mk -t cbi-v13:raw.qsr_expansion date:DATE,chain_name:STRING,new_stores:INT64,oil_demand_impact:FLOAT64
bq mk -t cbi-v13:raw.food_manufacturing date:DATE,sector:STRING,production_index:FLOAT64,oil_usage:FLOAT64
bq mk -t cbi-v13:raw.consumer_trends date:DATE,trend_name:STRING,impact_score:FLOAT64

# 13. TECHNICAL MARKET DATA
bq mk -t cbi-v13:raw.all_futures_contracts date:DATE,month:STRING,price:FLOAT64,volume:INT64,open_interest:INT64
bq mk -t cbi-v13:raw.calendar_spreads date:DATE,near_month:STRING,far_month:STRING,spread_value:FLOAT64
bq mk -t cbi-v13:raw.inter_commodity_spreads date:DATE,spread_type:STRING,value:FLOAT64,zsm_ratio:FLOAT64
bq mk -t cbi-v13:raw.basis_all_locations date:DATE,location:STRING,basis_value:FLOAT64
bq mk -t cbi-v13:raw.volatility_surface date:DATE,strike:FLOAT64,expiry:DATE,implied_vol:FLOAT64

# 14. REGULATORY & COMPLIANCE
bq mk -t cbi-v13:raw.food_safety_regulations date:DATE,regulation:STRING,status:STRING,compliance_date:DATE
bq mk -t cbi-v13:raw.gmo_approvals date:DATE,trait:STRING,country:STRING,approval_status:STRING
bq mk -t cbi-v13:raw.sustainability_rules date:DATE,rule_name:STRING,region:STRING,impact_level:STRING
bq mk -t cbi-v13:raw.carbon_footprint_regs date:DATE,regulation:STRING,carbon_price:FLOAT64

# 15. CURRENCY IMPACTS
bq mk -t cbi-v13:raw.usd_index date:DATE,dxy_value:FLOAT64,daily_change:FLOAT64
bq mk -t cbi-v13:raw.brl_real date:DATE,usdbrl_rate:FLOAT64,volatility:FLOAT64
bq mk -t cbi-v13:raw.ars_peso date:DATE,usdars_rate:FLOAT64,blue_rate:FLOAT64
bq mk -t cbi-v13:raw.cny_yuan date:DATE,usdcny_rate:FLOAT64,offshore_rate:FLOAT64
bq mk -t cbi-v13:raw.inr_rupee date:DATE,usdinr_rate:FLOAT64,rbi_intervention:FLOAT64

echo "All 100+ tables created"
