"""
Signal Monitor Service
Periodically checks for new trading signals and sends them to Telegram
"""
import asyncio
import requests
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot import TradingSignalBot

class SignalMonitor:
    def __init__(self, default_interval=300, active_interval=60):
        """
        Args:
            default_interval: Seconds between checks when no signals (default: 300 = 5 min)
            active_interval: Seconds between checks when signals are active (default: 60 = 1 min)
        """
        self.default_interval = default_interval
        self.active_interval = active_interval
        self.current_interval = default_interval
        self.api_base = os.getenv('API_BASE_URL', 'http://localhost:9000/api')
        self.bot = TradingSignalBot()
        self.sent_signals = set()  # Track sent signals to avoid duplicates
        
    async def check_for_signals(self):
        """Check API for new signals"""
        try:
            # Fetch current signals from API
            response = requests.get(
                f"{self.api_base}/analysis/signals",
                params={'strategy': 'human-trained'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                signals = data.get('signals', [])
                
                # Adaptive polling: If signals exist, check more frequently
                if signals:
                    self.current_interval = self.active_interval
                    print(f"⚡ Active signals detected - switching to {self.active_interval}s polling")
                else:
                    self.current_interval = self.default_interval
                
                # Send new signals
                for signal in signals:
                    signal_id = f"{signal.get('symbol')}_{signal.get('entry')}_{signal.get('time')}"
                    
                    if signal_id not in self.sent_signals:
                        print(f"📤 New signal detected: {signal.get('type')} {signal.get('symbol')}")
                        await self.bot.send_signal_alert(signal)
                        self.sent_signals.add(signal_id)
                        
                        # Limit cache size
                        if len(self.sent_signals) > 100:
                            self.sent_signals.clear()
                
                return len(signals)
            else:
                print(f"⚠️ API returned status {response.status_code}")
                return 0
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to API at {self.api_base}")
            print(f"   Make sure backend is running: make back")
            return 0
        except Exception as e:
            print(f"❌ Error checking signals: {e}")
            return 0
    
    async def run(self):
        """Run the signal monitor"""
        print(f"🔍 Signal Monitor started")
        print(f"   API: {self.api_base}")
        print(f"   Default polling: {self.default_interval}s")
        print(f"   Active polling: {self.active_interval}s")
        print(f"   Telegram: {self.bot.chat_id}")
        
        # Initialize bot application
        from telegram.ext import Application
        self.bot.application = Application.builder().token(self.bot.bot_token).build()
        await self.bot.application.initialize()
        await self.bot.application.start()
        
        try:
            while True:
                signal_count = await self.check_for_signals()
                if signal_count > 0:
                    print(f"✅ Active signals: {signal_count} (polling every {self.current_interval}s)")
                else:
                    print(f"💤 No signals (next check in {self.current_interval}s)")
                
                await asyncio.sleep(self.current_interval)
        except KeyboardInterrupt:
            print("\n🛑 Signal monitor stopped")
        finally:
            await self.bot.application.stop()
            await self.bot.application.shutdown()

async def main():
    """Main entry point"""
    # Check environment variables
    if not os.getenv('TELEGRAM_BOT_TOKEN') or not os.getenv('TELEGRAM_CHAT_ID'):
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Looking for .env file...")
        return
    
    # Start monitor with adaptive polling
    monitor = SignalMonitor(
        default_interval=300,  # 5 minutes when idle
        active_interval=60      # 1 minute when signals active
    )
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())
