#!/bin/bash
# Test script for CBI-V14 Dashboard API routes

API_BASE_URL="${1:-http://localhost:3000}"

echo "=================================="
echo "CBI-V14 Dashboard API Test Suite"
echo "=================================="
echo "Testing API: $API_BASE_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test health endpoint
echo "1. Testing Health Endpoint..."
HEALTH_RESPONSE=$(curl -s "$API_BASE_URL/api/health")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Health endpoint responding${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Health endpoint failed${NC}"
fi
echo ""

# Test 1W forecast
echo "2. Testing 1W Forecast (AutoML V4)..."
FORECAST_1W_RESPONSE=$(curl -s "$API_BASE_URL/api/v4/forecast/1w?model_type=automl_v4")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 1W forecast responding${NC}"
    echo "Response: $FORECAST_1W_RESPONSE"
else
    echo -e "${RED}✗ 1W forecast failed${NC}"
fi
echo ""

# Test 1M forecast
echo "3. Testing 1M Forecast (AutoML V4)..."
FORECAST_1M_RESPONSE=$(curl -s "$API_BASE_URL/api/v4/forecast/1m?model_type=automl_v4")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 1M forecast responding${NC}"
    echo "Response: $FORECAST_1M_RESPONSE"
else
    echo -e "${RED}✗ 1M forecast failed${NC}"
fi
echo ""

# Test 3M forecast
echo "4. Testing 3M Forecast (AutoML V4)..."
FORECAST_3M_RESPONSE=$(curl -s "$API_BASE_URL/api/v4/forecast/3m?model_type=automl_v4")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 3M forecast responding${NC}"
    echo "Response: $FORECAST_3M_RESPONSE"
else
    echo -e "${RED}✗ 3M forecast failed${NC}"
fi
echo ""

# Test 6M forecast (fallback to V3)
echo "5. Testing 6M Forecast (Boosted V3 fallback)..."
FORECAST_6M_RESPONSE=$(curl -s "$API_BASE_URL/api/v4/forecast/6m?model_type=boosted_v3")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 6M forecast responding${NC}"
    echo "Response: $FORECAST_6M_RESPONSE"
else
    echo -e "${RED}✗ 6M forecast failed${NC}"
fi
echo ""

echo "=================================="
echo "Test suite completed!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. If tests pass locally, deploy to Vercel: vercel --prod"
echo "2. Run tests against production: ./test-api.sh https://cbi-dashboard.vercel.app"
echo "3. Check Vercel logs if any issues: vercel logs"




