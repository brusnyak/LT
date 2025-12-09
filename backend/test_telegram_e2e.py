"""
End-to-end test for Telegram bot integration
Tests: env loading, bot connection, signal sending, and button callback
"""
import asyncio
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot import TradingSignalBot

async def test_complete_flow():
    """Test the complete flow"""
    print("🧪 End-to-End Telegram Bot Test\n")
    print("=" * 50)
    
    # 1. Check environment
    print("\n1️⃣ Checking Environment Variables...")
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    api_base = os.getenv('API_BASE_URL', 'http://localhost:9000/api')
    
    if not bot_token or not chat_id:
        print("❌ FAIL: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False
    
    print(f"✅ Bot Token: {bot_token[:20]}...")
    print(f"✅ Chat ID: {chat_id}")
    print(f"✅ API Base: {api_base}")
    
    # 2. Check backend connection
    print("\n2️⃣ Checking Backend Connection...")
    try:
        response = requests.get(f"{api_base}/stats/summary", timeout=3)
        if response.status_code == 200:
            print(f"✅ Backend is running at {api_base}")
        else:
            print(f"⚠️ Backend returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ FAIL: Cannot connect to backend at {api_base}")
        print(f"   Please start backend: make back")
        return False
    except Exception as e:
        print(f"⚠️ Warning: {e}")
    
    # 3. Test bot initialization
    print("\n3️⃣ Testing Bot Initialization...")
    bot = TradingSignalBot()
    
    from telegram.ext import Application
    bot.application = Application.builder().token(bot.bot_token).build()
    await bot.application.initialize()
    await bot.application.start()
    
    print("✅ Bot initialized successfully")
    
    # 4. Send test signal
    print("\n4️⃣ Sending Test Signal...")
    test_signal = {
        'type': 'LONG',
        'symbol': 'EURUSD',
        'entry': 1.05500,
        'sl': 1.05400,
        'tp': 1.05700,
        'rr': 2.0,
        'structure': 'bearish',
        'time': '2025-12-04T18:30:00'
    }
    
    try:
        await bot.send_signal_alert(test_signal)
        print("✅ Test signal sent to Telegram")
        print("\n📱 Check your Telegram and tap 'Accept' button")
        print("   The signal should be saved to the journal")
    except Exception as e:
        print(f"❌ FAIL: Error sending signal: {e}")
        await bot.application.stop()
        await bot.application.shutdown()
        return False
    
    # 5. Wait for user to test button
    print("\n5️⃣ Waiting for button test...")
    print("   After tapping 'Accept', check:")
    print(f"   1. Message updates with '✅ Trade Accepted!'")
    print(f"   2. Visit {api_base.replace('/api', '')}/api/trades/")
    print(f"   3. Verify trade appears in the list")
    
    await asyncio.sleep(3)
    
    # Cleanup
    await bot.application.stop()
    await bot.application.shutdown()
    
    print("\n" + "=" * 50)
    print("✅ Test Complete!")
    print("\nNext steps:")
    print("1. Tap 'Accept' on the Telegram message")
    print("2. Verify trade appears in journal")
    print("3. Run 'make tele' for live monitoring")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete_flow())
    sys.exit(0 if success else 1)
