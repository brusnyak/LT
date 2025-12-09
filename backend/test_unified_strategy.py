#!/usr/bin/env python3
"""
Quick test script for Unified SMC Strategy
This allows fast iteration without waiting for the full API/backtest flow
"""
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.strategies.unified_smc_strategy import UnifiedSMCStrategy
from app.services.data import load_candles

def test_strategy():
    print("=" * 60)
    print("Testing Unified SMC Strategy")
    print("=" * 60)
    
    # Load data
    print("\n1. Loading data...")
    symbol = "EURUSD"
    
    # Load just 3 days for quick testing
    df_h4 = load_candles(symbol, "H4", start="2024-01-01", end="2024-01-03")
    df_m5 = load_candles(symbol, "M5", start="2024-01-01", end="2024-01-03")
    
    print(f"   H4 candles: {len(df_h4)}")
    print(f"   M5 candles: {len(df_m5)}")
    
    # Initialize strategy
    print("\n2. Initializing strategy...")
    strategy = UnifiedSMCStrategy()
    
    # Run analysis
    print("\n3. Running analysis...")
    try:
        result = strategy.analyze(
            df_multi_tf={'H4': df_h4, 'M5': df_m5},
            config={'backtest': True}
        )
        
        print("\n4. Results:")
        print(f"   Signals generated: {len(result['signals'])}")
        
        if 'error' in result:
            print(f"   ERROR: {result['error']}")
        
        if result['signals']:
            print("\n   First 3 signals:")
            for i, sig in enumerate(result['signals'][:3]):
                print(f"   [{i+1}] {sig.time} - {sig.type} @ {sig.price:.5f}")
                print(f"       SL: {sig.sl:.5f}, TP1: {sig.tp:.5f}")
                print(f"       Reason: {sig.reason}")
        
        # Show metadata summary
        print("\n5. Metadata:")
        if 'metadata' in result:
            meta = result['metadata']
            print(f"   H4 Structure Events: {len(meta.get('h4_structure_events', []))}")
            print(f"   H4 PD Zones: {len(meta.get('h4_pd_zones', []))}")
            print(f"   M5 Structure Events: {len(meta.get('m5_structure_events', []))}")
            print(f"   M5 Order Blocks: {len(meta.get('m5_order_blocks', []))}")
            print(f"   M5 FVGs: {len(meta.get('m5_fvgs', []))}")
            if 'technical' in meta:
                tech = meta['technical']
                print(f"   Technical Trend: {tech.get('trend')}")
                print(f"   RSI: {tech.get('rsi'):.2f}")
        
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_strategy()
    sys.exit(0 if success else 1)
