#!/bin/bash
# Verify no fake data remains

echo "Verifying no fake data remains..."

# Check for random usage
echo "Checking for random usage..."
grep -r "np.random\|random.rand\|random.uniform" scripts/ src/ --include="*.py" \
  | grep -v "^#" \
  | grep -v "REMOVED" \
  | grep -v "scripts/audits/REMOVE_ALL_FAKE_DATA.py" \
  | grep -v "scripts/REMOVE_ALL_FAKE_DATA_NOW.py" \
  | grep -v "np.random.seed" \
  | grep -v "random.seed"

if [ $? -eq 0 ]; then
    echo "❌ FAKE DATA STILL EXISTS!"
    exit 1
else
    echo "✅ No random data generation found"
fi

# Check for mock/dummy/fake keywords
echo "Checking for mock/dummy/fake keywords (ingest code only)..."
# Limit scan to ingestion code paths where generation could occur
grep -r "mock_\|dummy_\|fake_\|placeholder\|synthetic" scripts/ingest src/ingestion --include="*.py" \
  | sed -e 's/^[^:]*://' \
  | grep -v "^[[:space:]]*#" \
  | grep -v "REMOVED"

if [ $? -eq 0 ]; then
    echo "❌ MOCK DATA STILL EXISTS!"
    exit 1
else
    echo "✅ No mock data found"
fi

echo "✅ VERIFICATION COMPLETE - NO FAKE DATA DETECTED"
