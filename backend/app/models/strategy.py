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
    type: Literal['LONG', 'SHORT']
    entry: float = Field(..., alias='price', description="Entry price")
    sl: float
    tp: float
    tp2: float | None = None
    tp_split: float = 0.5
    rr: float = 0.0
    time: datetime | None = None
    pair: str | None = None
    reason: str = ""
    status: Literal['PENDING', 'ACTIVE', 'CLOSED', 'PARTIAL'] = 'PENDING'
    close_time: datetime | None = None
    close_price: float | None = None
    outcome: Literal['TP_HIT', 'SL_HIT', 'TP1_HIT', 'TP2_HIT'] | None = None
    confidence: float = 0.5
    timeframe: str = 'M15'
    poi_type: str | None = None
    structure: str | None = None
    
    class Config:
        populate_by_name = True  # Allow both 'entry' and 'price'
        
    @property
    def price(self):
        """Alias for entry"""
        return self.entry

class StrategyResponse(BaseModel):
    """Strategy Analysis Response"""
    pair: str
    timeframe: str = "M15"
    strategy: str = "Unknown"
    ranges: List[RangeLevel] = []
    signals: List[Signal] = []
    analysis: dict = {}
