# SMC Trading Platform - Master Plan

## 🎯 Final Project Goals

Build an advanced, AI-powered trading environment that achieves exceptional performance across all market conditions.

### Performance Targets

- **Win Rate**: 90%
- **Risk-Reward Ratio**: 2-10R (minimum 2R, best setups up to 10R)
- **Maximum Drawdown**: 1-3%
- **Profit Target**: +35% PnL

### Core Objective

Create a modular, scalable trading platform that:

1. Tests and optimizes multiple SMC/ICT strategies
2. Connects to live market data (cTrader)
3. Provides advanced visualization and analysis tools
4. Learns and improves through AI-powered feedback loops
5. Helps pass prop firm challenges through systematic refinement

---

## 📊 Project Vision

### V1: Foundation (✅ Complete)

**"Momentum" - 4H Range Strategy Dashboard**

- ✅ FastAPI backend + React frontend
- ✅ 4H Range strategy implementation
- ✅ Split-view charts (4H context + 5M execution)
- ✅ Position visualization with entry/SL/TP markers
- ✅ Journaling system with P&L tracking
- ✅ Account stats dashboard
- ✅ Backtest module with comparison table

**Results**: 65% WR, 1.49% DD on EURUSD

---

### V2: Modular Architecture & Data

**Goal**: Build scalable foundation for multiple strategies

#### Core Features:

1. **Modular SMC Components**:

   - Reusable order block detection
   - Liquidity analysis (pools, sweeps, voids)
   - Market structure (BOS, ChoCH, swing points)
   - Fair Value Gap detection
   - Session analysis (London, NY, Asia)

2. **cTrader Integration**:

   - Live historical data fetch
   - Real-time market monitoring
   - Multi-pair support

3. **Multi-Pair Backtesting**:

   - Test strategies across EURUSD, GBPUSD, USDJPY, GBPJPY
   - Compare performance metrics
   - Identify optimal pairs for each strategy

4. **Strategy Framework**:
   - Base strategy class for inheritance
   - Dynamic strategy loading
   - Strategy-specific configuration

---

### V3: Advanced UI & Prediction Mode

**Goal**: Professional-grade interface with forward-testing

#### UI Configurability:

- **Layout Presets**: Save/load custom layouts for different strategies
- **Panel Toggles**: Show/hide charts, signals, journal, settings
- **Overlay Controls**: Toggle OBs, liquidity, structure, sessions
- **Drag-and-drop**: TradingView-style layout customization (future)

#### Prediction Mode:

Simulate strategy execution in real-time with "ghost predictions"

**Workflow**:

1. Load historical data up to specific date
2. Strategy generates prediction for next N candles
3. Display prediction as "ghost line" overlay
4. User advances time (step forward/backward)
5. Compare prediction vs reality
6. Track prediction accuracy over time

**Use Cases**:

- Forward-testing strategies without risking capital
- Understanding strategy behavior in different market conditions
- Training pattern recognition skills
- Validating strategy logic before live trading

---

### V4: Multi-Strategy Implementation

**Goal**: Implement robust strategy suite

#### Planned Strategies:

**1. 4H Range** (✅ Complete)

- Identify 4H range during NY session
- Detect breakout and re-entry signals
- Current: 65% WR, 1.49% DD

**2. MTF 30/1** (Multi-Timeframe)

- 4H: Determine trend direction
- 30M: Identify POIs (OBs, FVGs, liquidity zones)
- 1M: Enter from POI to liquidity target
- Target: Higher RR ratio (4-10R)

**3. Unified (Complex)**

- Combines multiple SMC/ICT concepts
- Dynamic TP based on FVG/liquidity
- Swing entry filter
- Session-based logic
- Target: 80%+ WR, 2-5R

#### Strategy Selection:

- Dropdown selector in UI
- Strategy-specific config panels
- Dedicated visualization overlays
- Performance comparison dashboard

---

### V5: AI Continuous Learning 🤖

**Goal**: Self-improving trading system through AI analysis

#### Data Collection Pipeline:

**YouTube Knowledge Extraction** (@KnoxWelles)

1. Extract video transcripts (trading explanations)
2. Identify chart screenshots from videos
3. Create timestamped annotation dataset
4. Build searchable knowledge base

