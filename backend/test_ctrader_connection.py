"""
Test cTrader API connection and account access
"""
from app.core.ctrader_client import get_ctrader_client

def test_ctrader_connection():
    print("="*60)
    print("cTrader API Connection Test")
    print("="*60)
    
    # Initialize client
    print("\n1. Initializing cTrader client...")
    try:
        client = get_ctrader_client()
        print(f"   ✅ Client ID: {client.client_id[:20]}...")
        print(f"   ✅ Account ID: {client.account_id}")
        print(f"   ✅ Has access token: {'Yes' if client.access_token else 'No'}")
    except Exception as e:
        print(f"   ❌ Failed to initialize client: {e}")
        return False
    
    # Test connection
    print("\n2. Testing API connection...")
    try:
        success = client.test_connection()
        if not success:
            return False
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        return False
    
    # Get accounts
    print("\n3. Fetching trading accounts...")
    try:
        accounts = client.get_accounts()
        print(f"   ✅ Found {len(accounts)} accounts:")
        for acc in accounts:
            print(f"      - Account #{acc.get('accountNumber')}: {acc.get('depositCurrency')} ${acc.get('balance'):,.0f}")
            print(f"        Leverage: {acc.get('leverage')}:1, Status: {acc.get('accountStatus')}")
    except Exception as e:
        print(f"   ❌ Failed to get accounts: {e}")
        return False
    
    # Try to fetch historical data
    print("\n4. Testing historical data fetch (EURUSD M5)...")
    try:
        df = client.get_historical_data('EURUSD', 'M5', bars=100)
        print(f"   ✅ Fetched {len(df)} candles")
        print(f"   Columns: {list(df.columns)}")
        if not df.empty:
            print(f"   Date range: {df.index.min()} to {df.index.max()}") # Access index directly
            print(f"\n   Sample data:")
            print(df.head(3).to_string())
        else:
            print("   ⚠️  No historical data fetched.")
    except Exception as e:
        print(f"   ❌ Error fetching historical data: {e}")
        import traceback
        traceback.print_exc()
        return False # Indicate failure if historical data fetch fails
    
    print("\n" + "="*60)
    print("✅ Basic cTrader connection working!")
    print("="*60)
    print("\nNext steps:")
    print("1. Test data quality vs CSV files")
    print("2. Implement caching mechanism")
    print("3. Integrate live data streaming")
    
    return True

if __name__ == "__main__":
    success = test_ctrader_connection()
    sys.exit(0 if success else 1)
