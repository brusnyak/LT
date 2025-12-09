# Frontend Specifications (The Cockpit)

## 1. Layout Design

The interface is designed for professional trading analysis.

### 1.1. Main View (Split Screen)

```few adjustments to the layout, right now it's a bit off, implemenetd frontend has container where starred tools can be displayed, located in the header on the right, there is a right panel with signals and trade details,
+---------------------------------------------------------------+
|  Header: [Asset: EURUSD] [TF: 5M] [Strategy: 4H Range]        |
+-----------------------+---------------------------------------+
|                       |                                       |
|  Left Toolbar         |  Chart Area (Split View)              |
|  [Cursor]             |                                       |
|  [Line]               |  +---------------------------------+  |
|  [Fib]                |  |  Left: 4H Context Chart         |  |
|  [Box]                |  |  (Shows Daily Ranges)           |  |
|                       |  +---------------------------------+  |
|                       |                                       |
|                       |  +---------------------------------+  |
|                       |  |  Right: 5M Execution Chart     |  |
|                       |  |  (Shows Entries/Exits)          |  |
|                       |  +---------------------------------+  |
|                       |                                       |
+-----------------------+---------------------------------------+
|  Bottom Panel: [Journal] + [existing tabs]                   |
+---------------------------------------------------------------+
```

## 2. Component Details

### 2.1. Chart Area

- **Library**: `lightweight-charts` (TradingView).
- **Timezone**: Charts must be configured to display time in **UTC+1**.
- **Features**:
  - **Sync**: Crosshair synchronization between Top (4H) and Bottom (5M) charts.
  - **Overlays**: Custom canvas layer (from `useChartOverlay.js`) to draw non-standard elements (Range Boxes, Arrows).

### 2.2. Left Toolbar (Minimalist)

- Icons only (no text labels unless hovered).
- Tools: Cursor, Trendline, Rectangle, Fibonacci, Text.

### 2.3. Right Panel (Collapsible)

- **Signals**: List of recent signals with timestamps.
  - _Example_: `14:35 - Long Entry @ 1.0540`.
- **Trade Details**: If a trade is selected, show SL, TP, RR, and Outcome.

### 2.4. Bottom Panel (Navigation)

- **Tabs**: Journal, Settings, Account.
- **Quick Stats**: Current Balance, Daily PnL, Open Risk.

## 3. Current State vs. Required Changes

- **Current**: Single chart, basic overlays.
- **Required**:
  - Implement **Split View** (CSS Grid/Flexbox).
  - Implement **Chart Synchronization** (TimeScale syncing).
  - Update **Overlay Hook** to handle "Range Box" drawing.
