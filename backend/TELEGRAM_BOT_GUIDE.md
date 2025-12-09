# Telegram Bot Usage Guide

## Setup

1. **Environment Variables** (already configured in `.env`):

   ```
   TELEGRAM_BOT_TOKEN=7967234670:AAHozk8HtbOx_vbVpQs82BBtXagHLAk6JzE
   TELEGRAM_CHAT_ID=5712028307
   API_BASE_URL=http://localhost:8000/api
   ```

2. **Install Dependencies**:
   ```bash
   pip install python-telegram-bot
   ```

## Running the Bot

### Option 1: Interactive Bot (Manual Commands)

Start the bot and interact with it via commands:

```bash
cd backend
python3 telegram_bot.py
```

Then in Telegram, send:

- `/start` - Initialize bot
- `/status` - Check connection and stats
- `/signals` - Get current signals manually

### Option 2: Signal Monitor (Automatic Alerts)

Automatically check for new signals every minute and send alerts:

```bash
cd backend
python3 signal_monitor.py
```

This will:

- Check `/api/analysis/signals` every 60 seconds
- Send new signals to your Telegram
- Show Accept/Decline buttons

## How It Works

1. **Signal Generation**: Backend generates signals via `/api/analysis/signals`
2. **Monitor**: `signal_monitor.py` polls the API every minute
3. **Alert**: New signals are sent to your Telegram with buttons
4. **Action**: You tap "Accept" or "Decline"
5. **Journal**: Accepted trades are saved via `/api/trades/accept`

## Testing

1. **Start Backend**:

   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start Signal Monitor**:

   ```bash
   python3 signal_monitor.py
   ```

3. **Generate Test Signal** (optional):
   You can manually trigger a signal by calling the API or waiting for the strategy to detect one.

## Next Steps

- [ ] Test with live cTrader data
- [ ] Add chart screenshots to alerts
- [ ] Implement trade execution via cTrader
