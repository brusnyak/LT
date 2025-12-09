"""
Multi-Timeframe Data Cache
Preloads all timeframes for a symbol to enable instant switching
"""
from typing import Dict, Optional
import pandas as pd
from app.core.data_loader import load_candle_data

# In-memory cache: {pair: {timeframe: DataFrame}}
_CACHE: Dict[str, Dict[str, pd.DataFrame]] = {}

# All timeframes to preload
ALL_TIMEFRAMES = ['M5', 'M15', 'M30', 'H1', 'H4']


def preload_symbol(pair: str, source: str = 'csv') -> Dict[str, int]:
    """
    Preload all timeframes for a symbol into cache
    
    Returns: Dictionary with loaded timeframe counts
    """
    # Ensure uppercase for consistency
    pair_upper = pair.upper()
    # No extra normalization here, assume caller (API) handles complex mapping, 
    # but we ensure basic uppercase match.
    
    if pair_upper not in _CACHE:
        _CACHE[pair_upper] = {}
    
    results = {}
    
    for tf in ALL_TIMEFRAMES:
        try:
            df = load_candle_data(pair_upper, tf, limit=0, source=source)  # limit=0 loads all data
            _CACHE[pair_upper][tf] = df
            results[tf] = len(df)
        except Exception as e:
            print(f"Failed to load {pair_upper} {tf}: {e}")
            results[tf] = 0
    
    return results


def get_cached_data(pair: str, timeframe: str, limit: int = 1000) -> Optional[pd.DataFrame]:
    """
    Get data from cache, preloading if necessary
    
    Returns: DataFrame or None if not available
    """
    pair_upper = pair.upper()
    tf_upper = timeframe.upper()
    
    # Check if pair is cached
    if pair_upper not in _CACHE or tf_upper not in _CACHE[pair_upper]:
        # Preload all timeframes for this pair
        print(f"Cache miss for {pair_upper} {tf_upper}, preloading all timeframes...")
        preload_symbol(pair_upper)
    
    # Get from cache
    if pair_upper in _CACHE and tf_upper in _CACHE[pair_upper]:
        df = _CACHE[pair_upper][tf_upper]
        
        # Return last N candles if limit specified
        if limit > 0:
            return df.tail(limit)
        return df
    
    return None


def clear_cache(pair: Optional[str] = None):
    """
    Clear cache for specific pair or all pairs
    """
    if pair:
        pair_upper = pair.upper()
        if pair_upper in _CACHE:
            del _CACHE[pair_upper]
            print(f"Cleared cache for {pair_upper}")
    else:
        _CACHE.clear()
        print("Cleared all cache")


def get_cache_info() -> Dict:
    """
    Get information about cached data
    """
    info = {}
    for pair, timeframes in _CACHE.items():
        info[pair] = {
            'timeframes': list(timeframes.keys()),
            'counts': {tf: len(df) for tf, df in timeframes.items()}
        }
    return info
