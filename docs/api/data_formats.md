# Data Formats & Schemas

## Overview

This document defines all data formats used across the SMC Trading Platform for consistency and interoperability.

---

## 1. OHLCV Data Format

### CSV Format (Standard)

**Files**: `*.csv` in `archive/trading bot 2/data/`

```csv
# Historical data for EURUSD M5
# timestamp open high low close volume
2025-05-01 08:05 1.13027 1.13062 1.13016 1.13061 523
2025-05-01 08:10 1.13060 1.13070 1.13023 1.13070 548
2025-05-01 08:15 1.13068 1.13083 1.13036 1.13061 542
```

**Field Descriptions**:

- `timestamp`: ISO format (YYYY-MM-DD HH:MM) or Unix timestamp
- `open`: Opening price for the period
- `high`: Highest price during the period
- `low`: Lowest price during the period
- `close`: Closing price for the period
- `volume`: Trading volume (optional, can be 0)

### JSON Format (API)

```json
{
  "pair": "EURUSD",
  "timeframe": "M5",
  "data": [
    {
      "timestamp": "2025-05-01T08:05:00Z",
      "open": 1.13027,
      "high": 1.13062,
      "low": 1.13016,
      "close": 1.13061,
      "volume": 523
    },
    {
      "timestamp": "2025-05-01T08:10:00Z",
      "open": 1.1306,
      "high": 1.1307,
      "low": 1.13023,
      "close": 1.1307,
      "volume": 548
    }
  ]
}
```

---

## 2. Strategy Signal Format

### JSON Schema

```json
{
  "pair": "EURUSD",
  "strategy": "range_4h",
  "timestamp": "2023-12-01T10:30:00Z",
  "signals": [
    {
      "id": "signal_001",
      "type": "LONG",
      "entry_price": 1.0785,
      "stop_loss": 1.0765,
      "take_profit": 1.0825,
      "risk_reward": 2.0,
      "position_size": 0.5,
      "reason": "4H range re-entry, bullish bounce from range high",
      "confidence": 0.75,
      "status": "open",
      "entry_time": "2023-12-01T10:30:00Z",
      "exit_time": null,
      "outcome": null,
      "pnl": null
    }
  ]
}
```

**Field Descriptions**:

- `type`: "LONG" or "SHORT"
- `entry_price`: Price to enter position
- `stop_loss`: Stop loss price
- `take_profit`: Take profit price
- `risk_reward`: RR ratio (e.g., 2.0 = 2R)
- `position_size`: Position size in lots
- `reason`: Human-readable entry reason
- `confidence`: AI confidence score (0-1)
- `status`: "open", "closed", "pending"
- `outcome`: "TP", "SL", or null (if still open)
- `pnl`: Profit/loss in account currency

---

## 3. SMC Component Formats

### Order Blocks

```json
{
  "order_blocks": [
    {
      "id": "ob_001",
      "type": "bearish",
      "timeframe": "30M",
      "time_start": "2023-12-01T08:00:00Z",
      "time_end": "2023-12-01T09:00:00Z",
      "price_high": 1.0792,
      "price_low": 1.0785,
      "status": "valid",
      "mitigated": false,
      "swing_type": "swing_high"
    }
  ]
}
```

**Status Values**:

- `valid`: OB has not been mitigated
- `mitigated`: Price has entered OB zone
- `invalidated`: OB no longer relevant

### Liquidity

```json
{
  "liquidity": [
    {
      "id": "liq_001",
      "type": "liquidity_pool",
      "price": 1.0795,
      "time": "2023-12-01T07:00:00Z",
      "swept": false,
      "sweep_time": null
    },
    {
      "id": "liq_002",
      "type": "liquidity_void",
      "price_range": [1.075, 1.0755],
      "filled": false
    }
  ]
}
```

**Liquidity Types**:

- `liquidity_pool`: Area of accumulated stops
- `liquidity_sweep`: Confirmed liquidity grab
- `liquidity_void`: Gap with minimal orders

### Market Structure

```json
{
  "structure": [
    {
      "id": "struct_001",
      "type": "BOS",
      "direction": "bullish",
      "time": "2023-12-01T09:30:00Z",
      "price": 1.08,
      "prev_high": 1.0795
    },
    {
      "id": "struct_002",
      "type": "ChoCH",
      "direction": "bearish",
      "time": "2023-12-01T12:00:00Z",
      "price": 1.077,
      "prev_low": 1.0775
    }
  ]
}
```

**Structure Types**:

- `BOS`: Break of Structure
- `ChoCH`: Change of Character
- `swing_high`: Swing high point
- `swing_low`: Swing low point

### Fair Value Gaps (FVG)

```json
{
  "fvgs": [
    {
      "id": "fvg_001",
      "type": "bullish",
      "time_created": "2023-12-01T10:00:00Z",
      "price_top": 1.079,
      "price_bottom": 1.0782,
      "filled": false,
      "fill_time": null,
      "fill_percentage": 0
    }
  ]
}
```

**FVG Types**:

- `bullish`: Gap created by bullish move
- `bearish`: Gap created by bearish move

---

## 4. Journal/Trade Record Format

