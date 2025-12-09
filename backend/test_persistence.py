import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from app.core.data_loader import load_candle_data, get_csv_path

def test_persistence():
    print("Testing Data Persistence...")
    
    pair = 'EURUSD'
    timeframe = 'H1'
    
    # Ensure directory exists (it should be created by load_candle_data, but just in case)
    # Actually load_candle_data creates it.
    
    try:
        print(f"Fetching data for {pair} {timeframe} from cTrader...")
        df = load_candle_data(pair, timeframe, limit=10, source='ctrader')
        
        if df.empty:
            print("✗ No data returned")
            return
            
        print(f"✓ Data fetched: {len(df)} bars")
        
        # Check if CSV exists
        csv_path = get_csv_path(pair, timeframe)
        if os.path.exists(csv_path):
            print(f"✓ CSV file created at {csv_path}")
            
            # Verify content
            import pandas as pd
            df_csv = pd.read_csv(csv_path)
            print(f"✓ CSV contains {len(df_csv)} rows")
            
            # Test loading back via data_loader (New Format)
            print(f"\nTesting loading back from CSV (New Format)...")
            df_loaded = load_candle_data(pair, timeframe, limit=10, source='csv')
            print(f"✓ Loaded {len(df_loaded)} bars from CSV")
            print(f"✓ Columns: {list(df_loaded.columns)}")
            
            # Test loading legacy format (M5)
            print(f"\nTesting loading legacy format (M5)...")
            try:
                df_legacy = load_candle_data(pair, 'M5', limit=10, source='csv')
                print(f"✓ Loaded {len(df_legacy)} bars from legacy CSV")
            except Exception as e:
                print(f"✗ Failed to load legacy CSV: {e}")

        else:
            print(f"✗ CSV file NOT found at {csv_path}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_persistence()
