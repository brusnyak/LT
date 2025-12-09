# Inactivity Monitoring Setup

## Overview

The inactivity monitoring system tracks trading activity and enforces prop firm rules:

- **7 days of inactivity**: Telegram warning sent
- **10 days of inactivity**: Account breached (deactivated)

## Components

### 1. Database Changes

- Added `last_trade_date` field to `Challenge` model
- Automatically updated when trades are accepted
- Falls back to `created_at` for new challenges

### 2. Inactivity Checker Script

Location: `backend/check_inactivity.py`

Features:

- Checks all active challenges
- Calculates days since last trade
- Sends Telegram notifications
- Automatically breaches accounts at 10 days

### 3. Makefile Command

```bash
make check-inactivity
```

## Setup Instructions

### Step 1: Run Database Migration

```bash
cd backend
. venv/bin/activate
python3 migrate_add_last_trade_date.py
```

This adds the `last_trade_date` column to existing challenges.

### Step 2: Test the Checker Manually

```bash
make check-inactivity
```

You should see output showing all active challenges and their inactivity status.

### Step 3: Set Up Daily Cron Job (Optional)

To run the checker automatically every day at 9 AM:

```bash
# Open crontab editor
crontab -e

# Add this line (adjust path to your project):
0 9 * * * cd /Users/yegor/Documents/Agency\ \&\ Security\ Stuff/Development/SMC && make check-inactivity >> /tmp/inactivity_check.log 2>&1
```

Or run it every 6 hours:

```bash
0 */6 * * * cd /Users/yegor/Documents/Agency\ \&\ Security\ Stuff/Development/SMC && make check-inactivity >> /tmp/inactivity_check.log 2>&1
```

### Step 4: Verify Telegram Integration

The checker uses the same Telegram credentials as the signal bot:

- `TELEGRAM_BOT_TOKEN` from `.env`
- `TELEGRAM_CHAT_ID` from `.env`

Test by running:

```bash
make check-inactivity
```

If you have an active challenge with no trades, you should receive a warning after 7 days.

## How It Works

### When You Accept a Trade

1. Trade is created in database
2. `challenge.last_trade_date` is updated to current time
3. Inactivity counter resets

### Daily Check (via cron)

1. Script loads all active challenges
2. For each challenge:
   - Calculates days since last trade
   - If ≥7 days: Sends Telegram warning
   - If ≥10 days: Breaches account + sends notification

### Telegram Notifications

**7-Day Warning:**

```
⚠️ INACTIVITY WARNING

Challenge: My FTMO Challenge
Days inactive: 7
Days until breach: 3

⏰ You must make a trade within 3 days to avoid account breach.

Last trade: 2025-11-28 14:30 UTC
```

**10-Day Breach:**

```
🚨 ACCOUNT BREACHED

Challenge: My FTMO Challenge
Reason: 10 days of inactivity
Limit: 10 days

Account has been deactivated.
```

## Testing

### Test with Existing Challenge

1. Check current status:

   ```bash
   make check-inactivity
   ```

2. Manually set `last_trade_date` to 8 days ago (for testing):

   ```python
   # In Python shell
   from app.database import SessionLocal
   from app.models.db.challenge import Challenge
   from datetime import datetime, timedelta

   db = SessionLocal()
   challenge = db.query(Challenge).filter(Challenge.id == 1).first()
   challenge.last_trade_date = datetime.utcnow() - timedelta(days=8)
   db.commit()
   db.close()
   ```

3. Run checker again:

   ```bash
   make check-inactivity
   ```

   You should receive a Telegram warning.

### Reset After Testing

```python
from app.database import SessionLocal
from app.models.db.challenge import Challenge
from datetime import datetime

db = SessionLocal()
challenge = db.query(Challenge).filter(Challenge.id == 1).first()
challenge.last_trade_date = datetime.utcnow()
challenge.is_active = True
db.commit()
db.close()
```

## Troubleshooting

### No Telegram Messages

- Check `.env` file has `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Verify bot token is valid
- Check chat ID is correct (use `/start` with bot to verify)

### Cron Job Not Running

- Check cron logs: `grep CRON /var/log/syslog` (Linux) or check Console.app (Mac)
- Verify path in crontab is absolute
- Check permissions on scripts
- Test command manually first

### Database Migration Failed

- Ensure backend virtual environment is activated
- Check database file permissions
- Verify SQLite version supports ALTER TABLE

## Notes

- Inactivity is calculated from `last_trade_date` or `created_at` if no trades yet
- Only ACTIVE challenges are checked
- Breached accounts are set to `is_active=False`
- The system tracks when trades are ACCEPTED, not when they close
- Importing gym trades also updates `last_trade_date`
