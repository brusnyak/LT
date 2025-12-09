import pandas as pd
import os
from datetime import datetime
from typing import Literal
from app.config import settings
import time
import pytz # Import pytz for timezone conversion

# Base path for data - pointing to the parent directory of categories
DATA_DIR = "/Users/yegor/Documents/Agency & Security Stuff/Development/SMC/archive/charts"

# Global data source setting (can be toggled via API)
_DATA_SOURCE: Literal["csv", "ctrader"] = "csv"

def set_data_source(source: Literal["csv", "ctrader"]):
    """Set the global data source"""
    global _DATA_SOURCE
    _DATA_SOURCE = source

def get_data_source() -> str:
    """Get the current data source"""
    return _DATA_SOURCE

def get_csv_path(pair: str, timeframe: str) -> str:
    """Constructs the absolute path to the CSV file, searching subdirectories."""
    # Map timeframe to minutes for new format (e.g., EURUSD5.csv for M5)
    tf_map = {
        "M1": "1", "1m": "1", "1M": "1",
        "M5": "5", "5m": "5", "5M": "5",
        "M15": "15", "15m": "15", "15M": "15",
        "M30": "30", "30m": "30", "30M": "30",
        "H1": "60", "1h": "60", "1H": "60",
        "H4": "240", "4h": "240", "4H": "240",
        "D1": "1440", "1d": "1440", "1D": "1440", "d": "1440"
    }
    
    tf_suffix = tf_map.get(timeframe.upper(), timeframe)
    # New format: EURUSD5.csv (no underscore)
    filename = f"{pair.upper()}{tf_suffix}.csv"
    
    # Check in all subdirectories
    for root, dirs, files in os.walk(DATA_DIR):
        if filename in files:
            return os.path.join(root, filename)
            
    # If not found, return default path in forex (will fail later but consistent)
    return os.path.join(DATA_DIR, "forex", filename)

def load_candle_data(pair: str, timeframe: str, limit: int = 1000, source: str = None, live: bool = False) -> pd.DataFrame:
    """
    Loads candle data from CSV or cTrader (with smart caching).
    
    Args:
        pair: Currency pair (e.g., "EURUSD")
        timeframe: Timeframe (e.g., "M5", "H4")
        limit: Max number of candles to return
        source: Data source ("csv" or "ctrader"). If None, uses global setting.
        live: If True, attempts to fetch live data stream (only for ctrader).
        
    Returns:
        DataFrame with columns: [time, open, high, low, close, volume] for historical,
        or a DataFrame of ticks for live data.
    """
    # Determine source
    data_source = source if source else _DATA_SOURCE
    
    # HISTORY MODE: Use ONLY CSV (no cTrader calls)
    if data_source == "csv":
        return _load_from_csv(pair, timeframe, limit)
    
    # LIVE MODE: Use hybrid CSV + cTrader
    elif data_source == "ctrader":
        if live:
            return _load_from_ctrader_live(pair, timeframe)
        else:
            return _load_from_ctrader(pair, timeframe, limit)
    
    # Fallback to CSV
    else:
        return _load_from_csv(pair, timeframe, limit)

