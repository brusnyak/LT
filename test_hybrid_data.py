import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.data_loader import load_candle_data, get_csv_path

def test_hybrid_loading():
    pair = "EURUSD"
    timeframe = "M15"
    
    print(f"Testing hybrid loading for {pair} {timeframe}...")
    
    # 1. Ensure we have some CSV data (mocking it if needed, or relying on existing)
    # Let's check if file exists
    csv_path = get_csv_path(pair, timeframe)
    if os.path.exists(csv_path):
        print(f"Found existing CSV at {csv_path}")
    else:
        print(f"No existing CSV at {csv_path}. Will try to fetch fresh.")

    try:
        # 2. Call load_candle_data with source='ctrader'
        # This should trigger the hybrid logic
        df = load_candle_data(pair, timeframe, limit=100, source='ctrader')
        
        print(f"Successfully loaded {len(df)} candles.")
        print("Last 5 candles:")
        print(df.tail())
        
        # Check timezone
        print(f"Timezone: {df.index.tz}")
        
    except Exception as e:
        print(f"Error during loading: {e}")

if __name__ == "__main__":
    test_hybrid_loading()
