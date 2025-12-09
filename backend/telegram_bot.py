"""
Telegram Bot for SMC Trading Signals
Sends real-time signal alerts with interactive Accept/Decline buttons
"""
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:9000/api')

class TradingSignalBot:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.api_base = API_BASE_URL
        self.application = None
        
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
            # Check API connection
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
        """Handle /signals command - fetch and display current signals"""
        try:
            # Fetch signals from API
            response = requests.get(f"{self.api_base}/analysis/signals", timeout=10)
            if response.status_code == 200:
                data = response.json()
                signals = data.get('signals', [])
                
                if not signals:
                    await update.message.reply_text("📭 No active signals at the moment")
                    return
                
                for signal in signals[:5]:  # Show max 5 signals
                    await self.send_signal_alert(signal, update.message.chat_id)
            else:
                await update.message.reply_text("⚠️ Failed to fetch signals")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def send_signal_alert(self, signal: dict, chat_id: str = None):
        """Send a signal alert with Accept/Decline buttons"""
        target_chat = chat_id or self.chat_id
        
        # Format signal message
        signal_type = signal.get('type', 'UNKNOWN')
        pair = signal.get('symbol', signal.get('pair', 'UNKNOWN'))
        entry = signal.get('entry', signal.get('price', 0))
        sl = signal.get('sl', 0)
        tp = signal.get('tp', 0)
        rr = signal.get('rr', 0)
        structure = signal.get('structure', 'N/A')
        time = signal.get('time', datetime.now().isoformat())
        
        # Calculate pips
        pip_size = 0.0001 if 'JPY' not in pair else 0.01
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
            f"🕐 Time: {time}\n"
        )
        
        # Create inline keyboard with Accept/Decline buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{pair}_{entry}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline_{pair}_{entry}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message
        await self.application.bot.send_message(
            chat_id=target_chat,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button presses (Accept/Decline)"""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        parts = query.data.split('_')
        action = parts[0]
        pair = parts[1]
        entry_str = '_'.join(parts[2:])  # Handle cases where entry has underscores
        
        if action == 'accept':
            # Parse signal data from the message text
            try:
                message_text = query.message.text
                lines = message_text.split('\n')
                
                # Extract values from formatted message
                signal_data = {'symbol': pair}
                
                for line in lines:
                    if 'Entry:' in line:
                        signal_data['entry'] = float(line.split('`')[1])
                    elif 'SL:' in line:
                        signal_data['sl'] = float(line.split('`')[1])
                    elif 'TP:' in line:
                        signal_data['tp'] = float(line.split('`')[1])
                    elif 'R:R:' in line:
                        signal_data['rr'] = float(line.split('`')[1])
                    elif signal_data.get('type') is None:
                        # Extract type from first line (e.g., "🟢 *LONG EURUSD*")
                        if 'LONG' in line:
                            signal_data['type'] = 'LONG'
                        elif 'SHORT' in line:
                            signal_data['type'] = 'SHORT'
                
                # Validate we have required fields
                required = ['symbol', 'entry', 'sl', 'tp', 'type']
                if not all(k in signal_data for k in required):
                    raise ValueError(f"Missing required fields. Got: {signal_data.keys()}")
                
                # Call API to accept the signal
                response = requests.post(
                    f"{self.api_base}/trades/accept",
                    json=signal_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    trade_data = response.json()
                    await query.edit_message_text(
                        text=f"{query.message.text}\n\n✅ *Trade Accepted!*\n"
                             f"Trade ID: {trade_data.get('id', 'N/A')}\n"
                             f"Check your Journal for details.",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        text=f"{query.message.text}\n\n⚠️ Failed to accept trade\n"
                             f"Status: {response.status_code}\n"
                             f"Error: {response.text[:100]}",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                await query.edit_message_text(
                    text=f"{query.message.text}\n\n❌ Error accepting trade:\n{str(e)[:100]}",
                    parse_mode='Markdown'
                )
        
        elif action == 'decline':
            await query.edit_message_text(
                text=f"{query.message.text}\n\n❌ *Trade Declined*",
                parse_mode='Markdown'
            )
    
    async def start_bot(self):
        """Start the Telegram bot"""
        print(f"🤖 Starting Telegram Bot...")
        print(f"   Bot Token: {self.bot_token[:20]}...")
        print(f"   Chat ID: {self.chat_id}")
        
        # Create application
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Start polling
        print("✅ Bot is running! Send /start to begin.")
        await self.application.run_polling()

async def main():
    """Main entry point"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        return
    
    bot = TradingSignalBot()
    await bot.start_bot()

if __name__ == "__main__":
    asyncio.run(main())
