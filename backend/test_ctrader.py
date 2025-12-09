"""
cTrader Connection Test Script
Tests connection, authentication, and data fetching with new credentials
"""
import pandas as pd
import sys
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from app.core.ctrader_client import CTraderClient

def test_connection():
    """Test cTrader connection and authentication"""
    print("\n" + "="*80)
    print("cTrader Connection Test")
    print("="*80)
    
    try:
        # Initialize cTrader client
        print("\n1. Initializing cTrader client...")  
        ctrader = CTraderClient()
        print("   ✓ Client initialized")
        
        # Connect to cTrader
        print("\n2. Connecting to cTrader...")
        if ctrader.connect():
             print("   ✓ Connected and authenticated")
        else:
             print("   ✗ Connection failed")
             return None

        # Test authentication
        print("\n3. Testing authentication...")
        if ctrader.authenticated:
            print("   ✓ Authenticated")
        else:
            print("   ⚠ Not authenticated yet")
            print("   Note: Authentication happens automatically on first data request")
        
        return ctrader
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_historical_data(ctrader, pair='EURUSD', timeframe='H4', bars=100):
    """Test fetching historical data"""
    print(f"\n3. Fetching historical data ({pair} {timeframe}, {bars} bars)...")
    
    try:
        df = ctrader.get_historical_data(pair, timeframe, bars=bars)
        
        if df.empty:
            print("   ✗ No data returned")
            return False
        
        print(f"   ✓ Fetched {len(df)} bars")
        print(f"   ✓ Columns: {list(df.columns)}")
        print(f"   ✓ Date range: {df.index[0]} to {df.index[-1]}")
        print(f"\n   Sample data (last 5 bars):")
        print(df.tail(5).to_string())
        
        # Verify data structure
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"   ⚠ Missing columns: {missing_columns}")
            return False
        
        print("   ✓ Data structure valid")
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache(ctrader, pair='EURUSD', timeframe='H4'):
    """Test cache functionality"""
    print(f"\n4. Testing cache functionality...")
    
    try:
        # First fetch (should hit API)
        print("   Fetching data (first time)...")
        start_time = datetime.now()
        df1 = ctrader.get_historical_data(pair, timeframe, bars=100)
        first_duration = (datetime.now() - start_time).total_seconds()
        print(f"   ✓ First fetch: {first_duration:.2f}s")
        
        # Second fetch (should use cache)
        print("   Fetching data (second time, should use cache)...")
        start_time = datetime.now()
        df2 = ctrader.get_historical_data(pair, timeframe, bars=100)
        second_duration = (datetime.now() - start_time).total_seconds()
        print(f"   ✓ Second fetch: {second_duration:.2f}s")
        
        if second_duration < first_duration:
            print(f"   ✓ Cache working (speedup: {first_duration/second_duration:.1f}x)")
        else:
            print("   ⚠ Cache may not be working (second fetch not faster)")
        
        # Verify data is the same
        if df1.equals(df2):
            print("   ✓ Cached data matches original")
        else:
            print("   ⚠ Cached data differs from original")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_pairs(ctrader):
    """Test fetching data for multiple pairs"""
    print(f"\n5. Testing multiple currency pairs...")
    
    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
    results = {}
    
    for pair in pairs:
        try:
            print(f"   Testing {pair}...")
            df = ctrader.get_historical_data(pair, 'H1', bars=50)
            if not df.empty:
                results[pair] = f"✓ {len(df)} bars"
                print(f"      ✓ {len(df)} bars fetched")
            else:
                results[pair] = "✗ No data"
                print(f"      ✗ No data returned")
        except Exception as e:
            results[pair] = f"✗ Error: {str(e)[:50]}"
            print(f"      ✗ Error: {e}")
    
    print(f"\n   Summary:")
    for pair, result in results.items():
        print(f"      {pair}: {result}")
    
    return results

if __name__ == "__main__":
    print("\n" + "="*80)
    print("cTrader Integration Test Suite")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test connection
    ctrader = test_connection()
    if not ctrader:
        print("\n✗ Connection test failed. Exiting.")
        sys.exit(1)
    
    # Test historical data
    if not test_historical_data(ctrader):
        print("\n⚠ Historical data test failed")
    
    # Test cache
    test_cache(ctrader)
    
    # Test multiple pairs
    test_multiple_pairs(ctrader)
    
    print("\n" + "="*80)
    print("Test Suite Complete")
    print("="*80)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✓ All tests completed")
