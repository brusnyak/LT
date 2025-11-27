import pandas as pd
import os
from datetime import datetime
from app.config import settings

# Base path for data - adjusting to point to the archive/charts/forex directory
# Assuming the app is running from the root or backend directory, we need to locate the archive
# Based on project structure: /Users/yegor/.../SMC/archive/charts/forex
DATA_DIR = "/Users/yegor/Documents/Agency & Security Stuff/Development/SMC/archive/charts/forex"

def get_csv_path(pair: str, timeframe: str) -> str:
    """Constructs the absolute path to the CSV file."""
    # Map timeframe formats if necessary (e.g., "5m" -> "M5", "4h" -> "H4")
    tf_map = {
        "1m": "M1",
        "5m": "M5",
        "15m": "M15",
        "30m": "M30",
        "1h": "H1",
        "4h": "H4",
        "d": "D1",
        "1d": "D1"
    }
    
    tf_suffix = tf_map.get(timeframe.lower(), timeframe.upper())
    filename = f"{pair.upper()}_{tf_suffix}.csv"
    return os.path.join(DATA_DIR, filename)

def load_candle_data(pair: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
    """
    Loads candle data from CSV.
    Returns a DataFrame with columns: [time, open, high, low, close, volume]
    'time' will be a datetime object.
    """
    path = get_csv_path(pair, timeframe)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")

    # Read first line to check for header
    with open(path, 'r') as f:
        first_line = f.readline()
        
    has_header = 'open' in first_line.lower() or 'close' in first_line.lower()
    
    try:
        if has_header:
            df = pd.read_csv(path)
            # Standardize columns
            df.columns = [c.lower().strip() for c in df.columns]
        else:
            # Assume standard format: Time, Open, High, Low, Close, Volume
            # The sample showed: 2024-07-21 21:25,1.08837,1.0884,1.08827,1.0883,28
            df = pd.read_csv(path, header=None, names=['time', 'open', 'high', 'low', 'close', 'volume'])
            
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV: {e}")

    # Handle different CSV formats
    # Format 1: 'date', 'time', 'open', ... (MT4 default)
    if 'date' in df.columns and 'time' in df.columns:
        df['datetime_str'] = df['date'] + ' ' + df['time']
        df['time'] = pd.to_datetime(df['datetime_str'])
        df = df.drop(columns=['date', 'datetime_str'])
    # Format 2: 'time' column is already full datetime (or string representation of it)
    elif 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
    
    # Ensure required columns exist
    required = ['time', 'open', 'high', 'low', 'close']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
            
    # Sort by time just in case
    df = df.sort_values('time').reset_index(drop=True)
    
    # Filter/Limit
    if limit and limit > 0:
        df = df.tail(limit).reset_index(drop=True)

    return df

def df_to_json_records(df: pd.DataFrame) -> list:
    """Converts DataFrame to list of dicts with unix timestamp for 'time'."""
    output = df.copy()
    # Convert datetime to unix timestamp (seconds)
    output['time'] = output['time'].astype('int64') // 10**9
    return output.to_dict(orient='records')
