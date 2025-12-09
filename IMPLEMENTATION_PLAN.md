# SMC Trading Platform - Unified Implementation Plan

## Vision

**A professional SMC trading environment that acts as your trading assistant** - generating high-quality signals based on your manual trading patterns, tracking performance with prop firm rules, and providing institutional-grade analysis. You maintain full control with manual execution while the system handles analysis, journaling, and performance tracking.

---

## Core Data Flow Architecture

```
┌─────────────────┐
│  Account Setup  │ ← User configures prop firm rules, risk settings
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Strategy Engine │ ← Generates signals based on HumanTrainedStrategy
│  (Automated)    │   (H4 structure → M15 shift → M5 POI)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Signal Display  │ ← User reviews signals on chart
│  (Manual Review)│   TradingView-style positions with Entry/SL/TP
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Manual Execution│ ← User decides: Accept or Reject signal
│  (User Action)  │   If accept → Creates journal entry
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Journal/Trades  │ ← Tracks accepted trades with account rules
│  (Database)     │   Calculates P&L, DD, challenge progress
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Home Dashboard  │ ← Displays aggregated stats from journal
│  (Stats View)   │   Win rate, R:R, trades count
└─────────────────┘
```

---

## ✅ Completed Phases

### Phase 1-3: Strategy Development (COMPLETE)

- ✅ Gym tab for manual trade recording
- ✅ HumanTrainedStrategy implementation
- ✅ Multi-timeframe analysis (H4/M15/M5)
- ✅ Backtested: 92% WR, 4.5 R:R across 4 pairs
- ✅ API endpoints for signals

### Phase 4A: Frontend Integration (COMPLETE)

- ✅ Position visualization on chart
- ✅ API performance optimization (20x faster)
- ✅ Home page real stats
- ✅ Signals panel with multi-pair support

---

## 🔄 Current Phase: Data Flow Implementation

### Missing Components

#### 1. Signal Acceptance Flow

**Problem**: Signals are displayed but not connected to journal/account

**Implementation**:

```
SignalsPanel → "Accept Signal" button →
  POST /api/trades/accept {signal, account_settings} →
    Journal entry created →
      Home stats updated
```

**Backend**:

- Create `/api/trades/accept` endpoint
- Accept signal data + account settings
- Create trade entry in database
- Apply account rules (risk %, max concurrent, etc.)

**Frontend**:

- Add "Accept" button to each signal in SignalsPanel
- Modal to confirm trade acceptance
- Fetch account settings from localStorage
- Send to backend with signal data

#### 2. Journal Integration with Account

**Problem**: Journal doesn't use account settings for calculations

**Implementation**:

- Journal fetches account config from `/api/account/config`
- Uses config for:
  - Balance tracking
  - Profit target calculations
  - Daily/total loss limits
  - Challenge phase tracking

#### 3. Home Stats from Journal

**Problem**: Home fetches from strategy, not journal

**Implementation**:

- Change `/api/stats/summary` to query journal database
- Return actual accepted trades, not strategy signals
- Calculate real win rate from closed trades

---

## 🎯 Immediate Tasks

### Task 1: Database Schema for Trades

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    signal_id TEXT,
    pair TEXT,
    type TEXT,  -- LONG/SHORT
    entry REAL,
    sl REAL,
    tp REAL,
    rr REAL,
    entry_time TIMESTAMP,
    close_time TIMESTAMP,
    status TEXT,  -- OPEN/CLOSED/PENDING
    outcome TEXT,  -- WIN/LOSS/BREAKEVEN
    pnl REAL,
    account_id INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE account_config (
    id INTEGER PRIMARY KEY,
    balance REAL,
    risk_per_trade REAL,
    challenge_type TEXT,
    profit_target REAL,
    daily_loss_limit REAL,
    total_loss_limit REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Task 2: Backend Endpoints

**File**: `backend/app/api/trades.py` (NEW)

```python
POST   /api/trades/accept        # Accept signal → create trade
GET    /api/trades               # List all trades
DELETE /api/trades/{id}          # Delete specific trade
DELETE /api/trades/clear         # Clear all trades for pair
PATCH  /api/trades/{id}/close    # Close trade (manual)
```

**File**: `backend/app/api/account.py` (NEW)

```python
GET    /api/account/config       # Get account settings
PUT    /api/account/config       # Update account settings
POST   /api/account/challenges   # Create new challenge
GET    /api/account/challenges   # List challenges
DELETE /api/account/challenges/{id}  # Delete challenge
```

### Task 3: Frontend Updates

**SignalsPanel.jsx**:

- Add "Accept" button per signal
- Modal: "Accept this trade?" with signal details
- On accept: POST to `/api/trades/accept`
- Refresh journal after acceptance

**JournalPage.jsx**:

- Fetch from `/api/trades` instead of `/api/analysis/journal`
- Fetch account config from `/api/account/config`
- Calculate metrics using account rules

**Home.jsx**:

- Update `/api/stats/summary` to use journal trades
- Display real accepted trade stats

**AccountPage.jsx**:

- Save button → PUT `/api/account/config`
- Persist to database, not just localStorage

---

## 📋 Clear History Implementation

### Requirements

1. **Signals**: Clear all signals for specific pair
2. **Gym Sessions**: Delete individual session (already exists)
3. **Trades**: Clear all accepted trades
4. **Challenges**: Delete specific challenge

### Backend Endpoints

```python
# In trades.py
DELETE /api/trades/clear?pair={pair}  # Clear trades for pair
DELETE /api/trades/clear              # Clear all trades

# In trainer.py (already exists)
DELETE /api/trainer/sessions/{id}

# In account.py
DELETE /api/account/challenges/{id}
```

### Frontend Buttons

- **SignalsPanel**: "Clear Signals" button
- **JournalPage**: "Clear History" button
- **GymAnalysisPanel**: "X" on each session card (exists)
- **AccountPage**: "Delete" on each challenge card

---

## 🎯 Workflow: Trader with Manual Execution

### Daily Trading Flow

1. **Morning Setup**

   - Open platform
   - Check account status (balance, limits, challenge progress)
   - Review overnight signals

2. **Signal Generation**

   - Strategy runs automatically on chart load
   - Displays signals as TradingView-style positions
   - Shows Entry, SL, TP with colors

3. **Manual Review**

   - User reviews each signal
   - Checks confluence with own analysis
   - Decides: Accept or Ignore

4. **Trade Acceptance**

   - Click "Accept" on signal
   - System creates journal entry
   - Applies account rules (risk %, position size)
   - Tracks trade in database

5. **Trade Management**

   - User executes trade manually on broker
   - Marks trade as closed when done
   - System calculates P&L, updates stats

6. **Performance Review**
   - Journal shows all accepted trades
   - Home displays aggregated stats
   - Account page shows challenge progress

### Key Principle

**System suggests, User decides, System tracks**

---

## 📊 Success Metrics

- ✅ Strategy generates quality signals (92% WR verified)
- 🔄 User can accept/reject signals easily
- 🔄 Journal tracks only accepted trades
- 🔄 Account rules applied automatically
- 🔄 Home shows real performance stats
- 🔄 Clear history works granularly

---

## Next Steps

1. **Implement database models** (trades, account_config)
2. **Create backend endpoints** (trades.py, account.py)
3. **Update frontend data flow** (SignalsPanel, Journal, Home)
4. **Test complete flow** (signal → accept → journal → home)
5. **Add clear history** (all delete endpoints)
