# Quick Start Guide

## Available Commands

### Full App (UI + Backend)

```bash
make -j2 run
```

Runs both frontend and backend in parallel. Access at:

- Frontend: http://localhost:4001
- Backend: http://localhost:9000

### Telegram Signal Monitor (Headless)

```bash
make tele
```

Runs signal monitoring in the background:

- Checks for signals every 60 seconds
- Sends alerts to your Telegram
- No UI needed
- Press Ctrl+C to stop

### Test Telegram Bot

```bash
make tele-test
```

Sends a test signal to verify bot is working.

### Individual Components

```bash
make back        # Backend only
make front       # Frontend only
make tele-bot    # Interactive Telegram bot
```

## Typical Workflows

### Development (with UI)

```bash
# Terminal 1: Start both
make -j2 run

# Access UI at http://localhost:4001
# Accept signals via UI or Telegram
```

### Production (headless monitoring)

```bash
# Terminal 1: Start backend
make back

# Terminal 2: Start signal monitor
make tele

# Signals sent to Telegram automatically
# Accept via phone, trades saved to journal
```

## Testing the Accept Button

1. **Start backend**:

   ```bash
   make back
   ```

2. **Send test signal**:

   ```bash
   make tele-test
   ```

3. **In Telegram**: Tap "Accept" button

4. **Verify**: Check http://localhost:9000/api/trades/ to see the accepted trade

## Next Steps

- [ ] Test Accept button with backend running
- [ ] Run `make tele` for live monitoring
- [ ] Integrate cTrader for live data
