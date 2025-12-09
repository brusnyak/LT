#!/usr/bin/env python3
"""
SIMPLE Unified Strategy Test
No loops, no complex backtest engine - just process CSV data directly
"""
import sys
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.smc.swings import SwingDetector
from app.smc.market_structure import MarketStructureDetector
from app.smc.order_blocks import OrderBlockDetector
from app.smc.fvg import FVGDetector
from app.models.strategy import Signal

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Simple EMA calculation"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Simple RSI calculation"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def test_simple_strategy():
    print("=" * 60)
    print("Simple Unified Strategy Test")
    print("=" * 60)
    
    # Load CSV data directly
    print("\n1. Loading CSV data...")
    data_path = Path(__file__).parent.parent / "archive" / "data" / "EURUSD_M5.csv"
    
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        return False
    
    df = pd.read_csv(data_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time').sort_index()
    
    # Take just January 2024 for quick test
    df = df['2024-01-01':'2024-01-05']
    print(f"   Loaded {len(df)} candles (Jan 1-5, 2024)")
    
    # Calculate indicators
    print("\n2. Calculating indicators...")
    df['ema_50'] = calculate_ema(df['close'], 50)
    df['ema_200'] = calculate_ema(df['close'], 200)
    df['rsi'] = calculate_rsi(df['close'], 14)
    
    # Remove NaN rows from EMA calculation
    df = df.dropna()
    print(f"   Valid candles after warmup: {len(df)}")
    
    # Detect swings
    print("\n3. Detecting swing points...")
    swing_detector = SwingDetector(lookback_left=10, lookback_right=10)
    swing_data = swing_detector.get_swing_data(df)
    swing_highs = swing_data['swing_highs']
    swing_lows = swing_data['swing_lows']
    classified_swings = swing_data['classified_swings']
    print(f"   Found {len(swing_highs)} swing highs, {len(swing_lows)} swing lows")
    
    # Detect market structure
    print("\n4. Detecting market structure...")
    ms_detector = MarketStructureDetector()
    structure_events = ms_detector.detect_structure(df, classified_swings)
    print(f"   Found {len(structure_events)} structure events (BOS/CHOCH)")
    for e in structure_events[:3]:
        print(f"      {e.timestamp}: {e.type} {e.direction}")
    
    # Detect Order Blocks
    print("\n5. Detecting Order Blocks...")
    ob_detector = OrderBlockDetector(lookback_window=20)
    order_blocks = ob_detector.detect_order_blocks(df, structure_events)
    order_blocks = ob_detector.update_ob_states(df, order_blocks)
    print(f"   Found {len(order_blocks)} order blocks")
    active_obs = [ob for ob in order_blocks if ob.state in ['active', 'touched', 'partial']]
    print(f"   Active/Touched: {len(active_obs)}")
    
    # Detect FVGs
    print("\n6. Detecting FVGs...")
    fvg_detector = FVGDetector()
    fvgs = fvg_detector.detect_fvgs(df, use_auto_threshold=True)
    print(f"   Found {len(fvgs)} Fair Value Gaps")
    unmitigated_fvgs = [fvg for fvg in fvgs if fvg.mitigation_level < 4]
    print(f"   Unmitigated: {len(unmitigated_fvgs)}")
    
    # Simple signal logic
    print("\n7. Generating signals...")
    signals = []
    
    # Determine current trend from last structure event
    current_trend = 'ranging'
    if structure_events:
        last_event = structure_events[-1]
        if last_event.type in ['BOS', 'CHOCH']:
            current_trend = last_event.direction
    
    print(f"   Current trend: {current_trend}")
    
    # Get current state (last candle)
    current_idx = -1
    current_price = df['close'].iloc[current_idx]
    current_rsi = df['rsi'].iloc[current_idx]
    current_ema_50 = df['ema_50'].iloc[current_idx]
    current_ema_200 = df['ema_200'].iloc[current_idx]
    current_time = df.index[current_idx]
    
    print(f"   Current price: {current_price:.5f}")
    print(f"   EMA 50: {current_ema_50:.5f}, EMA 200: {current_ema_200:.5f}")
    print(f"   RSI: {current_rsi:.2f}")
    
    # Simple LONG entry conditions
    if current_trend == 'bullish':
        # Price > EMA200 and RSI not overbought
        if current_price > current_ema_200 and current_rsi < 70:
            # Check if near an active bullish OB
            for ob in active_obs:
                if ob.type == 'bullish' and ob.low <= current_price <= ob.high:
                    # Simple 2R setup
                    sl = ob.low - 0.0010  # 10 pips below OB
                    risk = abs(current_price - sl)
                    tp1 = current_price + (risk * 2.0)
                    tp2 = current_price + (risk * 3.0)
                    
                    signals.append(Signal(
                        time=current_time,
                        type='LONG',
                        price=current_price,
                        sl=sl,
                        tp=tp1,
                        tp2=tp2,
                        reason=f"Bullish trend, at OB, RSI {current_rsi:.1f}"
                    ))
                    print(f"\n   ✅ LONG signal generated!")
                    print(f"      Entry: {current_price:.5f}")
                    print(f"      SL: {sl:.5f} | TP1: {tp1:.5f} | TP2: {tp2:.5f}")
                    print(f"      Risk: {risk*10000:.1f} pips | RR: 2.0")
                    break
    
    # Simple SHORT entry conditions
    elif current_trend == 'bearish':
        # Price < EMA200 and RSI not oversold
        if current_price < current_ema_200 and current_rsi > 30:
            # Check if near an active bearish OB
            for ob in active_obs:
                if ob.type == 'bearish' and ob.low <= current_price <= ob.high:
                    # Simple 2R setup
                    sl = ob.high + 0.0010  # 10 pips above OB
                    risk = abs(current_price - sl)
                    tp1 = current_price - (risk * 2.0)
                    tp2 = current_price - (risk * 3.0)
                    
                    signals.append(Signal(
                        time=current_time,
                        type='SHORT',
                        price=current_price,
                        sl=sl,
                        tp=tp1,
                        tp2=tp2,
                        reason=f"Bearish trend, at OB, RSI {current_rsi:.1f}"
                    ))
                    print(f"\n   ✅ SHORT signal generated!")
                    print(f"      Entry: {current_price:.5f}")
                    print(f"      SL: {sl:.5f} | TP1: {tp1:.5f} | TP2: {tp2:.5f}")
                    print(f"      Risk: {risk*10000:.1f} pips | RR: 2.0")
                    break
    
    if not signals:
        print("   ℹ️  No signals - conditions not met")
        print(f"      Trend ({current_trend}) + Technical filters + OB proximity all required")
    
    print("\n" + "=" * 60)
    print(f"Test completed! Generated {len(signals)} signal(s)")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_simple_strategy()
    sys.exit(0 if success else 1)
