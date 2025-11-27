"""
Backtrader Data Feed for CSV files
Loads OHLCV data from our forex CSV files
"""
import backtrader as bt
import pandas as pd
from datetime import datetime


class CSVDataFeed(bt.feeds.PandasData):
    """
    Custom data feed for our CSV format
    CSV format: timestamp,open,high,low,close,volume
    """
    params = (
        ('datetime', None),  # Index column (timestamp)
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
    )


def load_csv_data(filepath, start_date=None, end_date=None):
    """
    Load CSV data and convert to Backtrader-compatible format
    
    Args:
        filepath: Path to CSV file
        start_date: Optional start date (datetime or string)
        end_date: Optional end date (datetime or string)
    
    Returns:
        pandas DataFrame ready for Backtrader
    """
    # Read CSV (no header in our files)
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Parse timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Filter by date range if provided
    if start_date:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        df = df[df.index >= start_date]
    
    if end_date:
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        df = df[df.index <= end_date]
    
    # Ensure required columns exist
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Sort by timestamp
    df.sort_index(inplace=True)
    
    return df
