# Strategy Definitions

## 1. The "4H Range" Strategy (V1 Priority)

**Concept**: Scalping the 5-minute timeframe based on the first 4-hour candle of the day (New York Time).

### 1.1. Core Rules

1.  **Timezone**: All analysis and chart display are based on **UTC+1** (Central European Time).
    - **Decision**: Strategy logic uses **UTC+1**. The "First 4H Candle" is the one starting at 00:00 UTC+1.
2.  **The Range**:
    - Identify the **first 4-hour candle** of the trading day (00:00 - 04:00 UTC+1).
    - Mark its **High** and **Low**.
    - This creates a "Range Box" that extends to the end of the day (23:59 UTC+1).
3.  **The Setup (Breakout & Re-entry)**:
    - **Breakout**: A 5-minute candle must **CLOSE** outside the range.
      - _Note_: Wicks do not count. Must be a body close.
    - **Re-entry**: A subsequent 5-minute candle must **CLOSE** back inside the range.
4.  **Entry Trigger**:
    - **Long**: Price broke **below** Range Low, then closed **back inside**.
      - Entry: On the close of the re-entry candle.
    - **Short**: Price broke **above** Range High, then closed **back inside**.
      - Entry: On the close of the re-entry candle.

### 1.2. Optimized Rules (V5 Final)

1.  **Trend Filter (New)**:

    - **Long**: Price must be **ABOVE** the 200 EMA.
    - **Short**: Price must be **BELOW** the 200 EMA.
    - _Why_: Ensures we only trade with the dominant momentum.

2.  **Entry Trigger (Swing Filter)**:

    - **Standard**: Breakout + Re-entry Close.
    - **Optimization**: Entry is only valid if price is near a recent **Swing Point** (Order Block proxy).
      - _Long_: Re-entry near a recent Swing Low.
      - _Short_: Re-entry near a recent Swing High.
      - _Why_: Filters out weak reversals in the middle of nowhere.

3.  **Risk Management**:
    - **Stop Loss (SL)**: Swing High/Low of the breakout move.
    - **Take Profit (TP)**: **Dynamic Structure-Based**.
      - Target 1: Nearest **Fair Value Gap (FVG)** (50% fill).
      - Target 2: Nearest **Liquidity Zone** (Swing High/Low).
      - **Constraint**: Minimum Reward-to-Risk (RR) of **3.0R**.
      - **Fallback**: If no structure found, use fixed **3R**.
    - **Position Sizing**: 0.5-1% Risk per Trade (flexible for optimization).

### 1.3. Performance Targets (New Project Goals)

- **Win Rate**: **+90%**
- **Avg RR**: **Min 3R**
- **Max Drawdown**: **1-2%**
- **Total P&L**: **+20%**

### 1.4. Visualization Requirements

- **4H Chart**:
  - Highlight the "First 4H Candle".
  - Draw horizontal lines for High/Low extending to the right.
- **5M Chart**:
  - Show the same High/Low lines.
  - **Signal**: Plot an arrow (Green/Red) on the Re-entry candle.
  - **Trade**: Visualize the Entry, SL, and TP lines. like long/short positions in TradingView.

---

## 2. Future Strategies (Backlog)

- **SMC Session Profiles**: London Swing to NY Reversal.
- **Classic Buy/Sell Days**: Trend continuation models.
-
- **Note**: These are complex, context-heavy strategies reserved for V2.
