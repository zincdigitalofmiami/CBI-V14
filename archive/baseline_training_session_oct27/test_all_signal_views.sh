#!/bin/bash
# Test all signal views for errors
# No shortcuts - check EVERYTHING

echo "TESTING ALL SIGNAL VIEWS"
echo "========================"
echo ""

views=(
  "vw_vix_stress_signal"
  "vw_harvest_pace_signal"
  "vw_china_relations_signal"
  "vw_tariff_threat_signal"
  "vw_geopolitical_volatility_signal"
  "vw_biofuel_cascade_signal"
  "vw_hidden_correlation_signal"
  "vw_biofuel_ethanol_signal"
  "vw_bear_market_regime"
  "vw_supply_glut_indicator"
  "vw_trade_war_impact"
  "vw_biofuel_policy_intensity"
)

broken_views=()
working_views=()

for view in "${views[@]}"; do
  echo "Testing: $view"
  
  result=$(bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) as cnt FROM \`cbi-v14.signals.$view\` LIMIT 1" 2>&1)
  
  if echo "$result" | grep -q "Error"; then
    echo "  ❌ BROKEN: $result" | head -2
    broken_views+=("$view")
  else
    count=$(echo "$result" | tail -1)
    echo "  ✅ Working: $count rows"
    working_views+=("$view")
  fi
  echo ""
done

echo "========================"
echo "SUMMARY"
echo "========================"
echo "Working views: ${#working_views[@]}"
echo "Broken views: ${#broken_views[@]}"
echo ""

if [ ${#broken_views[@]} -gt 0 ]; then
  echo "BROKEN VIEWS:"
  for view in "${broken_views[@]}"; do
    echo "  - $view"
  done
  exit 1
else
  echo "✅ ALL VIEWS WORKING"
  exit 0
fi

