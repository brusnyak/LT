"""
Quick test script for Telegram bot
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot import TradingSignalBot

async def test_bot():
    """Test bot connection and send a test signal"""
    print("🧪 Testing Telegram Bot\n")
    
    # Check environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        return
    
    print(f"✅ Bot Token: {bot_token[:20]}...")
    print(f"✅ Chat ID: {chat_id}\n")
    
    # Create bot instance
    bot = TradingSignalBot()
    
    # Initialize application
    from telegram.ext import Application
    bot.application = Application.builder().token(bot.bot_token).build()
    await bot.application.initialize()
    await bot.application.start()
    
    try:
        # Send test signal
        test_signal = {
            'type': 'LONG',
            'symbol': 'EURUSD',
            'entry': 1.05500,
            'sl': 1.05400,
            'tp': 1.05700,
            'rr': 2.0,
            'structure': 'bearish',
            'time': '2025-12-04T18:00:00'
        }
        
        print("📤 Sending test signal to Telegram...")
        await bot.send_signal_alert(test_signal)
        print("✅ Test signal sent! Check your Telegram.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.application.stop()
        await bot.application.shutdown()

if __name__ == "__main__":
    asyncio.run(test_bot())
