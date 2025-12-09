"""
Quick diagnostic to check range detection
"""
import sys
import os
import pandas as pd
sys.path.append(os.getcwd())

from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range

# Load recent data
df_4h = load_candle_data("EURUSD", "H4", limit=200)

print("="*80)
print("Range Detection Diagnostic")
print("="*80)

print(f"\nH4 Data loaded: {len(df_4h)} candles")
print(f"Date range: {df_4h['time'].min()} to {df_4h['time'].max()}")

# Check for 00:00 candles
df_4h['hour'] = pd.to_datetime(df_4h['time']).dt.hour
midnight_candles = df_4h[df_4h['hour'] == 0]
print(f"\nMidnight (00:00) candles: {len(midnight_candles)}")

if len(midnight_candles) > 0:
    print(f"Sample midnight candles:\n{midnight_candles[['time']].head()}")

# Try range detection
print(f"\nDetecting ranges...")
ranges = detect_4h_range(df_4h)

print(f"Ranges detected: {len(ranges)}")

if ranges:
    print("\nLast 5 ranges:")
    for r in ranges[-5:]:
        print(f"  Date: {r.date}, High: {r.high}, Low: {r.low}, Start: {r.start_time}")
else:
    print("\n⚠️  No ranges detected!")
    print("\nPossible issues:")
    print("1. Timezone conversion issue")
    print("2. Data format problem")
    print("3. Logic error in detect_4h_range")

import pandas as pd