**Dataset Structure**:

```json
{
  "video_id": "xyz",
  "timestamp": "5:23",
  "concept": "Order Block Mitigation",
  "transcript": "Notice how price sweeps liquidity before entering the OB...",
  "chart_image": "/research/youtube/knox_welles/video_xyz_frame_323.png",
  "annotations": ["bearish OB", "liquidity sweep", "entry signal"]
}
```

#### AI Learning Loop:

**Phase 1: Post-Trade Analysis**

```
Trade Result → AI Analysis → Pattern Recognition →
Strategy Adjustment → Backtest → Deploy
```

**Phase 2: Pre-Trade Validation**

- AI compares current setup with historical winning setups
- References Knox Welles examples for validation
- Suggests improvements or warns of missing confirmations

**Phase 3: Continuous Optimization**

- Analyze 100+ trades to find patterns
- Identify why certain setups fail
- Suggest parameter adjustments
- A/B test modifications

#### AI Trading Assistant:

**Example Interaction**:

```
User: "Should I take this EURUSD setup?"

AI: "Analyzing setup...

     ✅ Matches Knox's setup from Video EP12 @ 7:32
     ✅ 4H bearish structure confirmed
     ✅ 30M OB mitigation zone
     ❌ Missing: FVG fill confirmation

     Recommendation: Wait for FVG fill at 1.0785 before entry

     Similar setups: 78% success rate when FVG confirmed
     Your historical performance: 15 wins, 4 losses (79% WR)
     Suggested SL: 1.0795 | TP: 1.0750 (4.5R)"
```

---

## 🏗️ System Architecture

### Backend Structure

```
backend/app/
├── smc/                    # Core SMC Components (Reusable)
│   ├── order_blocks.py     # OB detection & validation
│   ├── liquidity.py        # Liquidity analysis
│   ├── structure.py        # Market structure (BOS/ChoCH)
│   ├── fvg.py              # Fair Value Gaps
│   ├── sessions.py         # Trading sessions
│   └── imbalance.py        # Breaker blocks, mitigation
│
├── strategies/             # Strategy Implementations
│   ├── base.py             # Base strategy class
│   ├── range_4h.py         # ✅ 4H Range strategy
│   ├── mtf_30_1.py         # 🔜 30M/1M strategy
│   └── unified.py          # 🔜 Complex unified strategy
│
├── core/                   # Core Infrastructure
│   ├── data_loader.py      # CSV data loading
│   ├── ctrader_client.py   # cTrader API integration
│   └── config.py           # Configuration management
│
├── backtest/               # Backtesting Engine
│   ├── engine.py           # Backtest execution
│   └── metrics.py          # Performance metrics
│
├── ai/                     # AI Learning System
│   ├── youtube_extractor.py   # Video transcript extraction
│   ├── chart_analyzer.py      # Vision-based chart analysis
│   ├── trade_reviewer.py      # Post-trade analysis
│   └── knowledge_base.py      # Searchable learning data
│
└── api/                    # RESTful API
    ├── data.py             # Data endpoints
    ├── strategy.py         # Strategy endpoints
    ├── backtest.py         # Backtest endpoints
    └── ai.py               # AI assistant endpoints
```

### Frontend Structure

```
frontend/src/
├── components/
│   ├── charts/             # Chart components
│   ├── overlays/           # Order blocks, liquidity, structure
│   ├── layout/             # Panel system, drag-and-drop
│   ├── tabs/               # Main navigation tabs
│   └── strategies/         # Strategy-specific UI
│
├── contexts/               # React contexts
│   ├── LayoutContext.jsx   # Layout configuration
│   ├── StrategyContext.jsx # Active strategy state
│   └── DataContext.jsx     # Market data state
│
├── hooks/                  # Custom hooks
│   └── usePrediction.jsx   # Prediction mode logic
│
└── services/               # API clients
    ├── strategyApi.js
    ├── dataApi.js
    └── aiApi.js
```

---

## 📈 Data Sources

### Current Data (CSV Files)

**Location**: `archive/trading bot 2/`

**Coverage**:

- **Forex**: EURUSD, GBPUSD, GBPJPY, USDJPY, USDCAD, AUDUSD, EURGBP
- **Crypto**: BTC, ETH, ADA, XRP
- **Indices**: US30, US500, NAS100, USTEC
- **Metals**: XAUUSD (Gold), XAGUSD (Silver)

