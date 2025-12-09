import requests
import uuid
from datetime import datetime

BASE_URL = "http://localhost:9000/api/trainer"

def test_trainer_api():
    # 1. Create Session
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "name": "Test Session",
        "symbol": "EURUSD",
        "start_date": datetime.utcnow().isoformat(),
        "end_date": datetime.utcnow().isoformat()
    }
    
    print(f"Creating session: {session_id}")
    try:
        resp = requests.post(f"{BASE_URL}/sessions", json=session_data)
        if resp.status_code != 200:
            print(f"Failed to create session: {resp.text}")
            return
        print("Session created successfully")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        print("Make sure the backend is running!")
        return

    # 2. Log Trade
    trade_id = str(uuid.uuid4())
    trade_data = {
        "id": trade_id,
        "session_id": session_id,
        "symbol": "EURUSD",
        "entry_time": datetime.utcnow().isoformat(),
        "type": "LONG",
        "entry_price": 1.1000,
        "sl_price": 1.0950,
        "tp_price": 1.1100,
        "market_snapshot": {"trend": "bullish"}
    }
    
    print(f"Logging trade: {trade_id}")
    resp = requests.post(f"{BASE_URL}/sessions/{session_id}/trades", json=trade_data)
    if resp.status_code != 200:
        print(f"Failed to log trade: {resp.text}")
        return
    print("Trade logged successfully")
    
    # 3. Get Session details
    print("Fetching session details...")
    resp = requests.get(f"{BASE_URL}/sessions/{session_id}")
    if resp.status_code != 200:
        print(f"Failed to get session: {resp.text}")
        return
    
    data = resp.json()
    print(f"Session stats: Trades={data['total_trades']}")
    
    if data['total_trades'] == 1:
        print("✅ VERIFICATION SUCCESSFUL")
    else:
        print("❌ VERIFICATION FAILED: Trade count mismatch")

if __name__ == "__main__":
    test_trainer_api()
