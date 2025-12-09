import pandas as pd
from datetime import datetime, timedelta
from app.strategies.range_4h import analyze_5m_signals, RangeLevel
from app.models.strategy import Signal

def test_strategy_logic():
    print("Testing Strategy Logic (Multi-Target TP)...")
    
    # 1. Create Dummy Data
    dates = pd.date_range(start='2025-01-01 00:00', periods=100, freq='5min', tz='UTC')
    df_5m = pd.DataFrame({
        'time': dates,
        'open': 1.1000,
        'high': 1.1010,
        'low': 1.0990,
        'close': 1.1000,
        'volume': 100
    })
    df_5m = df_5m.set_index('time')
    
    # Create a range
    r = RangeLevel(
        date='2025-01-01',
        high=1.1020,
        low=1.0980,
        start_time=dates[0],
        end_time=dates[12*4] # 4 hours
    )
    
    # 2. Simulate a LONG Signal
    # Price breaks low (1.0970) then closes back inside (1.0985)
    
    # Breakout Low
    idx_break = 60
    df_5m.iloc[idx_break, df_5m.columns.get_loc('low')] = 1.0970
    df_5m.iloc[idx_break, df_5m.columns.get_loc('close')] = 1.0975 # Close below low
    
    # Re-entry
    idx_entry = 61
    entry_time = df_5m.index[idx_entry]
    df_5m.iloc[idx_entry, df_5m.columns.get_loc('close')] = 1.0985 # Close back inside
    df_5m.iloc[idx_entry, df_5m.columns.get_loc('low')] = 1.0975
    
    # 3. Simulate TP1 Hit
    # Entry: 1.0985, SL: 1.0975 (Low of entry candle? No, SL is usually Low of range or swing)
    # In code: sl = low (of current range? No, low of candle?)
    # Code says: sl = low (of current candle for Long) -> 1.0975
    # Risk = 10 pips (0.0010)
    # TP1 (2R) = 1.0985 + 0.0020 = 1.1005
    # TP2 (3R) = 1.0985 + 0.0030 = 1.1015
    
    idx_tp1 = 70
    df_5m.iloc[idx_tp1, df_5m.columns.get_loc('high')] = 1.1006 # Hit TP1
    
    # 4. Simulate TP2 Hit
    idx_tp2 = 80
    df_5m.iloc[idx_tp2, df_5m.columns.get_loc('high')] = 1.1016 # Hit TP2
    
    # Run Analysis
    print("Running analysis...")
    signals = analyze_5m_signals(
        df_5m, 
        [r], 
        use_dynamic_tp=False, # Use fixed 2R/3R for deterministic test
        use_swing_filter=False,
        use_trend_filter=False
    )
    
    print(f"Signals found: {len(signals)}")
    
    if not signals:
        print("✗ No signals found!")
        return
        
    sig = signals[0]
    print(f"Signal Type: {sig.type}")
    print(f"Entry: {sig.price}")
    print(f"TP1: {sig.tp}")
    print(f"TP2: {sig.tp2}")
    print(f"Status: {sig.status}")
    print(f"Outcome: {sig.outcome}")
    
    # Verify
    if sig.tp2 is None:
        print("✗ TP2 is missing")
    else:
        print("✓ TP2 is present")
        
    if sig.outcome == 'TP2_HIT':
        print("✓ Outcome is TP2_HIT (Full Win)")
    elif sig.outcome == 'TP1_HIT':
        print("⚠ Outcome is TP1_HIT (Partial Win) - Did it not reach TP2?")
    else:
        print(f"✗ Unexpected outcome: {sig.outcome}")

if __name__ == "__main__":
    test_strategy_logic()
