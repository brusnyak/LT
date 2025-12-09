"""
Simple test script to verify HumanTrainedStrategy generates signals
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.data_loader import load_candle_data
from app.strategies.human_trained_strategy import HumanTrainedStrategy

def test_strategy():
    print("🧪 Testing HumanTrainedStrategy in isolation\n")
    
    # Test on EURUSD
    pair = "EURUSD"
    print(f"Loading data for {pair}...")
    
    # Load data for all timeframes
    df_h4 = load_candle_data(pair, "H4", limit=1000)
    df_m15 = load_candle_data(pair, "M15", limit=5000)
    df_m5 = load_candle_data(pair, "M5", limit=15000)
    
    print(f"✅ Loaded data:")
    print(f"  H4: {len(df_h4)} candles ({df_h4.index[0]} to {df_h4.index[-1]})")
    print(f"  M15: {len(df_m15)} candles ({df_m15.index[0]} to {df_m15.index[-1]})")
    print(f"  M5: {len(df_m5)} candles ({df_m5.index[0]} to {df_m5.index[-1]})")
    
    # Initialize strategy
    strategy = HumanTrainedStrategy()
    
    # Generate signals
    print(f"\n🔍 Generating signals...")
    signals = strategy.generate_signals(pair, df_h4, df_m15, df_m5)
    
    print(f"\n📊 Results:")
    print(f"  Total signals: {len(signals)}")
    
    if signals:
        print(f"\n  Sample signals:")
        for i, sig in enumerate(signals[:5]):  # Show first 5
            print(f"    {i+1}. {sig['type']} @ {sig.get('entry', 'N/A')} | SL: {sig.get('sl', 'N/A')} | TP: {sig.get('tp', 'N/A')} | R:R: {sig.get('rr', 'N/A'):.2f}")
            print(f"       Time: {sig.get('time', 'N/A')} | Structure: {sig.get('structure', 'N/A')}")
    else:
        print("  ⚠️ No signals generated")
        print("\n  Debugging info:")
        # Run with debug prints
        structure = strategy.identify_structure(df_h4)
        print(f"    Structure trend: {structure.get('trend')}")
        print(f"    Swing highs: {len(structure.get('swings', {}).get('highs', []))}")
        print(f"    Swing lows: {len(structure.get('swings', {}).get('lows', []))}")
        
        shift = strategy.detect_shift(df_m15, structure)
        print(f"    Shift detected: {shift.get('shift_detected')}")
        if shift.get('shift_detected'):
            print(f"    Shift type: {shift.get('type')}")

if __name__ == "__main__":
    test_strategy()