```json
{
  "trades": [
    {
      "id": "trade_001",
      "date": "2023-12-01",
      "pair": "EURUSD",
      "strategy": "range_4h",
      "type": "LONG",
      "entry_price": 1.0785,
      "exit_price": 1.0825,
      "stop_loss": 1.0765,
      "take_profit": 1.0825,
      "position_size": 0.5,
      "risk_amount": 250.0,
      "reward_amount": 500.0,
      "risk_reward": 2.0,
      "outcome": "TP",
      "pnl": 500.0,
      "balance_before": 50000.0,
      "balance_after": 50500.0,
      "commission": 0.0,
      "entry_time": "2023-12-01T10:30:00Z",
      "exit_time": "2023-12-01T14:20:00Z",
      "duration_minutes": 230,
      "notes": "Clean 4H range setup, perfect re-entry"
    }
  ]
}
```

---

## 5. Account State Format

```json
{
  "account": {
    "balance": 50500.0,
    "equity": 50500.0,
    "currency": "USD",
    "leverage": 100,
    "margin_used": 0.0,
    "margin_free": 50500.0,
    "open_positions": 0,
    "total_trades": 15,
    "winning_trades": 10,
    "losing_trades": 5,
    "win_rate": 0.667,
    "profit_factor": 2.1,
    "max_drawdown": 1.49,
    "current_drawdown": 0.0,
    "total_pnl": 500.0,
    "total_pnl_percentage": 1.0
  }
}
```

---

## 6. Backtest Results Format

```json
{
  "backtest": {
    "strategy": "range_4h",
    "pair": "EURUSD",
    "start_date": "2023-09-01",
    "end_date": "2023-12-01",
    "starting_balance": 50000.0,
    "ending_balance": 57350.0,
    "total_return": 14.7,
    "max_drawdown": 1.49,
    "total_trades": 113,
    "winning_trades": 73,
    "losing_trades": 40,
    "win_rate": 64.6,
    "average_rr": 1.8,
    "profit_factor": 2.1,
    "sharpe_ratio": 1.87,
    "recovery_factor": 9.87,
    "trades": [
      {
        "date": "2023-09-05",
        "type": "LONG",
        "entry": 1.072,
        "exit": 1.076,
        "outcome": "TP",
        "pnl": 400.0
      }
    ],
    "equity_curve": [
      { "date": "2023-09-01", "equity": 50000.0 },
      { "date": "2023-09-05", "equity": 50400.0 }
    ]
  }
}
```

---

## 7. Configuration Format

### Strategy Configuration

```json
{
  "strategy_config": {
    "range_4h": {
      "enabled": true,
      "pairs": ["EURUSD", "GBPUSD"],
      "session_start": 8,
      "session_end": 16,
      "risk_per_trade": 0.005,
      "target_rr": 2.0,
      "use_swing_filter": true,
      "use_dynamic_tp": false
    }
  }
}
```

### UI Layout Configuration

```json
{
  "layout": {
    "preset": "range_4h",
    "panels": {
      "chart_4h": { "visible": true, "position": "top-left" },
      "chart_5m": { "visible": true, "position": "top-right" },
      "signals": { "visible": true, "position": "bottom-left" },
      "journal": { "visible": true, "position": "bottom-right" }
    },
    "overlays": {
      "ranges": true,
      "positions": true,
      "order_blocks": false,
      "liquidity": false,
      "structure": false
    }
  }
}
```

---

## 8. cTrader API Format

### Historical Data Request

```json
{
  "symbol": "EURUSD",
  "periodicity": "M5",
  "from": "2023-09-01T00:00:00Z",
  "to": "2023-12-01T00:00:00Z"
}
```

### cTrader Response (normalized to standard format)

```json
{
  "symbol": "EURUSD",
  "timeframe": "M5",
  "data": [...]  // Same as OHLCV JSON format
}
```

---

## 9. AI Learning Data Format

### Video Metadata

```json
{
  "video": {
    "id": "knox_welles_ep12",
    "platform": "youtube",
    "url": "https://youtube.com/watch?v=...",
    "title": "London Session Breakdown EP12",
    "author": "Knox Welles",
    "publish_date": "2023-11-15",
    "duration": "00:23:45",
    "transcript": "full transcript...",
    "key_moments": [...]
  }
}
```

### Chart Analysis

```json
{
  "chart_analysis": {
    "image_path": "/research/youtube/knox_welles/ep12_frame_452.png",
    "timestamp": "00:07:32",
    "pair": "EURUSD",
    "timeframe": "M5",
    "ai_annotations": {
      "order_blocks": [...],
      "liquidity": [...],
      "structure": {...},
      "entry_signal": {...}
    }
  }
}
```

---

## 10. API Endpoint Conventions

### Request Format

```
GET /api/{resource}/{action}?param1=value1&param2=value2
POST /api/{resource}
PUT /api/{resource}/{id}
DELETE /api/{resource}/{id}
```

### Response Format

```json
{
  "success": true,
  "data": {...},
  "error": null,
  "timestamp": "2023-12-01T10:30:00Z"
}
```

### Error Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid timeframe: ABC. Must be M1, M5, H1, H4, or D1",
    "details": {}
  },
  "timestamp": "2023-12-01T10:30:00Z"
}
```

---

## Data Validation Rules

### Price Data

- Prices must be positive numbers
- `high >= max(open, close)`
- `low <= min(open, close)`
- Volume >= 0

### Timestamps

- Must be in ISO 8601 format or Unix timestamp
- Must be chronologically ordered
- No gaps larger than expected timeframe

### Signals

- Entry must be between SL and TP
- SL must be on opposite side of entry from TP
- Position size must be > 0
- RR must be > 0

---

_Last Updated: 2025-11-28_
