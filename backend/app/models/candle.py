"""Candle data models"""
from datetime import datetime
from pydantic import BaseModel, Field


class Candle(BaseModel):
    """Single OHLCV candle"""
    timestamp: datetime
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: float = Field(..., description="Volume")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-07-21T21:25:00Z",
                "open": 1.08837,
                "high": 1.0884,
                "low": 1.08827,
                "close": 1.0883,
                "volume": 28
            }
        }


class ChartDataRequest(BaseModel):
    """Request for chart data"""
    pair: str
    timeframe: str
    start: datetime | None = None
    end: datetime | None = None


class ChartDataResponse(BaseModel):
    """Response with chart data"""
    pair: str
    timeframe: str
    candles: list[Candle]
    total_candles: int
