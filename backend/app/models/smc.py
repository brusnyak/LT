"""SMC entity models"""
from __future__ import annotations # Enable postponed evaluation of type annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal


class SwingPoint(BaseModel):
    """A swing high or swing low point"""
    index: int = Field(..., description="Index in the dataframe")
    timestamp: datetime = Field(..., description="Timestamp of the swing")
    price: float = Field(..., description="Price at the swing point")
    type: Literal['swing_high', 'swing_low'] = Field(..., description="Type of swing point")


class SwingAnalysis(BaseModel):
    """Swing analysis response"""
    pair: str
    timeframe: str
    swing_highs: List[SwingPoint]
    swing_lows: List[SwingPoint]
    total_swings: int
    lookback_left: int
    lookback_right: int


class OrderBlock(BaseModel):
    """Order block zone"""
    type: Literal['bullish', 'bearish']
    candle_index: int
    high: float
    low: float
    mid: float
    timestamp: datetime
    state: Literal['active', 'touched', 'partial', 'mitigated', 'breaker']
    liquidity_swept: float | None = None
    lookback_candles: int | None = None
    is_breaker: bool = False # Added for breaker blocks
    original_type: Literal['bullish', 'bearish'] | None = None # Original type if it became a breaker
    breaker_time: datetime | None = None # Timestamp when it became a breaker
    # Added for consistency with mitigation logic in order_blocks.py
    filled: bool = False
    mitigation_level: int = 0 # 0=untouched, 1=25%, 2=50%, 3=75%, 4=100%


class FairValueGap(BaseModel):
    """Fair value gap (imbalance zone)"""
    type: Literal['bullish', 'bearish']
    start_index: int
    end_index: int
    top: float
    bottom: float
    timestamp: datetime
    filled: bool = False
    mitigation_level: int = 0 # 0=untouched, 1=25%, 2=50%, 3=75%, 4=100%


class Session(BaseModel):
    """Trading session details"""
    name: str
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    open: float
    close: float
    active: bool


class PremiumDiscountZone(BaseModel):
    """Premium/Discount/OTE zones"""
    type: Literal['premium', 'discount', 'equilibrium', 'ote']
    start_time: datetime
    end_time: datetime
    top: float
    bottom: float
    color: str # Hex color code


class LiquidityZone(BaseModel):
    """Liquidity zone at swing points"""
    type: Literal['buy_side', 'sell_side']
    price: float
    timestamp: datetime
    index: int
    swept: bool = False
    sweep_time: datetime | None = None
    subtype: str | None = None # Added subtype


class OrderBlockResponse(BaseModel):
    """Single order block"""
    type: Literal['bullish', 'bearish']
    candle_index: int
    timestamp: datetime
    high: float
    low: float
    mid: float
    state: Literal['active', 'touched', 'partial', 'mitigated', 'breaker']
    liquidity_swept: float | None = None
    lookback_candles: int | None = None


class OrderBlockAnalysis(BaseModel):
    """Order block analysis response"""
    pair: str
    timeframe: str
    order_blocks: List[OrderBlockResponse]
    total_obs: int
    bullish_obs: int
    bearish_obs: int
    lookback_window: int


class MarketStructureEvent(BaseModel):
    """Single market structure event (BOS or CHOCH)"""
    type: Literal['BOS', 'CHOCH']
    direction: Literal['bullish', 'bearish']
    index: int
    price: float
    timestamp: datetime
    description: str
    pivot_index: int
    pivot_timestamp: datetime


class MarketStructureAnalysis(BaseModel):
    """Market structure analysis response"""
    pair: str
    timeframe: str
    structure_events: List[MarketStructureEvent]
    total_events: int
    bos_count: int
    choch_count: int


class FVGResponse(BaseModel):
    """Single Fair Value Gap"""
    type: Literal['bullish', 'bearish']
    start_index: int
    end_index: int
    top: float
    bottom: float
    timestamp: datetime
    filled: bool


class FVGAnalysis(BaseModel):
    """FVG analysis response"""
    pair: str
    timeframe: str
    fvgs: List[FVGResponse]
    total_fvgs: int
    bullish_fvgs: int
    bearish_fvgs: int


class LiquidityZoneResponse(BaseModel):
    """Single liquidity zone"""
    type: Literal['buy_side', 'sell_side']
    price: float
    timestamp: datetime
    index: int
    swept: bool
    sweep_time: datetime | None = None
    subtype: str | None = None


class LiquidityAnalysis(BaseModel):
    """Liquidity analysis response"""
    pair: str
    timeframe: str
    liquidity_zones: List[LiquidityZoneResponse]
    total_zones: int
    bsl_count: int
    ssl_count: int