def _load_from_csv(pair: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Load data from CSV file"""
    path = get_csv_path(pair, timeframe)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")

    # Read first line to check for header and separator
    with open(path, 'r') as f:
        first_line = f.readline()
        
    has_header = 'open' in first_line.lower() or 'close' in first_line.lower()
    is_comma = ',' in first_line
    
    try:
        if is_comma:
            # Standard CSV (comma separated)
            if has_header:
                df = pd.read_csv(path)
                df.columns = [c.lower().strip() for c in df.columns]
            else:
                # Assume standard order if no header but comma separated
                df = pd.read_csv(path, header=None)
                df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        else:
            # Legacy format (whitespace separated)
            if has_header:
                df = pd.read_csv(path, comment='#', sep=r'\s+')
                df.columns = [c.lower().strip() for c in df.columns]
            else:
                # Space-delimited format with date+time in first two columns
                df = pd.read_csv(path, header=None, comment='#', sep=r'\s+')
                
                # Check if first two columns are date and time (need to combine)
                if len(df.columns) >= 6:
                    # Assume format: date time open high low close volume
                    df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'volume']
                    df['time'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                    df = df.drop(columns=['date'])
                else:
                    # Fallback to standard format
                    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
            
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV: {e}")

    # Handle different CSV formats
    if 'timestamp' in df.columns and 'time' not in df.columns:
        df['time'] = pd.to_datetime(df['timestamp'])
        df = df.drop(columns=['timestamp'])
    elif 'time' in df.columns:
        # Time column might already be datetime or string
        if df['time'].dtype == 'object':
            df['time'] = pd.to_datetime(df['time'])
    
    # Ensure required columns exist
    required = ['time', 'open', 'high', 'low', 'close']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
            
    # Sort by time and set as index
    df = df.sort_values('time').set_index('time')
    
    # Ensure timezone-aware index (UTC)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    
    # Convert to Europe/Bratislava timezone
    bratislava_tz = pytz.timezone('Europe/Bratislava')
    df.index = df.index.tz_convert(bratislava_tz)
    
    # Limit
    if limit is not None and limit > 0: # Only apply limit if it's a positive number
        df = df.tail(limit)

    return df

def _load_from_ctrader(pair: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Load data from cTrader with smart caching (Hybrid CSV + Live)"""
    try:
        from app.core.ctrader_client import CTraderClient
        
        # 1. Try to load existing CSV data first (full history)
        csv_df = pd.DataFrame()
        try:
            # We use a large limit to get all data, or 0 if supported (but _load_from_csv uses tail(limit))
            # Let's use a very large number to ensure we get everything
            csv_df = _load_from_csv(pair, timeframe, limit=1000000)
            
            # Convert back to UTC for merging/saving (since _load_from_csv returns Bratislava)
            if not csv_df.empty:
                csv_df.index = csv_df.index.tz_convert('UTC')
                
        except FileNotFoundError:
            # No local data yet, that's fine
            pass
        except Exception as e:
            print(f"Warning: Failed to load existing CSV for hybrid mode: {e}")

        # 2. Determine start time for cTrader fetch
        start_date = None
        if not csv_df.empty:
            last_time = csv_df.index[-1]
            # Start from the next minute/interval to avoid duplicates (or just overlap and dedup)
            start_date = last_time
            print(f"Found local data for {pair} {timeframe} ending at {last_time}. Fetching new data...")
        
        # 3. Connect and Fetch from cTrader
        ctrader = CTraderClient()
        
        if not ctrader.connected:
            success = ctrader.connect()
            if not success:
                raise RuntimeError("Failed to connect to cTrader.")
        
        # Fetch data
        if start_date:
            # Fetch from last known time to now
            new_data = ctrader.get_historical_data(pair, timeframe, start_date=start_date, bars=limit)
        else:
            # No local data, fetch latest N bars
            new_data = ctrader.get_historical_data(pair, timeframe, bars=limit)
        
        # 4. Merge Data
        if new_data.empty:
            if csv_df.empty:
                raise RuntimeError("No data returned from cTrader and no local CSV found.")
            print("No new data from cTrader. Using local CSV.")
            final_df = csv_df
        else:
            # Ensure new_data is UTC (it should be from ctrader_client)
            if new_data.index.tz is None:
                new_data.index = new_data.index.tz_localize('UTC')
            else:
                new_data.index = new_data.index.tz_convert('UTC')
                
            if not csv_df.empty:
                # Combine and remove duplicates
                combined = pd.concat([csv_df, new_data])
                final_df = combined[~combined.index.duplicated(keep='last')]
                print(f"Merged {len(csv_df)} local rows with {len(new_data)} new rows.")
            else:
                final_df = new_data

        # 5. Save to CSV (in UTC, as expected by _load_from_csv)
        try:
            csv_path = get_csv_path(pair, timeframe)
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # Save to CSV
            # We save the index (time) and columns. 
            # Note: to_csv with datetime index writes ISO format usually.
            # _load_from_csv expects standard CSV or space-delimited.
            # Let's save as standard CSV.
            final_df.to_csv(csv_path)
            print(f"Saved merged data to {csv_path}")
            
        except Exception as e:
            print(f"Warning: Failed to save cTrader data to CSV: {e}")

        # 6. Prepare Return Data (Convert to Bratislava)
        bratislava_tz = pytz.timezone('Europe/Bratislava')
        final_df.index = final_df.index.tz_convert(bratislava_tz)
        
        # Apply limit
        if limit is not None and limit > 0:
            final_df = final_df.tail(limit)
            
        return final_df
        
    except Exception as e:
        print(f"cTrader error: {e}. Falling back to CSV.")
        # Fallback to CSV (re-load to ensure correct timezone/limit processing)
        return _load_from_csv(pair, timeframe, limit)

def _load_from_ctrader_live(pair: str, timeframe: str) -> pd.DataFrame:
    """
    Loads live candle data from cTrader by aggregating ticks.
    """
    try:
        from app.core.ctrader_client import CTraderClient
        
        ctrader = CTraderClient()
        
        if not ctrader.connected:
            success = ctrader.connect()
            if not success:
                raise RuntimeError("Failed to connect to cTrader for live data.")
        
        # Subscribe if not already subscribed, specify timeframes for aggregation
        if pair not in ctrader.live_data_streams:
            # We need to know which timeframes are relevant for live aggregation.
            # For now, let's assume M1, M5, M15, H1, H4 are generally useful.
            # In a real application, this might be dynamically configured.
            ctrader.subscribe_to_live_data(pair, timeframes=['M1', 'M5', 'M15', 'H1', 'H4'])
            # Give some time for initial ticks to arrive and candles to form
            time.sleep(2) 
        
        # Get the current forming candle for the requested timeframe
        live_candle = ctrader.get_live_candles(pair, timeframe)
        
        if live_candle is None:
            return pd.DataFrame()
        
        # Convert the single candle dict to a DataFrame
        df = pd.DataFrame([live_candle])
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)
        
        # The candle builder already handles timezone conversion to Bratislava
        return df
        
    except Exception as e:
        print(f"cTrader live data error: {e}.")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def df_to_json_records(df: pd.DataFrame) -> list:
    """Converts DataFrame to list of dicts with unix timestamp for 'time'."""
    output = df.copy()
    # Ensure 'time' is in UTC before converting to unix timestamp
    if output.index.tz is not None:
        output.index = output.index.tz_convert('UTC')
    output['time'] = output.index.astype('int64') // 10**9
    output = output.reset_index(drop=True) # Drop the original time index
    return output.to_dict(orient='records')
