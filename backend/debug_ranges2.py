"""
Test range detection with debug output
"""
import sys, os, pandas as pd
sys.path.append(os.getcwd())

from app.core.data_loader import load_candle_data
import pytz
from datetime import timedelta

# Load data
df_4h = load_candle_data("EURUSD", "H4", limit=50)

print("Raw data (first 10 rows):")
print(df_4h[['time']].head(10))

# Manually process like detect_4h_range does
print("\n" + "="*80)
print("Processing like detect_4h_range...")
print("="*80)

# Convert time to datetime and localize
df_4h['time'] = pd.to_datetime(df_4h['time'], utc=True)
df_4h = df_4h.set_index('time')

print(f"\nAfter UTC localization:")
print(f"Index timezone: {df_4h.index.tz}")
print(df_4h.index[:10])

# Convert to Bratislava timezone
target_timezone = pytz.timezone('Europe/Bratislava')
df_4h_localized = df_4h.tz_convert(target_timezone)

print(f"\nAfter Bratislava conversion:")
print(df_4h_localized.index[:10])

# Get unique dates
unique_dates = df_4h_localized.index.normalize().unique()
print(f"\nUnique dates: {len(unique_dates)}")
print(unique_dates[:5])

# Check for 00:00 candles in Bratislava time
ranges_found = 0
for date in unique_dates[:5]:
    day_data = df_4h_localized[df_4h_localized.index.date == date.date()]
    first_candle_of_day = day_data[day_data.index.hour == 0]
    
    print(f"\nDate: {date.date()}")
    print(f"  Day data: {len(day_data)} candles")
    print(f"  Hours in day: {day_data.index.hour.unique()}")
    print(f"  00:00 candles: {len(first_candle_of_day)}")
    
    if not first_candle_of_day.empty:
        print(f"  ✅ Range found!")
        ranges_found += 1

print(f"\n{'='*80}")
print(f"Total ranges found: {ranges_found}")
