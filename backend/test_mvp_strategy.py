#!/usr/bin/env python3
"""
Quick Test for MVP Unified Strategy
Tests the strategy with real CSV data
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.strategies.unified_mvp import UnifiedMVPStrategy
from app.core.data_loader import load_candle_data

def test_mvp_strategy():
    print("=" * 70)
    print("MVP Unified Strategy - Test Run")
    print("=" * 70)
    
    # Load multi-timeframe data
    print("\n1. Loading multi-timeframe data...")
    try:
        # Use last 200 H4, 500 M15, 1000 M5 candles
        df_h4 = load_candle_data('EURUSD', 'H4', limit=200)
        df_m15 = load_candle_data('EURUSD', 'M15', limit=500)
        df_m5 = load_candle_data('EURUSD', 'M5', limit=1000)
        
        print(f"   ✅ H4: {len(df_h4)} candles")
        print(f"   ✅ M15: {len(df_m15)} candles")
        print(f"   ✅ M5: {len(df_m5)} candles")
        
        # Show date range
        print(f"\n   Date range: {df_m5.index[0]} to {df_m5.index[-1]}")
        
    except Exception as e:
        print(f"   ❌ Error loading data: {e}")
        return False
    
    # Initialize strategy
    print("\n2. Initializing MVP Unified Strategy...")
    try:
        strategy = UnifiedMVPStrategy()
        print("   ✅ Strategy initialized")
    except Exception as e:
        print(f"   ❌ Error initializing strategy: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Run analysis
    print("\n3. Running multi-timeframe analysis...")
    try:
        result = strategy.analyze({
            'H4': df_h4,
            'M15': df_m15,
            'M5': df_m5
        }, config={})
        
        print("   ✅ Analysis complete")
        
    except Exception as e:
        print(f"   ❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Display results
    print("\n4. Results:")
    print("-" * 70)
    
    # Metadata
    metadata = result.get('metadata', {})
    print(f"\n   H4 Trend: {metadata.get('h4_trend', 'N/A').upper()}")
    print(f"   H4 Swings: {metadata.get('h4_swing_count', 0)}")
    print(f"   M15 Internal Trend: {metadata.get('m15_internal_trend', 'N/A').upper()}")
    print(f"   M15 Quality OBs: {metadata.get('m15_quality_obs', 0)}")
    print(f"   M15 Liquidity Zones: {metadata.get('m15_liquidity_zones', 0)}")
    print(f"   Entry Timeframe: {metadata.get('entry_timeframe', 'N/A')}")
    
    # Signals
    signals = result.get('signals', [])
    print(f"\n   Signals Generated: {len(signals)}")
    
    if signals:
        print("\n   Signal Details:")
        print("   " + "-" * 66)
        for i, sig in enumerate(signals[:5]):  # Show first 5
            print(f"\n   [{i+1}] {sig.type} Signal")
            print(f"       Time: {sig.time}")
            print(f"       Entry: {sig.price:.5f}")
            print(f"       SL: {sig.sl:.5f} (Risk: {abs(sig.price - sig.sl)*10000:.1f} pips)")
            print(f"       TP1: {sig.tp:.5f} (RR: {abs(sig.tp - sig.price)/abs(sig.price - sig.sl):.2f})")
            if sig.tp2:
                print(f"       TP2: {sig.tp2:.5f} (RR: {abs(sig.tp2 - sig.price)/abs(sig.price - sig.sl):.2f})")
            print(f"       Reason: {sig.reason}")
    else:
        print("\n   ℹ️  No signals - Market conditions didn't meet criteria")
        print("       This is normal - strategy is selective for quality setups")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = test_mvp_strategy()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
