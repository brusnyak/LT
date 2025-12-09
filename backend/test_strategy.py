import pandas as pd

from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals

def test_strategy():
    print("Loading data...")
    try:
        df_4h = load_candle_data("EURUSD", "H4", limit=1000)
        df_5m = load_candle_data("EURUSD", "M5", limit=5000)
        print(f"Loaded {len(df_4h)} 4H candles and {len(df_5m)} 5M candles.")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("\nDetecting Ranges...")
    ranges = detect_4h_range(df_4h)
    print(f"Found {len(ranges)} ranges.")
    if ranges:
        print("Last 3 ranges:")
        for r in ranges[-3:]:
            print(f"  Date: {r.date}, High: {r.high}, Low: {r.low}, Start: {r.start_time}")

    print("\nAnalyzing Signals...")
    signals = analyze_5m_signals(df_5m, ranges)
    print(f"Found {len(signals)} signals.")
    if signals:
        print("Last 3 signals:")
        for s in signals[-3:]:
            print(f"  Time: {s.time}, Type: {s.type}, Price: {s.price}, Reason: {s.reason}")

if __name__ == "__main__":
    test_strategy()
