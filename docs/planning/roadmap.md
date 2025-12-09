# Implementation Roadmap

## Overview

This roadmap outlines the step-by-step implementation plan for transforming the SMC Trading Platform into a modular, AI-powered trading environment.

**Total Estimated Time**: 10-14 hours
**Target Completion**: Incremental (can be split across multiple sessions)

---

## Phase 1: Documentation & Organization ✅

**Duration**: 30 minutes
**Status**: In Progress

### Tasks

- [x] Create organized folder structure in `docs/`
- [x] Move existing documentation to proper locations
- [x] Write comprehensive `master_plan.md`
- [ ] Create `roadmap.md` (this document)
- [ ] Create `ai_learning/vision.md`
- [ ] Create `strategies/range_4h.md`
- [ ] Create `api/data_formats.md`

### Deliverables

- Organized documentation structure
- Clear project vision documented
- Easy navigation for future reference

---

## Phase 2: Modular Refactor

**Duration**: 1-2 hours
**Priority**: High (foundation for all future work)

### 2.1 Create SMC Core Modules (45 mins)

#### `backend/app/smc/order_blocks.py`

```python
def detect_order_blocks(df, swing_points):
    """Detect order blocks based on swing points"""

def validate_order_block(ob, current_price):
    """Check if OB is still valid (not mitigated)"""

def is_ob_mitigated(ob, df):
    """Check if price has entered OB zone"""
```

#### `backend/app/smc/structure.py`

```python
def detect_swing_highs(df, lookback):
    """Identify swing high points"""

def detect_swing_lows(df, lookback):
    """Identify swing low points"""

def identify_bos(df, swings):
    """Detect Break of Structure"""

def identify_choch(df, swings):
    """Detect Change of Character"""
```

#### `backend/app/smc/liquidity.py`

```python
def identify_liquidity_pools(df, swings):
    """Find areas of accumulated liquidity"""

def detect_liquidity_sweep(df, pool):
    """Check if liquidity has been swept"""

def find_liquidity_voids(df):
    """Identify areas with low liquidity"""
```

#### `backend/app/smc/fvg.py`

```python
def detect_fvg(df):
    """Detect Fair Value Gaps"""

def is_fvg_filled(fvg, df):
    """Check if FVG has been filled"""
```

#### `backend/app/smc/sessions.py`

```python
def get_session_times(timezone="US/Eastern"):
    """Return session start/end times"""

def identify_session(timestamp):
    """Determine which session (London, NY, Asia)"""

def is_overlap(timestamp):
    """Check if timestamp is during London/NY overlap"""
```

### 2.2 Create Strategy Base Class (30 mins)

#### `backend/app/strategies/base.py`

```python
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.signals = []

    @abstractmethod
    def analyze(self, df_multi_tf):
        """Main analysis method - must be implemented"""
        pass

    @abstractmethod
    def get_config_schema(self):
        """Return configuration options for this strategy"""
        pass

    def calculate_position_size(self, balance, risk_pct, sl_distance):
        """Standard position sizing logic"""
        pass

    def calculate_rr(self, entry, sl, tp):
        """Calculate risk-reward ratio"""
        pass
```

### 2.3 Refactor Existing Strategy (30 mins)

- Extract OB logic from `range_4h.py` → use `smc/order_blocks.py`
- Extract structure logic → use `smc/structure.py`
- Make `range_4h.py` inherit from `BaseStrategy`
- Keep strategy-specific logic (range detection, entry rules)

### 2.4 Testing (15 mins)

- Run existing backtests
- Verify performance metrics unchanged
- Confirm no regressions

### Deliverables

- ✅ Reusable SMC components
- ✅ Clean strategy framework
- ✅ No performance degradation

---

## Phase 3: cTrader Integration

**Duration**: 1-2 hours
**Priority**: High (enables live data)

### 3.1 Setup cTrader Client (30 mins)

#### Update `.env`

```bash
# Use new access token
CTRADER_ACCESS_TOKEN=b9rw1tn3sEhSVmKWOTjl2sGyT693XXYzgBOGTxJyjuY
CTRADER_ACCOUNT_ID=2067137  # $1M demo account
```

#### Create `backend/app/core/ctrader_client.py`

