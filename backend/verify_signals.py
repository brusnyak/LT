"""
Signal Verification Script
Tests both Range 4H and MTF 30/1 strategies to verify signal generation
"""
from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals
from app.strategies.mtf_30_1 import MTF30_1Strategy

def test_range_4h_strategy(pair='EURUSD'):
    """Test Range 4H Strategy"""
    print(f"\n{'='*60}")
    print(f"Testing Range 4H Strategy for {pair}")
    print(f"{'='*60}\n")
    
    try:
        # Load data
        df_4h = load_candle_data(pair, "H4", limit=1000)
        df_5m = load_candle_data(pair, "M5", limit=5000)
        
        print(f"✓ Loaded {len(df_4h)} 4H candles")
        print(f"✓ Loaded {len(df_5m)} 5M candles")
        
        # Detect ranges
        ranges = detect_4h_range(df_4h)
        print(f"✓ Detected {len(ranges)} 4H ranges")
        
        # Analyze signals
        signals = analyze_5m_signals(df_5m, ranges)
        print(f"✓ Generated {len(signals)} signals\n")
        
        # Display signals
        if signals:
            print("Signals:")
            for i, signal in enumerate(signals[:5], 1):  # Show first 5
                # Handle both dict and Pydantic models
                if hasattr(signal, 'type'):
                    # Pydantic model
                    print(f"\n  Signal {i}:")
                    print(f"    Type: {signal.type}")
                    print(f"    Price: {signal.price}")
                    print(f"    SL: {signal.sl}")
                    print(f"    TP: {signal.tp}")
                    print(f"    Time: {signal.time}")
                    if hasattr(signal, 'reason'):
                        print(f"    Reason: {signal.reason}")
                else:
                    # Dict
                    print(f"\n  Signal {i}:")
                    print(f"    Type: {signal.get('type', 'N/A')}")
                    print(f"    Price: {signal.get('price', 'N/A')}")
                    print(f"    SL: {signal.get('sl', 'N/A')}")
                    print(f"    TP: {signal.get('tp', 'N/A')}")
                    print(f"    Time: {signal.get('time', 'N/A')}")
                    if 'reason' in signal:
                        print(f"    Reason: {signal['reason']}")
            
            if len(signals) > 5:
                print(f"\n  ... and {len(signals) - 5} more signals")
        else:
            print("  ⚠ No signals generated")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mtf_30_1_strategy(pair='EURUSD'):
    """Test MTF 30/1 Strategy"""
    print(f"\n{'='*60}")
    print(f"Testing MTF 30/1 Strategy for {pair}")
    print(f"{'='*60}\n")
    
    try:
        # Load data
        df_4h = load_candle_data(pair, "H4", limit=1000)
        df_30m = load_candle_data(pair, "M30", limit=2000)
        df_1m = load_candle_data(pair, "M1", limit=5000)
        
        print(f"✓ Loaded {len(df_4h)} 4H candles")
        print(f"✓ Loaded {len(df_30m)} 30M candles")
        print(f"✓ Loaded {len(df_1m)} 1M candles")
        
        # Run strategy
        strategy = MTF30_1Strategy()
        result = strategy.analyze({
            'H4': df_4h,
            '30M': df_30m,
            '1M': df_1m
        })
        
        signals = result.get('signals', [])
        metadata = result.get('metadata', {})
        
        print(f"✓ Trend: {metadata.get('trend', 'N/A')}")
        print(f"✓ POIs: {len(metadata.get('pois', []))}")
        print(f"✓ Generated {len(signals)} signals\n")
        
        # Display signals
        if signals:
            print("Signals:")
            for i, signal in enumerate(signals[:5], 1):  # Show first 5
                print(f"\n  Signal {i}:")
                print(f"    Type: {signal.type}")
                print(f"    Price: {signal.price}")
                print(f"    SL: {signal.sl}")
                print(f"    TP: {signal.tp}")
                print(f"    Time: {signal.time}")
                print(f"    Reason: {signal.reason}")
            
            if len(signals) > 5:
                print(f"\n  ... and {len(signals) - 5} more signals")
        else:
            print("  ⚠ No signals generated")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SMC Signal Verification")
    print("="*60)
    
    # Test both strategies
    pairs = ['EURUSD']  # Can add more pairs: ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    results = {}
    for pair in pairs:
        results[f"{pair}_range_4h"] = test_range_4h_strategy(pair)
        results[f"{pair}_mtf_30_1"] = test_mtf_30_1_strategy(pair)
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        sys.exit(1)