**Timeframes**: M1, M5, M15, M30, H1, H4, D1, W1

### Future Data (cTrader)

**Accounts**:

- Demo 2067130: $100k, 500:1 leverage
- Demo 2067137: $1M, 100:1 leverage

**Capabilities**:

- Real-time historical data fetch
- Live market monitoring
- Multi-timeframe support
- Multiple asset classes

---

## 🚀 Implementation Roadmap

### Phase 1: Documentation & Organization ✅

- Structured docs/ folder
- Clear planning documents
- Strategy documentation
- AI learning vision

### Phase 2: Modular Refactor (1-2 hours)

- Extract SMC logic into reusable modules
- Create base strategy class
- Refactor existing code

### Phase 3: cTrader Integration (1-2 hours)

- API client implementation
- Historical data fetch
- Data quality validation

### Phase 4: Multi-Pair Backtest (30 mins)

- Test across multiple pairs
- Performance comparison
- Identify optimal pairs

### Phase 5: UI Configurability (2-3 hours)

- Layout presets system
- Panel/overlay toggles
- Strategy-specific UI

### Phase 6: Prediction Mode (2-3 hours)

- Prediction engine
- Ghost line visualization
- Time navigation controls

### Phase 6c: Enhanced Gym System (2-3 days) - IN PROGRESS

**Goal**: Implement TradingView-style position tool with proper trade recording

**Why This Approach**:

- Backfill approach was flawed (tried to simulate outcomes from future data)
- Need accurate entry/exit marking by user
- Visual context (screenshots) for AI training
- Annotation tools to document trading logic

**Features**:

- TradingView-style position drawing (Entry/SL/TP + Exit)
- Drawing tools (lines, zones, text annotations)
- Auto-screenshot capture on save
- Enhanced data model (exit_time, screenshot_path, annotations)

**Deliverables**:

- Unified DrawingToolbar component
- Enhanced position tool (4-click: Entry → SL → TP → Exit)
- Screenshot capture with html2canvas
- Updated database schema
- Re-recorded trades with accurate data

### Phase 7: AI Pattern Recognition (2-3 weeks)

**Updated Approach**: Learn from properly recorded trades with visual context

- Generate chart screenshots from trades (already captured)
- Train CLIP classifier on WIN/LOSS outcomes
- Deploy confidence scoring system
- Integrate into Gym UI

**Why This Approach**:

- Properly documented trades with screenshots
- CLIP is free, fast, runs on CPU
- Learns YOUR specific patterns
- No need for GPT-4V or YouTube extraction

**Optional**: Use existing SMC documentation (`docs/concepts/`) for validation

### Phase 8: MTF 30/1 Strategy (2-3 hours)

- Strategy implementation
- Backtesting
- UI integration

---

## 📝 Success Metrics

### Technical Metrics

- Code modularity (reusable SMC components)
- Test coverage (>80% for core logic)
- API response time (<100ms)
- UI responsiveness (60fps)

### Trading Metrics

- Win rate per strategy
- Risk-reward ratio distribution
- Maximum drawdown
- Recovery factor
- Profit factor

### AI Learning Metrics

- Prediction accuracy
- Trade analysis quality
- Knowledge base coverage
- Optimization improvements

---

## 🔐 Version Control & Deployment

**Repository**: `https://github.com/brusnyak/LT.git`
**License**: Apache 2.0

**Deployment Strategy**:

- Development: Local (FastAPI + Vite dev servers)
- Testing: Docker containers
- Production: TBD (after prop firm validation)

---

## 📚 Learning Resources

- **YouTube**: @KnoxWelles (SMC/ICT concepts)
- **Documentation**: `/docs` (internal knowledge base)
- **Backtest Results**: `/docs/planning/backtest_results.md`
- **AI Analysis**: `/docs/research/ai_datasets`

---

## 🎓 Next Steps

1. Complete modular refactor
2. Validate cTrader integration
3. Test multi-pair performance
4. Build configurable UI
5. Implement prediction mode
6. Explore AI learning pipeline
7. Deploy MTF 30/1 strategy
8. **Pass prop firm challenge** 🏆
