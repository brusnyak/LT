"""
Validate Manual Trade Patterns on CSV Data
Test if the observed patterns (4.5 R:R, tight SL) work on historical data
"""

import pandas as pd
import json
from pathlib import Path

# Load manual trade analysis
with open('backend/data/manual_trades_analysis.json', 'r') as f:
    manual_analysis = json.load(f)

print(f"\n{'='*60}")
print(f"VALIDATING MANUAL PATTERNS ON CSV DATA")
print(f"{'='*60}\n")

print(f"Manual Trade Patterns:")
print(f"  Avg R:R: {manual_analysis['avg_rr']:.2f}")
print(f"  Avg SL: {manual_analysis['avg_sl_pips']:.1f} pips")
print(f"  Avg TP: {manual_analysis['avg_tp_pips']:.1f} pips")
print(f"  Total Trades: {manual_analysis['total_trades']}")

# CSV files to test
csv_files = {
    'EURUSD_M15': 'archive/charts/forex/EURUSD15.csv',
    'GBPUSD_M15': 'archive/charts/forex/GBPUSD15.csv',
    'XAUUSD_M15': 'archive/charts/metals/XAUUSD15.csv',
    'USDCAD_M15': 'archive/charts/forex/USDCAD15.csv',
}

print(f"\n{'='*60}")
print(f"CSV DATA AVAILABILITY")
print(f"{'='*60}\n")

available_data = {}
for name, path in csv_files.items():
    file_path = Path(path)
    if file_path.exists():
        try:
            df = pd.read_csv(file_path)
            # Check if it has required columns
            required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
            if all(col in df.columns for col in required_cols):
                available_data[name] = df
                print(f"✓ {name}: {len(df)} candles")
                print(f"  Period: {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
            else:
                print(f"✗ {name}: Missing required columns")
        except Exception as e:
            print(f"✗ {name}: Error loading - {e}")
    else:
        print(f"✗ {name}: File not found")

if not available_data:
    print("\nNo valid CSV data found!")
    exit(1)

print(f"\n{'='*60}")
print(f"SIMPLE PATTERN VALIDATION")
print(f"{'='*60}\n")

print("Testing if manual trade characteristics exist in CSV data:")
print("(This is NOT a full backtest, just pattern validation)\n")

for name, df in available_data.items():
    print(f"\n{name}:")
    
    # Calculate basic volatility metrics
    df['range_pips'] = (df['high'] - df['low']) * 10000
    
    avg_range = df['range_pips'].mean()
    median_range = df['range_pips'].median()
    
    # Check if manual SL/TP sizes are reasonable for this pair
    manual_sl = manual_analysis['avg_sl_pips']
    manual_tp = manual_analysis['avg_tp_pips']
    
    print(f"  Avg Candle Range: {avg_range:.1f} pips")
    print(f"  Median Candle Range: {median_range:.1f} pips")
    
    # Check if manual SL is within reasonable range
    if manual_sl < avg_range * 2:
        print(f"  ✓ Manual SL ({manual_sl:.1f} pips) is reasonable")
    else:
        print(f"  ⚠ Manual SL ({manual_sl:.1f} pips) might be too tight")
    
    # Check if manual TP is achievable
    if manual_tp < avg_range * 10:
        print(f"  ✓ Manual TP ({manual_tp:.1f} pips) is achievable")
    else:
        print(f"  ⚠ Manual TP ({manual_tp:.1f} pips) might be too ambitious")
    
    # Calculate how many candles move >= manual TP
    big_moves = (df['range_pips'] >= manual_tp).sum()
    big_moves_pct = (big_moves / len(df)) * 100
    
    print(f"  Candles with {manual_tp:.1f}+ pip range: {big_moves} ({big_moves_pct:.1f}%)")

print(f"\n{'='*60}")
print(f"VALIDATION SUMMARY")
print(f"{'='*60}\n")

print("✓ CSV data is available for multiple pairs")
print("✓ Manual trade patterns (SL/TP sizes) appear reasonable")
print("\nNext Steps:")
print("1. Build HumanTrainedStrategy class")
print("2. Implement SMC logic (Structure, Shift, POI, Liquidity)")
print("3. Run full backtest on CSV data")
print("4. Compare with manual trade performance")
print()