```python
import requests

class CTraderClient:
    def __init__(self, access_token, account_id):
        self.token = access_token
        self.account_id = account_id
        self.base_url = "https://api.spotware.com"

    def get_accounts(self):
        """Fetch account list"""

    def get_historical_data(self, symbol, timeframe, start_date, end_date):
        """Fetch historical OHLCV data"""

    def normalize_data(self, raw_data):
        """Convert cTrader format to standard CSV format"""
```

### 3.2 Test Connection (15 mins)

- Test with new access token
- Verify account access (both 2067130 and 2067137)
- List available symbols

### 3.3 Fetch Historical Data (30 mins)

- EURUSD M5 (last 3 months)
- EURUSD H1 (last 6 months)
- EURUSD H4 (last 1 year)
- Compare data quality with CSV files

### 3.4 Create API Endpoints (30 mins)

#### `GET /api/data/ctrader/accounts`

Returns list of available trading accounts

#### `GET /api/data/ctrader/historical`

Parameters:

- `symbol`: EURUSD, GBPUSD, etc.
- `timeframe`: M1, M5, H1, H4, D1
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

Returns: OHLCV data in standard format

### 3.5 Documentation (15 mins)

Create `docs/research/ctrader_evaluation.md`:

- Data quality comparison
- API reliability assessment
- Recommendations

### Deliverables

- ✅ Working cTrader connection
- ✅ Historical data access
- ✅ API endpoints ready
- ✅ Quality assessment

---

## Phase 4: Multi-Pair Backtest

**Duration**: 30 minutes
**Priority**: Medium (validates strategy robustness)

### Tasks

1. **Run Backtests** (20 mins)

   - EURUSD (baseline)
   - GBPUSD
   - USDJPY
   - GBPJPY

2. **Collect Metrics** (5 mins)

   - Win Rate (%)
   - Average RR
   - Max Drawdown (%)
   - Total Trades
   - Profit Factor
   - Recovery Factor

3. **Create Report** (5 mins)

Create `docs/planning/backtest_results.md`:

| Pair   | Win Rate | Avg RR | Max DD | Trades | Profit Factor |
| ------ | -------- | ------ | ------ | ------ | ------------- |
| EURUSD | 65%      | 1.8    | 1.49%  | 113    | 2.1           |
| GBPUSD | ?        | ?      | ?      | ?      | ?             |
| USDJPY | ?        | ?      | ?      | ?      | ?             |
| GBPJPY | ?        | ?      | ?      | ?      | ?             |

### Analysis

- Which pairs perform best?
- Why do certain pairs fail?
- Should we filter out specific pairs?

### Deliverables

- ✅ Multi-pair performance data
- ✅ Strategy robustness validation
- ✅ Pair selection criteria

---

## Phase 5: UI Configurability

**Duration**: 2-3 hours
**Priority**: Medium (improves user experience)

### 5.1 Layout Preset System (1 hour)

#### Create `frontend/src/contexts/LayoutContext.jsx`

```javascript
const layoutPresets = {
  range_4h: {
    panels: ["chart-4h", "chart-5m", "signals", "journal"],
    overlays: ["ranges", "positions"],
    splitDirection: "horizontal",
  },
  mtf_30_1: {
    panels: ["chart-4h", "chart-30m", "chart-1m", "signals"],
    overlays: ["pois", "liquidity", "structure"],
    splitDirection: "vertical",
  },
  multi_pair: {
    panels: ["chart-1", "chart-2", "chart-3", "comparison"],
    overlays: ["signals_only"],
    splitDirection: "grid",
  },
};
```

### 5.2 Panel Toggles (30 mins)

Add show/hide controls:

- Chart panels (4H, 5M, etc.)
- Signals panel
- Journal panel
- Account stats

### 5.3 Overlay Toggles (30 mins)

Add visibility controls:

- Order blocks
- Liquidity lines
- Structure markers (BOS/ChoCH)
- FVG zones
- Session backgrounds

### 5.4 Settings UI (30 mins)

Create settings panel:

- Layout preset selector
- Panel visibility checkboxes
- Overlay visibility checkboxes
- "Reset to Default" button
- "Save Current Layout" button

### 5.5 Persistence (30 mins)

- Save layout config to localStorage
- Load on app startup
- Allow export/import of layouts

### Deliverables

- ✅ Flexible layout system
- ✅ User customization
- ✅ Saved preferences

---

