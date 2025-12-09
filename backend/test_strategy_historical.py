"""
Test strategy on larger historical dataset to find trending periods
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.data_loader import load_candle_data
from app.strategies.human_trained_strategy import HumanTrainedStrategy

def test_strategy_historical():
    print("🧪 Testing HumanTrainedStrategy on larger historical dataset\n")
    
    # Test on EURUSD with MORE data
    pair = "EURUSD"
    print(f"Loading LARGER dataset for {pair}...")
    
    # Load much more data to cover different market conditions
    df_h4 = load_candle_data(pair, "H4", limit=5000)   # ~833 days
    df_m15 = load_candle_data(pair, "M15", limit=50000) # ~520 days  
    df_m5 = load_candle_data(pair, "M5", limit=150000)  # ~520 days
    
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
        print(f"\n  First 10 signals:")
        for i, sig in enumerate(signals[:10]):
            print(f"    {i+1}. {sig['type']} @ {sig.get('entry', 'N/A'):.5f} | SL: {sig.get('sl', 'N/A'):.5f} | TP: {sig.get('tp', 'N/A'):.5f} | R:R: {sig.get('rr', 'N/A'):.2f}")
            print(f"       Time: {sig.get('time', 'N/A')} | Structure: {sig.get('structure', 'N/A')}")
    else:
        print("  ⚠️ Still no signals - market may be ranging for entire period")

if __name__ == "__main__":
    test_strategy_historical()
