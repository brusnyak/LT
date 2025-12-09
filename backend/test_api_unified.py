#!/usr/bin/env python3
"""
SIMPLEST Unified Strategy Test - Using Backend API
"""
import requests
import pandas as pd
from datetime import datetime

def test_strategy():
    print("=" * 60)
    print("Unified Strategy Test - Via API")
    print("=" * 60)
    
    # Use the existing backend to get data
    base_url = "http://localhost:9000"
    
    print("\n1. Fetching M5 data via API...")
    response = requests.get(f"{base_url}/api/data/candles", params={
        "symbol": "EURUSD",
        "timeframe": "M5",
        "start": "2024-01-01",
        "end": "2024-01-05",
        "limit": 10000
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch data: {response.status_code}")
        print(response.text)
        return False
    
    candles = response.json()
    print(f"   Got {len(candles)} candles")
    
    # Convert to DataFrame
    df = pd.DataFrame(candles)
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    
    # Get current state
    current = df.iloc[-1]
    print(f"\n2. Current state (last candle):")
    print(f"   Time: {current.name}")
    print(f"   Price: {current['close']:.5f}")
    print(f"   High: {current['high']:.5f}, Low: {current['low']:.5f}")
    
    # Now use the Unified Strategy via API
    print(f"\n3. Running Unified Strategy analysis...")
    response = requests.post(f"{base_url}/api/analysis/unified", json={
        "symbol": "EURUSD",
       "timeframe_h4": "H4",
        "timeframe_m5": "M5",
        "start": "2024-01-01",
        "end": "2024-01-05"
    })
    
    if response.status_code != 200:
        print(f"❌ Analysis failed: {response.status_code}")
        print(response.text[:500])
        return False
    
    result = response.json()
    
    signals = result.get('signals', [])
    metadata = result.get('metadata', {})
    
    print(f"\n4. Results:")
    print(f"   Signals: {len(signals)}")
    
    if signals:
        print("\n   Top 3 Signals:")
        for i, sig in enumerate(signals[:3]):
            print(f"   [{i+1}] {sig.get('time')} - {sig.get('type')}")
            print(f"       Entry: {sig.get('price'):.5f}")
            print(f"       SL: {sig.get('sl'):.5f} | TP: {sig.get('tp'):.5f}")
            print(f"       Reason: {sig.get('reason')}")
    else:
        print("   ℹ️  No signals generated")
    
    print("\n   Metadata:")
    for key, value in metadata.items():
        if isinstance(value, list):
            print(f"   {key}: {len(value)} items")
        elif isinstance(value, dict):
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    import sys
    try:
        success = test_strategy()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to backend API (http://localhost:9000)")
        print("   Make sure the backend is running: cd backend && make back")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
