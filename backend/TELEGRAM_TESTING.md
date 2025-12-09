# Telegram Bot - Complete Testing Guide

## Prerequisites

1. **Backend must be running**:

   ```bash
   make back
   ```

   Backend should be accessible at http://localhost:9000

2. **Environment variables set** (already done in `.env`):
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `API_BASE_URL` (optional, defaults to http://localhost:8000/api)

## Testing Steps

### 1. Quick Test (Signal Only)

```bash
make tele-test
```

- Sends a test signal to your Telegram
- Verifies bot connection
- **Note**: Accept button won't work without backend running

### 2. Full End-to-End Test

```bash
# Terminal 1: Start backend
make back

# Terminal 2: Run E2E test
cd backend
python3 test_telegram_e2e.py
```

This will:

1. ✅ Check environment variables
2. ✅ Verify backend connection
3. ✅ Initialize bot
4. ✅ Send test signal to Telegram
5. ⏳ Wait for you to tap "Accept"

**After tapping Accept**:

- Message should update with "✅ Trade Accepted!"
- Trade ID should be shown
- Check http://localhost:9000/api/trades/ to verify

### 3. Live Monitoring

```bash
# Terminal 1: Backend
make back

# Terminal 2: Signal monitor
make tele
```

**What happens**:

- Polls `/api/analysis/signals` every 5 minutes (idle)
- Switches to 60s polling when signals are active
- Sends new signals to Telegram automatically
- You tap Accept/Decline on your phone
- Accepted trades saved to journal

## Troubleshooting

### "Error: TELEGRAM_BOT_TOKEN not set"

- Ensure `.env` file exists in `backend/` directory
- Check file has correct variables (no quotes needed)
- Try: `cd backend && cat .env | grep TELEGRAM`

### "Cannot connect to API"

- Backend not running
- Start with: `make back`
- Verify: http://localhost:9000/docs

### "Accept button does nothing"

- Backend must be running for button to work
- Check backend logs for errors
- Verify `/api/trades/accept` endpoint exists

### "No signals generated"

- Strategy requires trending market
- Current data may be ranging
- Test with: `make tele-test` (sends fake signal)

## Expected Behavior

### Signal Message Format

```
🟢 LONG EURUSD

📍 Entry: 1.05500
🛑 SL: 1.05400 (10.0 pips)
🎯 TP: 1.05700 (20.0 pips)
📊 R:R: 2.00
📈 Structure: bearish
🕐 Time: 2025-12-04T18:30:00

[✅ Accept] [❌ Decline]
```

### After Tapping Accept

```
🟢 LONG EURUSD
...

✅ Trade Accepted!
Trade ID: 123
Check your Journal for details.
```

## Adaptive Polling

The signal monitor uses smart polling:

- **Idle (no signals)**: Checks every 5 minutes
- **Active (signals exist)**: Checks every 60 seconds
- **Automatic switching**: Based on signal presence

This saves API calls while staying responsive when needed.

## Next Steps

1. ✅ Test Accept button with backend running
2. ✅ Verify trade appears in journal
3. ⏳ Integrate cTrader for live data
4. ⏳ Add automatic trade execution
