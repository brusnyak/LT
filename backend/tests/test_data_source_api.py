import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pandas as pd

from app.main import app
from app.core.data_loader import get_data_source, set_data_source, load_candle_data
from app.core.constants import Pair, Timeframe

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_data_source():
    """Fixture to reset the data source to 'csv' after each test."""
    yield
    set_data_source("csv")

def test_get_data_source_endpoint():
    """Test the GET /api/data/source endpoint."""
    response = client.get("/api/data/source")
    assert response.status_code == 200
    assert "source" in response.json()
    assert response.json()["source"] in ["csv", "ctrader"]

def test_set_data_source_endpoint_valid():
    """Test the POST /api/data/source endpoint with a valid source."""
    response = client.post("/api/data/source?source=ctrader")
    assert response.status_code == 200
    assert response.json()["message"] == "Data source set to ctrader"
    assert response.json()["source"] == "ctrader"
    assert get_data_source() == "ctrader"

    response = client.post("/api/data/source?source=csv")
    assert response.status_code == 200
    assert response.json()["message"] == "Data source set to csv"
    assert response.json()["source"] == "csv"
    assert get_data_source() == "csv"

def test_set_data_source_endpoint_invalid():
    """Test the POST /api/data/source endpoint with an invalid source."""
    response = client.post("/api/data/source?source=invalid")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid source. Must be 'csv' or 'ctrader'"
    assert get_data_source() == "csv" # Should remain unchanged

def test_get_candles_with_source_parameter():
    """
    Test that the /api/data/candles endpoint respects the 'source' query parameter.
    This test will attempt to load from cTrader and then fallback to CSV if cTrader fails.
    """
    pair = Pair.EURUSD.value
    timeframe = Timeframe.M5.value
    limit = 10

    # Test with source=csv
    response_csv = client.get(f"/api/data/candles?pair={pair}&timeframe={timeframe}&limit={limit}&source=csv")
    assert response_csv.status_code == 200
    assert response_csv.json()["pair"] == pair
    assert response_csv.json()["timeframe"] == timeframe
    assert len(response_csv.json()["candles"]) == limit
    
    # Test with source=ctrader (should attempt cTrader, then fallback to CSV if not connected/authenticated)
    # For this test, we assume cTrader might fail if not properly configured,
    # but data_loader has a fallback to CSV.
    response_ctrader = client.get(f"/api/data/candles?pair={pair}&timeframe={timeframe}&limit={limit}&source=ctrader")
    assert response_ctrader.status_code == 200
    assert response_ctrader.json()["pair"] == pair
    assert response_ctrader.json()["timeframe"] == timeframe
    assert len(response_ctrader.json()["candles"]) == limit

    # Verify that the data is consistent between the two sources (if cTrader fallback occurred)
    # This is a basic check, a more robust test would compare actual candle data.
    assert response_csv.json()["candles"][0]["open"] == response_ctrader.json()["candles"][0]["open"]
    assert response_csv.json()["candles"][-1]["close"] == response_ctrader.json()["candles"][-1]["close"]

def test_get_candles_live_data_ctrader():
    """
    Test fetching live data from cTrader.
    This test assumes cTrader is configured and connected for live data.
    """
    pair = Pair.EURUSD.value
    timeframe = Timeframe.M5.value # Timeframe is less relevant for raw ticks
    
    # Set data source to cTrader globally for this test
    set_data_source("ctrader")

    response = client.get(f"/api/data/candles?pair={pair}&timeframe={timeframe}&live=true")
    assert response.status_code == 200
    assert response.json()["pair"] == pair
    assert response.json()["timeframe"] == timeframe
    
    # Expect some live ticks, but not necessarily a fixed number
    assert len(response.json()["candles"]) > 0
    
    # Check structure of live tick data
    first_candle = response.json()["candles"][0]
    assert "timestamp" in first_candle
    assert "open" in first_candle # 'open' is used as proxy for bid in live ticks
    assert "high" in first_candle
    assert "low" in first_candle
    assert "close" in first_candle
    assert "volume" in first_candle
    assert first_candle["volume"] == 0 # Live ticks don't have volume in this implementation

def test_get_candles_live_data_csv_fallback():
    """
    Test fetching live data with CSV source, expecting fallback to historical CSV.
    """
    pair = Pair.EURUSD.value
    timeframe = Timeframe.M5.value
    limit = 10
    
    # Set data source to CSV globally for this test
    set_data_source("csv")

    response = client.get(f"/api/data/candles?pair={pair}&timeframe={timeframe}&limit={limit}&live=true")
    assert response.status_code == 200
    assert response.json()["pair"] == pair
    assert response.json()["timeframe"] == timeframe
    assert len(response.json()["candles"]) == limit # Should return historical CSV data
    
    # Verify it's historical data structure
    first_candle = response.json()["candles"][0]
    assert "timestamp" in first_candle
    assert "open" in first_candle
    assert "high" in first_candle
    assert "low" in first_candle
    assert "close" in first_candle
    assert "volume" in first_candle
    assert first_candle["volume"] > 0 # Historical data should have volume
