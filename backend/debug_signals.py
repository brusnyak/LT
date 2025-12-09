"""
Debug test to understand why no signals are being generated
"""
import sys
import os
sys.path.append(os.getcwd())

from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range

# Test with GBPUSD since it found 24 ranges
df_4h = load_candle_data("GBPUSD", "H4", limit=500)
df_m15 = load_candle_data("GBPUSD", "M15", limit=3000)

print("="*80)
print("DEBUG: Range and Data Analysis")
print("="*80)

print(f"\n4H Data:")
print(f"  Candles: {len(df_4h)}")
print(f"  Date range: {df_4h['time'].min()} to {df_4h['time'].max()}")
print(f"  Sample times:\n{df_4h[['time']].head()}")

print(f"\nM15 Data:")
print(f"  Candles: {len(df_m15)}")
print(f"  Date range: {df_m15['time'].min()} to {df_m15['time'].max()}")
print(f"  Sample times:\n{df_m15[['time']].head()}")

# Detect ranges
ranges = detect_4h_range(df_4h)
print(f"\n\nRanges Detected: {len(ranges)}")

if ranges:
    print("\nLast 3 ranges:")
    for i, r in enumerate(ranges[-3:]):
        print(f"\nRange {i+1}:")
        print(f"  Date: {r.date}")
        print(f"  Start time: {r.start_time}")
        print(f"  High: {r.high}")
        print(f"  Low: {r.low}")
        print(f"  Size: {r.high - r.low:.5f}")
    
    # Check if range times overlap with M15 data
    range_times = [r.start_time for r in ranges]
    m15_min = df_m15['time'].min()
    m15_max = df_m15['time'].max()
    
    overlapping_ranges = [r for r in ranges if m15_min <= r.start_time <= m15_max]
    print(f"\n\nRanges that overlap with M15 data: {len(overlapping_ranges)}/{len(ranges)}")
    
    if not overlapping_ranges:
        print("\n⚠️  PROBLEM FOUND: No ranges overlap with M15 data timeframe!")
        print(f"   Range times: {min(range_times)} to {max(range_times)}")
        print(f"   M15 times:   {m15_min} to {m15_max}")
        print("\n   This is why no signals are generated - the data doesn't align.")
else:
    print("\n⚠️  No ranges detected at all")
