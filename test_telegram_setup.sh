#!/bin/bash
# Quick test script to verify Telegram bot setup

echo "🔍 Checking Telegram Bot Setup..."
echo ""

# 1. Check if backend is running
echo "1️⃣ Checking backend..."
if curl -s http://localhost:9000/api/stats/summary > /dev/null 2>&1; then
    echo "✅ Backend is running on port 9000"
else
    echo "❌ Backend is NOT running"
    echo "   Start it with: make back"
    echo ""
    exit 1
fi

# 2. Check env variables
echo ""
echo "2️⃣ Checking environment..."
cd backend
if [ -f .env ]; then
    if grep -q "TELEGRAM_BOT_TOKEN" .env && grep -q "TELEGRAM_CHAT_ID" .env; then
        echo "✅ .env file exists with Telegram credentials"
    else
        echo "❌ .env missing Telegram credentials"
        exit 1
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

# 3. Test signal send
echo ""
echo "3️⃣ Sending test signal..."
python3 test_telegram_bot.py
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All checks passed!"
    echo ""
    echo "📱 Check your Telegram and tap 'Accept'"
    echo "   Then verify at: http://localhost:9000/api/trades/"
else
    echo "❌ Test failed"
    exit 1
fi
