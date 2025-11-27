"""Chart data API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional

from app.core.data_loader import load_candle_data
from app.core.constants import Pair, Timeframe
from app.models.candle import Candle, ChartDataResponse

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/candles", response_model=ChartDataResponse)
async def get_candles(
    pair: str = Query(..., description="Currency pair (e.g., EURUSD)"),
    timeframe: str = Query(..., description="Timeframe (e.g., M5, H1, H4)"),
    start: Optional[str] = Query(None, description="Start date (ISO format)"),
    end: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: Optional[int] = Query(1000, description="Max number of candles to return")
):
    """Get OHLCV candle data for a specific pair and timeframe"""
    try:
        # Validate pair and timeframe
        # We accept case-insensitive strings and convert to Enum if possible, 
        # or just pass the string if it matches the file naming convention.
        # The Enum check helps validation but my loader is flexible.
        # Let's try to use the Enum for validation.
        pair_upper = pair.upper()
        timeframe_upper = timeframe.upper()
        
        # Check if valid enum (optional, but good for safety)
        if pair_upper in Pair.__members__:
            pair_str = Pair[pair_upper].value
        else:
            pair_str = pair_upper # Allow other pairs if files exist
            
        # Timeframe validation
        # My loader handles "5m", "M5" etc.
        timeframe_str = timeframe
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {e}")
    
    # Load data
    try:
        df = load_candle_data(pair_str, timeframe_str, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")
    
    # Filter by date if provided
    if start:
        start_dt = datetime.fromisoformat(start)
        df = df[df['time'] >= start_dt]
    if end:
        end_dt = datetime.fromisoformat(end)
        df = df[df['time'] <= end_dt]
    
    # Convert to Candle models
    candles = [
        Candle(
            timestamp=row['time'],
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


@router.get("/pairs")
async def get_pairs():
    """Get list of available currency pairs"""
    # Return values from Enum
    return {"pairs": [p.value for p in Pair]}


@router.get("/timeframes")
async def get_timeframes():
    """Get list of available timeframes"""
    # Return values from Enum
    return {"timeframes": [t.value for t in Timeframe]}
