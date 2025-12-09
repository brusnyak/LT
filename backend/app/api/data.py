"""Chart data API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional

from app.core.data_loader import load_candle_data, set_data_source, get_data_source
from app.core.data_cache import get_cached_data, preload_symbol, clear_cache, get_cache_info
from app.core.constants import Pair, Timeframe
from app.models.candle import Candle, ChartDataResponse

router = APIRouter()


@router.get("/candles", response_model=ChartDataResponse)
async def get_candles(
    pair: str = Query(..., description="Currency pair (e.g., EURUSD)"),
    timeframe: str = Query(..., description="Timeframe (e.g., M5, H1, H4)"),
    start: Optional[str] = Query(None, description="Start date (ISO format)"),
    end: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: Optional[int] = Query(1000, description="Max number of candles to return"),
    source: Optional[str] = Query(None, description="Data source: 'csv' or 'ctrader'"),
    live: bool = Query(False, description="If true, fetch live data stream (only for cTrader source)"),
    use_cache: bool = Query(True, description="If true, use cached data for faster loading")
):
    """Get OHLCV candle data for a specific pair and timeframe"""
    try:
        pair_upper = pair.upper()
        # Normalize timeframe (e.g., "15m" -> "M15")
        try:
            # Try to map input string to Timeframe enum
            # This handles "M15" directly, but for "15m" we need manual check or smarter lookup
            if timeframe.upper() in Timeframe.__members__:
                timeframe_enum = Timeframe[timeframe.upper()]
                timeframe_str = timeframe_enum.value
            else:
                 # Attempt simple mapping if not direct match
                 # e.g. "15m" -> "M15", "1h" -> "H1"
                 tf_clean = timeframe.upper().replace(" ", "")
                 # Reverse lookup map if needed or just simple heuristics
                 # Simpler: just iterate enum values
                 found = False
                 for tf_val in Timeframe:
                     if tf_val.value == tf_clean or tf_val.value.replace("M","") + "M" == tf_clean: # Handle M15 vs 15M
                          timeframe_str = tf_val.value
                          found = True
                          break
                 
                 # Handle "15m" -> "M15" specifically if enum iteration didn't catch it
                 if not found:
                     if tf_clean.endswith("M") and tf_clean[:-1].isdigit(): # 15M -> M15
                         timeframe_str = f"M{tf_clean[:-1]}"
                     elif tf_clean.endswith("H") and tf_clean[:-1].isdigit(): # 4H -> H4
                         timeframe_str = f"H{tf_clean[:-1]}"
                     else:
                         timeframe_str = timeframe # Fallback
            
        except Exception:
            timeframe_str = timeframe

        if pair_upper in Pair.__members__:
            pair_str = Pair[pair_upper].value
        else:
            pair_str = pair_upper
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {e}")
    
    # Load data
    try:
        # Use cache for CSV data (not for live cTrader data)
        # Use cache for CSV data (not for live cTrader data)
        if use_cache and (source == 'csv' or source is None) and not live:
            df = get_cached_data(pair_str, timeframe_str, limit=limit if limit else 0)
            if df is None:
                # Fallback: Load from disk if not in cache (and populate cache implicitly if data loader does it, or strict load)
                # Note: load_candle_data does not auto-cache in memory usually, but it returns the data.
                load_limit = 0 if (start or end) else limit
                df = load_candle_data(pair_str, timeframe_str, limit=load_limit, source=source, live=False)
        else:
            # Original loading logic for live data or when cache is disabled
            if live:
                df = load_candle_data(pair_str, timeframe_str, limit=limit, source=source, live=True)
            else:
                load_limit = 0 if (start or end) else limit
                df = load_candle_data(pair_str, timeframe_str, limit=load_limit, source=source, live=False)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")
    
    # Filter by date if provided (only for historical data)
    if not live:
        if start:
            start_dt = datetime.fromisoformat(start)
            df = df[df.index >= start_dt]
        if end:
            end_dt = datetime.fromisoformat(end)
            df = df[df.index <= end_dt]
            
        # Apply limit after filtering if it was ignored during load
        if (start or end) and limit:
            df = df.tail(limit)
    
    # Convert to Candle models (or just return raw data for live ticks for now)
    current_data_source = get_data_source() # Get the current global data source setting
    if live and current_data_source == "ctrader": # Only use bid/ask if it's actual live cTrader data
        # For live data, return raw ticks for now.
        # A proper implementation would aggregate ticks into candles on the frontend or backend.
        return ChartDataResponse(
            pair=pair,
            timeframe=timeframe,
            candles=[
                Candle(
                    timestamp=row.name,
                    open=row['bid'], # Using bid as a proxy for price for live ticks
                    high=row['bid'],
                    low=row['bid'],
                    close=row['bid'],
                    volume=0 # No volume for tick data
                )
                for _, row in df.iterrows()
            ],
            total_candles=len(df)
        )
    else: # For historical data (CSV or cTrader) or live data that fell back to CSV
        candles = [
            Candle(
                timestamp=row.name,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            for _, row in df.iterrows()
        ]
        
        return ChartDataResponse(
            pair=pair,
            timeframe=timeframe,
            candles=candles,
            total_candles=len(candles)
        )


@router.post("/source")
async def set_data_source_endpoint(source: str = Query(..., description="Data source: 'csv' or 'ctrader'")):
    """Set the global data source"""
    if source not in ["csv", "ctrader"]:
        raise HTTPException(status_code=400, detail="Invalid source. Must be 'csv' or 'ctrader'")
    
    set_data_source(source)
    return {"message": f"Data source set to {source}", "source": source}


@router.get("/source")
async def get_data_source_endpoint():
    """Get the current data source"""
    return {"source": get_data_source()}


@router.get("/pairs")
async def get_pairs():
    """Get list of available currency pairs from data directory"""
    import os
    from app.core.data_loader import DATA_DIR
    
    pairs = set()
    # Also include Enum pairs as defaults
    for p in Pair:
        pairs.add(p.value)
        
    try:
        # Scan data directory
        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                if file.endswith(".csv"):
                    # Filename format: PAIR + TIMEFRAME + .csv (e.g. EURUSD5.csv or EURUSDM5.csv)
                    # We need to extract the pair part.
                    # Heuristics:
                    # 1. Remove .csv
                    name = file.replace(".csv", "")
                    
                    # 2. Strip numeric suffix (m5, 5, etc)
                    # Find where the trailing digits start
                    head = name.rstrip('0123456789')
                    
                    # 3. Strip trailing 'm' or 'h' or 'd' if present before digits (like M5, H1)
                    # This is tricky because some pairs might end in those letters. 
                    # But standard suffixes are simple.
                    # Common tf suffixes: 1, 5, 15, 60, 240, 1440.
                    # Or M1, M5...
                    
                    # Better approach: Iterate known pairs? No, we want *new* pairs.
                    # Let's try to remove common timeframe strings from the end.
                    
                    bg = name.upper()
                    # Try to strip standard timeframes from the end
                    # Sort timeframes by length desc to match M15 before M1 (or 15 before 5 if ambiguous)
                    # NOTE: We only include numeric suffixes because files use minute-based naming (e.g. 1440 for D1).
                    # Including 'D1', 'H1' causes bugs with pairs ending in D or H (e.g. EURUSD1 -> D1 -> EURUS).
                    known_tfs = ["1440", "240", "60", "30", "15", "5", "1"]
                    
                    parsed_pair = bg
                    for tf in sorted(known_tfs, key=len, reverse=True):
                         if bg.endswith(tf):
                             parsed_pair = bg[:-len(tf)]
                             break
                    
                    if parsed_pair:
                        pairs.add(parsed_pair)
                        
    except Exception as e:
        print(f"Error scanning for pairs: {e}")
        
    return {"pairs": sorted(list(pairs))}


@router.post("/cache/preload")
async def preload_cache(pair: str = Query(..., description="Currency pair to preload")):
    """Preload all timeframes for a specific pair into cache"""
    try:
        results = preload_symbol(pair)
        return {
            "message": f"Preloaded {pair} into cache",
            "pair": pair.upper(),
            "timeframes_loaded": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preload: {str(e)}")


@router.delete("/cache/clear")
async def clear_data_cache(pair: Optional[str] = Query(None, description="Specific pair to clear, or all if not provided")):
    """Clear cache for specific pair or all pairs"""
    clear_cache(pair)
    return {
        "message": f"Cache cleared for {pair if pair else 'all pairs'}",
        "pair": pair.upper() if pair else "all"
    }


@router.get("/cache/info")
async def get_cache_status():
    """Get information about cached data"""
    info = get_cache_info()
    return {
        "cached_pairs": list(info.keys()),
        "details": info
    }


@router.get("/timeframes")
async def get_timeframes():
    """Get list of available timeframes"""
    return {"timeframes": [t.value for t in Timeframe]}
