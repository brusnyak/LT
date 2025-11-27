# Project Master Plan: SMC Trading Environment (V1)

## 1. Vision & Goal

**Goal**: Build a robust, evolving trading environment for recording, reviewing, and learning.
**V1 Focus**: "Momentum" - Implement the **4H Range Strategy** with a professional dashboard using local CSV data.
**End State**: A professional-grade web application that connects to data (cTrader), visualizes market data, executes strategies, and journals trades automatically.

## 2. V1 Scope: The "4H Range" Dashboard

### Core Features

1.  **Environment**:
    - **Frontend**: React + Vite application with a "Cockpit" layout.
    - **Backend**: FastAPI server for strategy logic and data processing.
    - **Data**: Local CSV files (EURUSD, GBPUSD) from `archive/LT1/data`.
2.  **Strategy**: **4H Range Scalping** (See `strategies.md`).
    - **Logic**: Identify 4H Range (NY Time), detect Breakout & Re-entry.
    - **Visualization**: Split View (4H Context + 5M Execution).
3.  **Journaling**:
    - Automatic recording of simulated trades.
    - Account Balance tracking (Start $50k, Risk 0.5%).

### Architecture Overview

- **Frontend**:
  - **Chart**: `Lightweight Charts` (TradingView).
  - **State**: React Context for Account & Strategy state.
  - **Layout**: Split Screen (Top/Bottom or Left/Right) for Multi-Timeframe analysis.
- **Backend**:
  - **API**: Endpoints to serve candle data and strategy signals.
  - **Engine**: Python-based strategy runner (Pandas).

## 3. Directory Structure (Cleaned)

```
/SMC
├── backend/
│   ├── app/
│   │   ├── api/            # API Endpoints
│   │   ├── core/           # Config, Data Loaders (CSV)
│   │   ├── smc/            # Shared SMC Logic (Swings, etc.)
│   │   ├── strategies/     # Strategy Implementations
│   │   │   └── range_4h.py # V1 Strategy Logic
│   │   ├── journal/        # Trade Recording Logic
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # UI Components (Chart, Panels)
│   │   ├── hooks/          # Logic Hooks
│   │   ├── pages/          # Main Views
│   │   └── services/       # API Calls
│   └── package.json
├── docs/                   # Documentation
│   ├── master_plan.md      # This file
│   ├── strategies.md       # Strategy Rules
│   ├── architecture.md     # System Design
│   ├── frontend_spec.md    # UI/UX Spec
│   └── api_spec.md         # API Contract
├── data/                   # Active CSV data (Symlinked or copied from archive)
└── archive/                # Old/Unused files (LT1, charts, bot code)
```

## 4. Roadmap (Implementation Phase)

### Phase 1: Foundation & Cleanup

1.  **Setup**: Verify `backend` and `frontend` run after re-organization.
2.  **Data**: Ensure CSV loader works with the files in `archive/LT1/data`.

### Phase 2: Backend Logic (4H Range & SMC)

1.  **SMC Core**: Port advanced logic from `pine.txt` to Python.
    - _Why_: `pine.txt` contains robust definitions for Swings, OBs, and FVGs that we should reuse.
2.  **Strategy Module**: Implement `range_4h.py`.
    - Function: `calculate_4h_range(df_4h)` -> Returns High/Low/Time.
    - Function: `detect_signals(df_5m, range_levels)` -> Returns Entry/Exit signals.
3.  **API**: Create endpoints `/strategy/range-4h/analyze`.

### Phase 3: Frontend "Cockpit"

1.  **Layout**: Implement the Split View (4H + 5M).
2.  **Integration**: Connect Chart to Backend API.
3.  **Overlays**: Draw the 4H Box and Signal Arrows.

### Phase 4: Journaling & Polish

1.  **Account Config**: Add UI to set Balance ($20k) and Risk (0.5%).
2.  **Trade List**: Display simulated trades in a table.
3.  **Stats**: Show Win Rate, max DD, time, RR

### Phase 5: V2 Features (Backtest & Optimization)

1.  **Backtest Module**: Historical testing with date range (Implemented).
2.  **Comparison Table**: A/B test strategies (Implemented).
3.  **Live Data**: Connect to cTrader/MetaTrader.

### Phase 6: V3 - Market Prediction Mode

1.  **Concept**: "What If" Simulator.
2.  **UI**: Split Screen.
    - **Left**: Actual Market Data (Real-time/Current).
    - **Right**: Predicted Future (Simulation).
    - **Logic**: The system updates the prediction on the right with every new candle on the left, acting as a forward-testing assistant.

### Phase 7: V4 - AI Vision Analysis

1.  **Concept**: "Analyze My Chart" (Photo/Screenshot Input).
2.  **Workflow**:
    - User uploads 3 screenshots: 4H (Context), 30M (Structure), 5M (Entry).
    - User selects Pair (e.g., EURUSD).
3.  **Output**:
    - AI analyzes market structure, OBs, and Liquidity from images.
    - Generates a trade plan (Long/Short, Entry, SL, TP).
    - **Visual Overlay**: Draws the analysis directly onto the uploaded images.

## 5. Repository & Version Control

- **Repo**: `https://github.com/brusnyak/LT.git`
- **License**: Apache 2.0
- **Status**: V1 Complete. Ready for push.
