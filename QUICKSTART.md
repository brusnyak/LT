# Quick Start Guide

## Running the Application

### From the SMC directory (not backend!):

```bash
# Start both backend and frontend
make -j2 run

# Or start them separately:
make run-backend    # Terminal 1
make run-frontend   # Terminal 2
```

### Check Inactivity

```bash
make check-inactivity
```

### Import Gym Trades (one-time test)

```bash
# Make sure backend is running first (make run-backend)
curl -X POST "http://localhost:9000/api/trades/import-from-gym?challenge_id=1"
```

## Setup Cron Job

### Automated Setup (Recommended)

```bash
./setup_cron.sh
```

This will:

- Check if cron job already exists
- Ask for confirmation before replacing
- Set up daily check at 9:00 AM
- Create log file at `/tmp/smc_inactivity.log`

### Manual Setup

```bash
crontab -e
```

Add this line:

```
0 9 * * * cd "/Users/yegor/Documents/Agency & Security Stuff/Development/SMC" && make check-inactivity >> /tmp/smc_inactivity.log 2>&1
```

### Verify Cron Job

```bash
crontab -l
```

### View Logs

```bash
tail -f /tmp/smc_inactivity.log
```

### Remove Cron Job

```bash
crontab -l | grep -v 'check-inactivity' | crontab -
```

## Testing Workflow

### 1. Start the Application

```bash
cd /Users/yegor/Documents/Agency\ \&\ Security\ Stuff/Development/SMC
make -j2 run
```

### 2. Open Browser

Navigate to: http://localhost:4001

### 3. Test Account Settings

- Go to Account page
- Change starting balance to 20000
- Click "Save Configuration"
- Verify Challenge Status updates correctly

### 4. Test Journal

- Go to Journal page
- Verify balance shows 20k (not 50k)
- Check that chart renders without errors

### 5. Import Gym Trades (Optional)

```bash
curl -X POST "http://localhost:9000/api/trades/import-from-gym?challenge_id=1"
```

Check response for number of trades imported.

### 6. Test Inactivity Checker

```bash
make check-inactivity
```

Should show your challenge with current inactivity days.

### 7. Clear History (After Testing)

- In Journal page, click "Clear History"
- Confirm deletion
- Verify trades are cleared

## Troubleshooting

### "No rule to make target"

You're in the wrong directory. Make sure you're in:

```bash
/Users/yegor/Documents/Agency & Security Stuff/Development/SMC
```

NOT in the `backend` subdirectory.

### Backend Won't Start

```bash
cd backend
. venv/bin/activate
pip install -r requirements.txt
```

### Frontend Won't Start

```bash
cd frontend
npm install
```

### Cron Job Not Running

- Check cron is running: `ps aux | grep cron`
- Check logs: `tail -f /tmp/smc_inactivity.log`
- Test manually: `make check-inactivity`
- Verify path in crontab is correct

## Current Status

✅ Migration complete - `last_trade_date` field added
✅ Inactivity checker working - 5 days inactive, no warnings
✅ Cron available - ready to set up
⏳ Gym trades - ready to import when backend is running
