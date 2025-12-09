"""
Quick script to check data overlap and understand why we're getting 0 signals
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path("/Users/yegor/Documents/Agency & Security Stuff/Development/SMC/archive/charts/forex")

# Load EURUSD data
df_4h = pd.read_csv(
    DATA_DIR / "EURUSD240.csv",
    sep=r'\s+',
    header=None,
    names=['time', 'open', 'high', 'low', 'close', 'volume']
)
df_5m = pd.read_csv(DATA_DIR / "EURUSD5.csv")
df_5m.columns = df_5m.columns.str.lower()

df_4h['time'] = pd.to_datetime(df_4h['time'], utc=True)
df_5m['time'] = pd.to_datetime(df_5m['time'], utc=True)

print("4H Data:")
print(f"  Rows: {len(df_4h)}")
print(f"  Range: {df_4h['time'].min()} to {df_4h['time'].max()}")
print(f"  Days: {(df_4h['time'].max() - df_4h['time'].min()).days}")

print("\n5M Data:")
print(f"  Rows: {len(df_5m)}")
print(f"  Range: {df_5m['time'].min()} to {df_5m['time'].max()}")
print(f"  Days: {(df_5m['time'].max() - df_5m['time'].min()).days}")

# Find overlap
overlap_start = max(df_4h['time'].min(), df_5m['time'].min())
overlap_end = min(df_4h['time'].max(), df_5m['time'].max())

print(f"\nOverlap:")
print(f"  Range: {overlap_start} to {overlap_end}")
print(f"  Days: {(overlap_end - overlap_start).days}")

# Filter to overlap
df_4h_overlap = df_4h[(df_4h['time'] >= overlap_start) & (df_4h['time'] <= overlap_end)]
df_5m_overlap = df_5m[(df_5m['time'] >= overlap_start) & (df_5m['time'] <= overlap_end)]

print(f"\n4H rows in overlap: {len(df_4h_overlap)}")
print(f"5M rows in overlap: {len(df_5m_overlap)}")

# Check unique dates in overlap
unique_dates_4h = df_4h_overlap['time'].dt.date.unique()
unique_dates_5m = df_5m_overlap['time'].dt.date.unique()

print(f"\nUnique dates in 4H overlap: {len(unique_dates_4h)}")
print(f"Unique dates in 5M overlap: {len(unique_dates_5m)}")
print(f"\nFirst 10 dates in 4H: {unique_dates_4h[:10]}")
print(f"First 10 dates in 5M: {unique_dates_5m[:10]}")
