"""Strategy models"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal

class RangeLevel(BaseModel):
    """4H Range Definition"""
    date: str = Field(..., description="Date of the range (YYYY-MM-DD)")
    high: float
    low: float
    start_time: datetime
    end_time: datetime
    
class Signal(BaseModel):
    """Trading Signal"""
    time: datetime
    type: Literal['LONG', 'SHORT']
    price: float
    sl: float
    tp: float
    reason: str
    status: Literal['PENDING', 'ACTIVE', 'CLOSED'] = 'PENDING'
    close_time: datetime | None = None
    close_price: float | None = None
    outcome: Literal['TP_HIT', 'SL_HIT'] | None = None

class StrategyResponse(BaseModel):
    """Strategy Analysis Response"""
    pair: str
    ranges: List[RangeLevel]
    signals: List[Signal]
