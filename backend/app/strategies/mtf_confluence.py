"""
Multi-timeframe confluence helper for V8 strategy
Checks trend alignment across 4H, 30M, and 5M timeframes
"""
import pandas as pd

def calculate_ema(df: pd.DataFrame, period: int = 200) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return df['close'].ewm(span=period, adjust=False).mean()

def check_mtf_confluence(df_4h: pd.DataFrame, df_30m: pd.DataFrame, df_5m: pd.DataFrame,
                         signal_time, signal_type: str) -> bool:
    """
    Check if all timeframes align for the trade direction.
    
    Args:
        df_4h: 4H timeframe data
        df_30m: 30M timeframe data
        df_5m: 5M timeframe data
        signal_time: Time of the signal
        signal_type: 'LONG' or 'SHORT'
        
    Returns:
        bool: True if all timeframes align
    """
    # Ensure dataframes have 'time' column and set as index
    for df in [df_4h, df_30m, df_5m]:
        if 'time' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
    
    # Get the most recent candles before signal time
    df_4h_recent = df_4h[df_4h.index <= signal_time].tail(1)
    df_30m_recent = df_30m[df_30m.index <= signal_time].tail(1)
    df_5m_recent = df_5m[df_5m.index <= signal_time].tail(1)
    
    if df_4h_recent.empty or df_30m_recent.empty or df_5m_recent.empty:
        return False
    
    # Calculate EMAs for each timeframe
    ema_4h = calculate_ema(df_4h[df_4h.index <= signal_time].tail(250), period=50)
    ema_30m = calculate_ema(df_30m[df_30m.index <= signal_time].tail(250), period=100)
    ema_5m = calculate_ema(df_5m[df_5m.index <= signal_time].tail(250), period=200)
    
    if ema_4h.empty or ema_30m.empty or ema_5m.empty:
        return False
    
    # Get current prices
    price_4h = df_4h_recent.iloc[0]['close']
    price_30m = df_30m_recent.iloc[0]['close']
    price_5m = df_5m_recent.iloc[0]['close']
    
    # Get EMA values
    ema_4h_val = ema_4h.iloc[-1]
    ema_30m_val = ema_30m.iloc[-1]
    ema_5m_val = ema_5m.iloc[-1]
    
    # Check alignment
    if signal_type == 'LONG':
        # All prices should be above their respective EMAs
        return (price_4h > ema_4h_val and 
                price_30m > ema_30m_val and 
                price_5m > ema_5m_val)
    else:  # SHORT
        # All prices should be below their respective EMAs
        return (price_4h < ema_4h_val and 
                price_30m < ema_30m_val and 
                price_5m < ema_5m_val)
