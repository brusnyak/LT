"""
Debug script to understand why detect_4h_range only returns 1 range
"""
import pandas as pd
from pathlib import Path
from datetime import timedelta
from app.models.strategy import RangeLevel

DATA_DIR = Path("/Users/yegor/Documents/Agency & Security Stuff/Development/SMC/archive/charts/forex")

# Load 4H data
df_4h = pd.read_csv(
    DATA_DIR / "EURUSD240.csv",
    sep='\t',
    header=None,
    names=['time', 'open', 'high', 'low', 'close', 'volume']
)

print(f"Loaded {len(df_4h)} rows")
print(f"First 5 rows:\n{df_4h.head()}")
print(f"\nLast 5 rows:\n{df_4h.tail()}")

# Convert time
df_4h['time'] = pd.to_datetime(df_4h['time'])
if df_4h['time'].dt.tz is None:
    df_4h['time'] = df_4h['time'].dt.tz_localize('UTC')

print(f"\nAfter datetime conversion:")
print(f"First time: {df_4h['time'].iloc[0]}")
print(f"Last time: {df_4h['time'].iloc[-1]}")

# Set index
df_4h = df_4h.set_index('time')

# Add date column
df_4h['date'] = df_4h.index.date

print(f"\nUnique dates: {len(df_4h['date'].unique())}")
print(f"First 10 dates: {df_4h['date'].unique()[:10]}")
print(f"Last 10 dates: {df_4h['date'].unique()[-10:]}")

# Test range detection
ranges = []
for date in df_4h['date'].unique():
    day_data = df_4h[df_4h['date'] == date]
    
    if not day_data.empty:
        candle = day_data.iloc[0]
        start_time = candle.name
        end_time = start_time + timedelta(hours=4)
        
        r = RangeLevel(
            date=str(date),
            high=candle['high'],
            low=candle['low'],
            start_time=start_time,
            end_time=end_time
        )
        ranges.append(r)

print(f"\nDetected {len(ranges)} ranges")
print(f"First 5 ranges:")
for r in ranges[:5]:
    print(f"  {r.date}: {r.start_time} - {r.end_time}, H:{r.high}, L:{r.low}")
