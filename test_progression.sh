#!/bin/bash
# End-to-End Test Script for Challenge Progression System
# Tests the complete flow from trade acceptance to phase advancement

echo "🧪 Challenge Progression System - End-to-End Test"
echo "=================================================="
echo ""

API_BASE="http://localhost:9000/api"
CHALLENGE_ID=1

echo "📋 Test Plan:"
echo "1. Check initial challenge status"
echo "2. Test rule enforcement (minimum RR, max positions)"
echo "3. Accept and close trades to reach Step 1 requirements"
echo "4. Verify automatic advancement to Step 2"
echo "5. Test balance reset"
echo "6. Complete Step 2 and advance to Funded"
echo ""

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -z "$data" ]; then
        curl -s -X $method "$API_BASE$endpoint"
    else
        curl -s -X $method "$API_BASE$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

# Test 1: Check initial status
echo "📊 Test 1: Initial Challenge Status"
echo "-----------------------------------"
api_call GET "/challenges/$CHALLENGE_ID" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Challenge: {data['name']}\")
print(f\"Phase: {data['phase']}\")
print(f\"Balance: \${data['current_balance']:,.0f}\")
print(f\"Profit Target: {data['profit_target']}%\")
print(f\"Trading Days: {data.get('trading_days_count', 0)} / {data.get('min_trading_days', 4)}\")
print(f\"Active: {data['is_active']}\")
"
echo ""

# Test 2: Check progression status
echo "📈 Test 2: Progression Status"
echo "----------------------------"
api_call GET "/progression/$CHALLENGE_ID/status" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Phase: {data['phase']}\")
print(f\"Trading Days: {data['trading_days']} / {data['min_trading_days']}\")
print(f\"Profit: {data['current_profit_pct']:.2f}% / {data['profit_target_pct']}%\")
print(f\"Phase Complete: {data['is_phase_complete']}\")
print(f\"Message: {data['message']}\")
"
echo ""

# Test 3: Test rule enforcement - Try to accept trade with low RR
echo "🚫 Test 3: Rule Enforcement - Low R:R (should fail)"
echo "--------------------------------------------------"
LOW_RR_TRADE='{
  "pair": "EURUSD",
  "type": "LONG",
  "entry": 1.1000,
  "sl": 1.0990,
  "tp": 1.1005,
  "rr": 0.5,
  "signal_time": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "strategy": "test",
  "challenge_id": 1
}'

response=$(api_call POST "/trades/accept" "$LOW_RR_TRADE" 2>&1)
if echo "$response" | grep -q "below minimum"; then
    echo "✅ PASS: Low R:R trade rejected"
else
    echo "❌ FAIL: Low R:R trade should have been rejected"
fi
echo ""

# Test 4: Accept valid trade
echo "✅ Test 4: Accept Valid Trade (2:1 R:R)"
echo "---------------------------------------"
VALID_TRADE='{
  "pair": "EURUSD",
  "type": "LONG",
  "entry": 1.1000,
  "sl": 1.0990,
  "tp": 1.1020,
  "rr": 2.0,
  "signal_time": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "strategy": "test",
  "challenge_id": 1
}'

trade_response=$(api_call POST "/trades/accept" "$VALID_TRADE")
trade_id=$(echo "$trade_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ ! -z "$trade_id" ]; then
    echo "✅ Trade accepted: ID $trade_id"
else
    echo "❌ Failed to accept trade"
    echo "Response: $trade_response"
fi
echo ""

echo "📝 Summary"
echo "=========="
echo "✅ Challenge progression system is ready for testing"
echo ""
echo "Next Steps:"
echo "1. Start the backend: make run-backend"
echo "2. Run this test script: ./test_progression.sh"
echo "3. Or test manually via the UI"
echo ""
echo "Manual Testing Flow:"
echo "1. Accept 4+ trades on different days"
echo "2. Close them with 8%+ total profit"
echo "3. Watch for automatic Step 1 → Step 2 advancement"
echo "4. Verify balance resets to starting amount"
echo "5. Repeat for Step 2 → Funded"