## Phase 6: V3 - Prediction Mode

**Duration**: 2-3 hours
**Priority**: Medium (unique feature for learning)

### 6.1 Backend Prediction Engine (1 hour)

#### Create `backend/app/core/prediction_engine.py`

```python
class PredictionEngine:
    def __init__(self, strategy):
        self.strategy = strategy
        self.predictions = []

    def predict_next_n_candles(self, df, n=20):
        """Run strategy on current data, predict next N signals"""

    def step_forward(self, df, new_candle):
        """Add 1 candle, regenerate prediction"""

    def get_prediction_accuracy(self):
        """Compare predictions vs reality"""
```

#### API Endpoints

- `POST /api/predict/start` - Initialize prediction mode
- `POST /api/predict/step` - Advance 1 candle
- `GET /api/predict/accuracy` - Get accuracy metrics

### 6.2 Frontend Prediction UI (1 hour)

#### Create `frontend/src/components/PredictionMode.jsx`

Features:

- "Enable Prediction Mode" toggle
- Time slider (navigate through historical data)
- "Step Forward" / "Step Back" buttons
- Prediction accuracy display

#### Chart Visualization

Candle Types:

- **Solid candles**: Actual historical data
- **Dotted candles**: Predicted future data
- **Ghost lines**: Previous predictions (for comparison)

Color Coding:

- Actual: Green/Red
- Predicted: Blue/Purple (semi-transparent)
- Ghost: Gray (thin lines)

### 6.3 Prediction Tracking (30 mins)

Store predictions:

```javascript
{
  timestamp: "2023-12-01 08:00",
  prediction_id: 1,
  predicted_candles: [...],
  predicted_signals: [...],
  actual_outcome: "...",  // filled after reality unfolds
  accuracy: 0.85
}
```

### 6.4 Polish (30 mins)

- Add prediction accuracy chart
- Export prediction logs
- Add replay controls (play/pause animation)

### Deliverables

- ✅ Working prediction mode
- ✅ Visual prediction tracking
- ✅ Accuracy metrics
- ✅ Learning tool for strategy validation

---

## Phase 7: V5 AI Learning - Exploration

**Duration**: 1 hour
**Priority**: Low (future enhancement, exploratory)

### 7.1 YouTube Transcript Extraction (20 mins)

Research & test:

- YouTube Data API v3 (official)
- `yt-dlp` (command-line tool)
- `youtube-transcript-api` (Python library)

Test on Knox Welles video:

- Extract transcript
- Extract metadata (title, publish date, description)
- Parse timestamps

### 7.2 Chart Screenshot Detection (20 mins)

Research & test:

- Frame extraction from video (`ffmpeg`)
- Computer vision to detect charts (OpenCV)
- Or manual timestamping of key frames

Extract 5-10 chart screenshots from 1 video

### 7.3 AI Analysis Proof-of-Concept (15 mins)

Test GPT-4V with chart screenshot:

Prompt:

```
Analyze this trading chart and identify:
1. Order blocks (mark location and type)
2. Liquidity pools/sweeps
3. Market structure (bullish/bearish)
4. Potential entry points
5. Stop loss and take profit levels
```

Test transcript processing:

Prompt:

```
Extract trading rules from this transcript:
[transcript text]

Format as:
- Entry conditions
- Stop loss rules
- Take profit rules
- Filters/confirmations
```

### 7.4 Design Data Structure (5 mins)

Create schema for AI learning dataset:

```json
{
  "videos": [
    {
      "id": "video_123",
      "title": "London Session Breakdown EP12",
      "url": "https://youtube.com/...",
      "publish_date": "2023-11-15",
      "transcript": "...",
      "key_moments": [
        {
          "timestamp": "7:32",
          "concept": "Order Block Entry",
          "transcript_excerpt": "...",
          "chart_frame": "frame_452.png",
          "ai_annotations": {
            "order_blocks": [...],
            "liquidity": [...],
            "entry_signal": {...}
          }
        }
      ]
    }
  ]
}
```

### 7.5 Documentation (5 mins)

Create `docs/ai_learning/vision.md`:

- Feasibility assessment
- Recommended tools
- Data structure design
- Next steps for full implementation

### Deliverables

- ✅ Proof-of-concept complete
- ✅ Tools identified
- ✅ Data structure designed
- ✅ Roadmap for full implementation

