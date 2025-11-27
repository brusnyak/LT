# Implementation Plan - SMC Trading Environment V1
## Goal
Implement the **4H Range Strategy** ("Momentum") dashboard using a React Frontend and FastAPI Backend, powered by local CSV data.
## User Review Required
> [!IMPORTANT]
> **Timezone Decision**: The strategy logic will use **UTC+1** as the base time, as decided in [strategies.md](file:///Users/yegor/Documents/Agency%20&%20Security%20Stuff/Development/SMC/docs/strategies.md). The "First 4H Candle" will be identified as the candle starting at **00:00 UTC+1**. This differs slightly from the "New York Time" instruction in the video transcript but aligns with the project's documented decision.
## Proposed Changes
### Backend (`/backend`)
#### [NEW] `app/core/data_loader.py`
- Implement `load_candle_data(pair, timeframe)` to read CSVs from `archive/charts/forex`.
- Handle standardizing column names to `[time, open, high, low, close, volume]`.
#### [NEW] `app/strategies/range_4h.py`
- Implement `detect_4h_range(df_4h)`: Finds the 00:00 UTC+1 candle and defines High/Low.
- Implement `analyze_5m_signals(df_5m, range_levels)`: Detects Breakout (Close > High) and Re-entry (Close < High).
- Returns a list of `Signal` objects and `RangeLevel` objects.
#### [MODIFY] `app/api/data.py`
- Update `get_candles` endpoint to use the new `data_loader`.
#### [MODIFY] `app/api/analysis.py`
- Create `get_range_strategy` endpoint that runs the logic from `range_4h.py`.
### Frontend (`/frontend`)
#### [MODIFY] `src/components/chart/TradingViewChart.jsx`
- Ensure it can accept `markers` (arrows) and `shapes` (rectangles/lines) as props.
- Add logic to draw the "Range Box" (High/Low lines extending to the right).
#### [NEW] `src/components/layout/SplitView.jsx`
- Create a layout component that renders two `TradingViewChart` instances stacked vertically.
- Top Chart: 4H Timeframe (Context).
- Bottom Chart: 5M Timeframe (Execution).
- Implement crosshair synchronization (if possible with `lightweight-charts` API, otherwise independent).
#### [MODIFY] `src/App.jsx`
- Replace the single chart view with `SplitView` when the strategy is active.
- Fetch data for both 4H and 5M timeframes.
- Fetch strategy analysis from `GET /api/analysis/range-4h`.
## Verification Plan
### Automated Tests
- **Backend**: Unit tests for `range_4h.py` using sample DataFrames to verify signal detection logic (Breakout + Re-entry).
- **API**: Test endpoints return JSON in the expected format.
### Manual Verification
- **Visual Check**:
    - Load "EURUSD".
    - Verify Top Chart shows 4H candles.
    - Verify Bottom Chart shows 5M candles.
    - Verify "Range Box" is drawn correctly on the 00:00 candle.
    - Check if "Green Arrow" appears on a valid Long Re-entry.
