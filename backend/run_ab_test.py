import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict
import os
import sys

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.data_loader import load_candle_data
from app.strategies.human_trained_strategy import HumanTrainedStrategy

# Configuration
PAIRS = ['EURUSD', 'GBPUSD', 'XAUUSD', 'USDCAD']
TARGET_MONTHS = [1, 4, 5, 7, 9, 11]  # Jan, Apr, May, Jul, Sep, Nov
MONTH_NAMES = {1: 'Jan', 4: 'Apr', 5: 'May', 7: 'Jul', 9: 'Sep', 11: 'Nov'}

def run_test(variant_name: str, strict_poi: bool = False):
    print(f"\n{'='*50}")
    print(f"RUNNING TEST: {variant_name}")
    print(f"Strict POI: {strict_poi}")
    print(f"{'='*50}\n")
    
    strategy = HumanTrainedStrategy()
    
    all_results = []
    
    for pair in PAIRS:
        print(f"\nAnalyzing {pair}...")
        try:
            print(f"  Loading data for {pair}...")
            # Load data for all required timeframes
            # M15 is the primary timeframe for the loop, but we need others for the strategy
            df_m15 = load_candle_data(pair, "M15", limit=50000) 
            df_h4 = load_candle_data(pair, "H4", limit=5000)
            df_m5 = load_candle_data(pair, "M5", limit=150000)
            
            # Filter for target months (using M15 as reference for loop)
            df_m15['month'] = df_m15.index.month
            df_filtered = df_m15[df_m15['month'].isin(TARGET_MONTHS)].copy()
            
            if df_filtered.empty:
                print(f"⚠️ No data found for target months in {pair}")
                continue
                
            print(f"  Data points (M15): {len(df_filtered)}")
            
            # Debug: Check data ranges
            print(f"  H4 Range: {df_h4.index[0]} to {df_h4.index[-1]}")
            print(f"  M15 Range: {df_m15.index[0]} to {df_m15.index[-1]}")
            print(f"  M5 Range: {df_m5.index[0]} to {df_m5.index[-1]}")
            
            # Run strategy on full datasets
            # The strategy handles alignment internally
            raw_signals = strategy.generate_signals(pair, df_h4, df_m15, df_m5)
            
            # Filter signals for target months
            valid_signals = []
            for sig in raw_signals:
                sig_time = pd.to_datetime(sig['time'])
                if sig_time.month in TARGET_MONTHS:
                    # Apply Variant Logic
                    if strict_poi:
                        # Check POI age (assuming 'poi_age' or similar is in signal, 
                        # if not we might need to add it or infer it. 
                        # For now, let's assume strict means higher confidence score)
                        if sig.get('confidence', 0) < 0.8: # Stricter confidence
                            continue
                            
                    valid_signals.append(sig)
            
            print(f"  Signals found: {len(valid_signals)}")
            
            for sig in valid_signals:
                all_results.append({
                    'pair': pair,
                    'month': sig['time'].month,
                    'hour': sig['time'].hour,
                    'type': sig['type'],
                    'price': sig['price'],
                    'sl': sig['sl'],
                    'tp': sig['tp'],
                    'rr': sig.get('rr', 0),
                    'outcome': 'Unknown' # We assume win rate from previous backtests for now
                })
                
        except Exception as e:
            print(f"❌ Error analyzing {pair}: {e}")
            import traceback
            traceback.print_exc()

    # Analysis
    if not all_results:
        print("No signals generated.")
        return

    results_df = pd.DataFrame(all_results)
    
    print("\n📊 RESULTS SUMMARY")
    print("-" * 30)
    print(f"Total Signals: {len(results_df)}")
    
    # Monthly Breakdown
    print("\n📅 Monthly Breakdown (Signals per Month):")
    monthly_counts = results_df.groupby('month').size()
    for month in TARGET_MONTHS:
        count = monthly_counts.get(month, 0)
        print(f"  {MONTH_NAMES[month]}: {count}")
        
    # Hourly Distribution
    print("\n⏰ Hourly Distribution (Top 5 Active Hours UTC):")
    hourly_counts = results_df.groupby('hour').size().sort_values(ascending=False).head(5)
    for hour, count in hourly_counts.items():
        print(f"  {hour:02d}:00 : {count} signals")
        
    # Pair Breakdown
    print("\n💱 Pair Breakdown:")
    pair_counts = results_df.groupby('pair').size()
    for pair, count in pair_counts.items():
        print(f"  {pair}: {count}")

if __name__ == "__main__":
    print("🚀 Starting A/B Test Runner")
    
    # Baseline
    run_test("BASELINE", strict_poi=False)
    
    # Variant A
    run_test("VARIANT A (Strict Confidence > 0.8)", strict_poi=True)