---

## Phase 8: MTF 30/1 Strategy

**Duration**: 2-3 hours
**Priority**: High (new strategy implementation)

### 8.1 Strategy Logic (1.5 hours)

#### Create `backend/app/strategies/mtf_30_1.py`

```python
from strategies.base import BaseStrategy
from smc import structure, order_blocks, liquidity, fvg

class MTF30_1Strategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="MTF 30/1 POI to Liquidity",
            description="Multi-timeframe strategy: 4H trend, 30M POI, 1M entry"
        )

    def analyze(self, df_multi_tf):
        df_4h = df_multi_tf['4H']
        df_30m = df_multi_tf['30M']
        df_1m = df_multi_tf['1M']

        # Step 1: Determine 4H trend
        trend = self._analyze_4h_trend(df_4h)

        # Step 2: Find 30M POIs (OBs, FVGs, liquidity zones)
        pois = self._find_pois_30m(df_30m, trend)

        # Step 3: Wait for 1M entry from POI
        signals = self._find_1m_entries(df_1m, pois, trend)

        return signals

    def _analyze_4h_trend(self, df_4h):
        """Identify trend direction using structure"""
        swings = structure.detect_swings(df_4h)
        bos = structure.identify_bos(df_4h, swings)
        # Return 'bullish', 'bearish', or 'ranging'

    def _find_pois_30m(self, df_30m, trend):
        """Identify Points of Interest on 30M"""
        obs = order_blocks.detect_order_blocks(df_30m)
        fvgs = fvg.detect_fvg(df_30m)
        liq_zones = liquidity.identify_liquidity_pools(df_30m)
        # Filter POIs based on trend direction

    def _find_1m_entries(self, df_1m, pois, trend):
        """Find entry signals from POI to liquidity target"""
        # Wait for price to enter POI (OB/FVG)
        # Confirm with 1M structure shift
        # Set TP at liquidity target
        # Calculate high RR (targeting 4-10R)
```

### 8.2 Backtesting (30 mins)

- Test on EURUSD (3 months of data)
- Collect performance metrics
- Compare with `range_4h` results

### 8.3 Documentation (15 mins)

Create `docs/strategies/mtf_30_1.md`:

- Strategy rules (detailed)
- Entry conditions
- Exit conditions
- Risk management
- Expected performance

### 8.4 UI Integration (45 mins)

- Add "MTF 30/1" to strategy selector
- Create strategy config panel (show POI boxes, liquidity targets)
- Add MTF-specific chart overlays
- Update visualization to show 3 timeframes

### Deliverables

- ✅ New strategy implemented
- ✅ Backtest results documented
- ✅ UI integration complete
- ✅ Ready for forward-testing

---

## Success Criteria

### Phase Completion Checklist

- [ ] All 8 phases completed
- [ ] No regressions in existing functionality
- [ ] Documentation up-to-date
- [ ] All tests passing
- [ ] Performance targets met (90% WR, 2-10R, 1-3% DD)

### Performance Validation

Before considering project complete:

1. Run multi-strategy comparison
2. Validate on out-of-sample data
3. Forward-test with prediction mode
4. Review AI analysis recommendations

---

## Risk Management

### Technical Risks

- **cTrader API changes**: Have CSV fallback
- **Performance degradation**: Comprehensive testing after each phase
- **Data quality issues**: Validate against known-good CSV data

### Strategy Risks

- **Overfitting**: Test on multiple pairs and time periods
- **Market regime changes**: Continuous monitoring and adaptation
- **Black swan events**: Strict risk management (max 0.5% per trade)

---

## Timeline

### Optimistic (10 hours)

- Phase 1: 0.5h
- Phase 2: 1h
- Phase 3: 1h
- Phase 4: 0.5h
- Phase 5: 2h
- Phase 6: 2h
- Phase 7: 1h
- Phase 8: 2h

### Realistic (14 hours)

- Add 20-40% buffer for debugging, testing, refinement
- Split across multiple sessions
- Allow time for user feedback and iteration

---

## Next Steps

1. ✅ **Complete Phase 1** (documentation)
2. **Start Phase 2** (modular refactor)
3. Proceed sequentially through phases
4. Review and validate after each phase
5. Iterate based on findings

---

_Last Updated: 2025-11-28_
