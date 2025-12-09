"""
Combined Signal Monitor + Bot
Runs the Telegram bot with active polling AND monitors for signals
This allows button callbacks to work properly
"""
import asyncio
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:9000/api')


class SignalBot:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_base = API_BASE_URL
        self.sent_signals = set()  # Track sent signals
        self.check_interval = 300  # Default 5 min
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 *SMC Trading Signal Bot*\n\n"
            "I'll send you trading signals as they're generated.\n\n"
            "Commands:\n"
            "/start - Show this message\n"
            "/status - Check bot status\n"
            "/signals - Get latest signals",
            parse_mode='Markdown'
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            response = requests.get(f"{self.api_base}/stats/summary", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                await update.message.reply_text(
                    f"✅ *Bot Status: Active*\n\n"
                    f"API: Connected\n"
                    f"Total Trades: {stats.get('total_trades', 0)}\n"
                    f"Win Rate: {stats.get('win_rate', 0):.1f}%",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("⚠️ API connection issue")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command"""
        await self.check_and_send_signals(context.application)
        await update.message.reply_text("✅ Checked for new signals")
    
    async def send_signal_alert(self, application, signal: dict):
        """Send a signal alert with Accept/Decline buttons"""
        signal_type = signal.get('type', 'UNKNOWN')
        pair = signal.get('pair', signal.get('symbol', 'UNKNOWN'))
        entry = signal.get('entry', 0)
        sl = signal.get('sl', 0)
        tp = signal.get('tp', 0)
        rr = signal.get('rr', 0)
        structure = signal.get('structure', 'N/A')
        time_str = signal.get('time', datetime.now().isoformat())
        
        pip_size = 0.0001 if 'JPY' not in pair and 'XAU' not in pair else 0.01
        sl_pips = abs(entry - sl) / pip_size
        tp_pips = abs(tp - entry) / pip_size
        
        emoji = "🟢" if signal_type == "LONG" else "🔴"
        
        message = (
            f"{emoji} *{signal_type} {pair}*\n\n"
            f"📍 Entry: `{entry:.5f}`\n"
            f"🛑 SL: `{sl:.5f}` ({sl_pips:.1f} pips)\n"
            f"🎯 TP: `{tp:.5f}` ({tp_pips:.1f} pips)\n"
            f"📊 R:R: `{rr:.2f}`\n"
            f"📈 Structure: {structure}\n"
            f"🕐 Time: {time_str}\n"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{pair}_{entry}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline_{pair}_{entry}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await application.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Accept/Decline button presses"""
        query = update.callback_query
        await query.answer()  # Acknowledge the button press
        
        parts = query.data.split('_')
        action = parts[0]
        pair = parts[1]
        
        if action == 'accept':
            try:
                message_text = query.message.text
                # Use regex to extract values robustly
                import re
                
                signal_data = {'symbol': pair}
                
                # Extract values using regex patterns
                entry_match = re.search(r"Entry:.*?(\d+\.\d+)", message_text)
                sl_match = re.search(r"SL:.*?(\d+\.\d+)", message_text)
                tp_match = re.search(r"TP:.*?(\d+\.\d+)", message_text)
                rr_match = re.search(r"R:R:.*?(\d+\.\d+)", message_text)
                time_match = re.search(r"Time: (.*?)(?:\n|$)", message_text)
                
                if entry_match: signal_data['entry'] = float(entry_match.group(1))
                if sl_match: signal_data['sl'] = float(sl_match.group(1))
                if tp_match: signal_data['tp'] = float(tp_match.group(1))
                if rr_match: signal_data['rr'] = float(rr_match.group(1))
                
                # Add required fields for backend
                signal_data['pair'] = pair  # Backend expects 'pair', not 'symbol'
                signal_data['signal_time'] = time_match.group(1).strip() if time_match else datetime.now().isoformat()
                
                # Determine type from text
                if 'LONG' in message_text:
                    signal_data['type'] = 'LONG'
                elif 'SHORT' in message_text:
                    signal_data['type'] = 'SHORT'
                
                required = ['pair', 'entry', 'sl', 'tp', 'type', 'signal_time']
                if not all(k in signal_data for k in required):
                    missing = [k for k in required if k not in signal_data]
                    raise ValueError(f"Missing fields: {missing}")
                
                response = requests.post(
                    f"{self.api_base}/trades/accept",
                    json=signal_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    trade_data = response.json()
                    await query.edit_message_text(
                        text=f"{query.message.text}\n\n✅ *Trade Accepted!*\n"
                             f"Trade ID: {trade_data.get('id', 'N/A')}",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        text=f"{query.message.text}\n\n⚠️ Failed: {response.status_code}\n{response.text[:50]}",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                print(f"Error processing callback: {e}")
                await query.edit_message_text(
                    text=f"{query.message.text}\n\n❌ Error: {str(e)[:100]}",
                    parse_mode='Markdown'
                )
        
        elif action == 'decline':
            await query.edit_message_text(
                text=f"{query.message.text}\n\n❌ *Trade Declined*",
                parse_mode='Markdown'
            )
    
    async def check_and_send_signals(self, application):
        """Check for new signals and send to Telegram"""
        try:
            response = requests.get(
                f"{self.api_base}/analysis/signals",
                params={'strategy': 'human-trained'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                signals = data.get('signals', [])
                
                for signal in signals:
                    signal_id = f"{signal.get('pair')}_{signal.get('entry')}_{signal.get('time')}"
                    
                    if signal_id not in self.sent_signals:
                        print(f"📤 New signal: {signal.get('type')} {signal.get('pair')}")
                        await self.send_signal_alert(application, signal)
                        self.sent_signals.add(signal_id)
                        
                        if len(self.sent_signals) > 100:
                            self.sent_signals.clear()
                
                return len(signals)
            else:
                print(f"⚠️ API returned {response.status_code}")
                return 0
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to {self.api_base}")
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0
    
    async def signal_checker(self, application):
        """Background task to check for signals periodically"""
        while True:
            count = await self.check_and_send_signals(application)
            if count > 0:
                print(f"✅ {count} active signals")
            else:
                print(f"💤 No new signals (next check in {self.check_interval}s)")
            await asyncio.sleep(self.check_interval)


async def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required")
        return
    
    print("🤖 Starting SMC Signal Bot")
    print(f"   API: {API_BASE_URL}")
    print(f"   Telegram: {TELEGRAM_CHAT_ID}")
    
    bot = SignalBot()
    
    # Create application
    application = Application.builder().token(bot.bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("status", bot.status_command))
    application.add_handler(CommandHandler("signals", bot.signals_command))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    
    # Initialize and start
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ Bot running! Buttons will now work.")
    print("   Send /start to the bot in Telegram")
    print("")
    
    # Run signal checker in background
    try:
        await bot.signal_checker(application)
    except KeyboardInterrupt:
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
