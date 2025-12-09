import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.data_loader import get_csv_path, load_candle_data

def test_data_loading():
    print("Testing Data Loading...")
    
    pair = "EURUSD"
    timeframe = "15M" # User reported 404 for this
    
    # 1. Check Path
    path = get_csv_path(pair, timeframe)
    print(f"Resolved Path for {pair} {timeframe}: {path}")
    print(f"Exists? {os.path.exists(path)}")
    
    if not os.path.exists(path):
        print("Detailed walk check:")
        data_dir = "/Users/yegor/Documents/Agency & Security Stuff/Development/SMC/archive/charts"
        for root, dirs, files in os.walk(data_dir):
            print(f"Scanning {root}...")
            for f in files:
                if "EURUSD" in f and "15" in f:
                    print(f"  Found similar: {f}")
    
    # 2. Try Loading
    try:
        df = load_candle_data(pair, timeframe, limit=100)
        print(f"Load Success! Shape: {df.shape}")
        print(df.head())
    except Exception as e:
        print(f"Load Failed: {e}")

if __name__ == "__main__":
    test_data_loading()
