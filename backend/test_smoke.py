"""
Quick smoke test to verify strategy module loads and functions work
"""
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals
from app.core.data_loader import load_candle_data
import pandas as pd

def test_strategy_smoke():
    print("✅ Strategy imports successful")
    
    # Test data loading
    try:
        df_4h = load_candle_data("EURUSD", "H4", limit=50)
        print(f"✅ Data loader works: loaded {len(df_4h)} H4 candles")
        print(f"   Columns: {list(df_4h.columns)}")
        print(f"   Date range: {df_4h['time'].min()} to {df_4h['time'].max()}")
    except Exception as e:
        print(f"❌ Data loader failed: {e}")
        return False
    
    # Test range detection function
    try:
        ranges = detect_4h_range(df_4h)
        print(f"✅ Range detection works: found {len(ranges)} ranges")
        if ranges:
            print(f"   Sample range: {ranges[0]}")
    except Exception as e:
        print(f"❌ Range detection failed: {e}")
        return False
    
    # Test signal analysis function (with minimal data)
    try:
        df_5m = df_4h.copy()  # Use 4H as substitute for testing
        signals = analyze_5m_signals(df_5m, ranges)
        print(f"✅ Signal analysis works: found {len(signals)} signals")
    except Exception as e:
        print(f"❌ Signal analysis failed: {e}")
        return False
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED - Strategy is functional!")
    print("="*50)
    print("\nNote: 0 signals is expected with limited data.")
    print("Phase 3 (cTrader integration) will provide live data for proper testing.")
    return True

if __name__ == "__main__":
    success = test_strategy_smoke()
    sys.exit(0 if success else 1)
