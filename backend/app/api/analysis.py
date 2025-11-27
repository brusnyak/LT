"""SMC Analysis API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.core.data_loader import load_candle_data
from app.core.constants import Pair, Timeframe
from app.smc.swings import SwingDetector, get_optimal_lookback
from app.models.smc import (
    SwingAnalysis, OrderBlockAnalysis, MarketStructureAnalysis,
    FVGAnalysis, LiquidityAnalysis
)
from app.models.strategy import StrategyResponse
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals

router = APIRouter(prefix="/analysis", tags=["smc-analysis"])


@router.get("/range-4h", response_model=StrategyResponse)
async def analyze_range_4h(
    pair: str = Query(..., description="Currency pair"),
):
    """
    Analyze 4H Range Strategy (V1)
    """
    # 1. Load 4H Data
    try:
        df_4h = load_candle_data(pair, "H4", limit=1000)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"4H data not found for {pair}")
        
    # 2. Detect Ranges
    ranges = detect_4h_range(df_4h)
    
    # 3. Load 5M Data
    try:
        df_5m = load_candle_data(pair, "M5", limit=5000) # Need more history for 5M
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"5M data not found for {pair}")
        
    # 4. Analyze Signals
    signals = analyze_5m_signals(df_5m, ranges)
    
    return StrategyResponse(
        pair=pair,
        ranges=ranges,
        signals=signals
    )


@router.get("/journal")
async def get_journal(
    pair: str = Query(..., description="Currency pair"),
):
    """
    Get journal data with trade records, account state, and stats
    """
    from app.services.journal import journal_service
    
    # First get strategy signals
    try:
        df_4h = load_candle_data(pair, "H4", limit=1000)
        df_5m = load_candle_data(pair, "M5", limit=5000)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    ranges = detect_4h_range(df_4h)
    signals = analyze_5m_signals(df_5m, ranges)
    
    # Process through journal service
    journal_data = journal_service.process_signals(signals, pair)
    
    return journal_data


@router.get("/swings", response_model=SwingAnalysis)
async def analyze_swings(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query(..., description="Timeframe"),
    lookback_left: Optional[int] = Query(None, description="Left lookback window (optional, auto-calculated)"),
    lookback_right: Optional[int] = Query(None, description="Right lookback window (optional, auto-calculated)"),
    limit: Optional[int] = Query(1000, description="Number of candles to analyze")
):
    """
    Detect swing highs and swing lows
    """
    try:
        # Load data
        df = load_candle_data(pair, timeframe, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Get optimal lookback if not provided
    if lookback_left is None or lookback_right is None:
        auto_left, auto_right = get_optimal_lookback(timeframe)
        lookback_left = lookback_left or auto_left
        lookback_right = lookback_right or auto_right
    
    # Detect swings
    detector = SwingDetector(lookback_left=lookback_left, lookback_right=lookback_right)
    swing_data = detector.get_swing_data(df)
    
    return SwingAnalysis(
        pair=pair,
        timeframe=timeframe,
        swing_highs=swing_data['swing_highs'],
        swing_lows=swing_data['swing_lows'],
        total_swings=len(swing_data['swing_highs']) + len(swing_data['swing_lows']),
        lookback_left=lookback_left,
        lookback_right=lookback_right
    )


@router.get("/order-blocks", response_model=OrderBlockAnalysis)
async def analyze_order_blocks(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query(..., description="Timeframe"),
    lookback_window: Optional[int] = Query(None, description="OB lookback window (auto-calculated if not provided)"),
    limit: Optional[int] = Query(1000, description="Number of candles to analyze")
):
    """
    Detect order blocks based on liquidity sweeps
    """
    try:
        df = load_candle_data(pair, timeframe, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Get optimal lookback for swings
    swing_lookback_left, swing_lookback_right = get_optimal_lookback(timeframe)
    
    # Detect swings first (required for OB detection)
    from app.smc.swings import SwingDetector
    swing_detector = SwingDetector(lookback_left=swing_lookback_left, lookback_right=swing_lookback_right)
    swing_highs, swing_lows = swing_detector.detect_swings(df)
    
    # Get optimal OB lookback if not provided
    if lookback_window is None:
        from app.smc.order_blocks import get_ob_lookback_window
        lookback_window = get_ob_lookback_window(timeframe)
    
    # Detect market structure (needed for OBs often, but let's see if OB detector needs it)
    # The original code passed 'structure_events' which wasn't defined in the function scope!
    # It seems the original code had a bug or I missed where it came from.
    # Let's detect structure first.
    from app.smc.market_structure import MarketStructureDetector
    structure_detector = MarketStructureDetector()
    structure_events = structure_detector.detect_structure(df, swing_highs, swing_lows)

    # Detect order blocks
    from app.smc.order_blocks import OrderBlockDetector
    ob_detector = OrderBlockDetector(lookback_window=lookback_window)
    
    # Pass structure events to OB detector
    order_blocks = ob_detector.detect_order_blocks(df, structure_events)
    order_blocks = ob_detector.update_ob_states(df, order_blocks)
    
    # Count by type
    bullish_count = sum(1 for ob in order_blocks if ob['type'] == 'bullish')
    bearish_count = sum(1 for ob in order_blocks if ob['type'] == 'bearish')
    
    return OrderBlockAnalysis(
        pair=pair,
        timeframe=timeframe,
        order_blocks=order_blocks,
        total_obs=len(order_blocks),
        bullish_obs=bullish_count,
        bearish_obs=bearish_count,
        lookback_window=lookback_window
    )


@router.get("/market-structure", response_model=MarketStructureAnalysis)
async def analyze_market_structure(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query(..., description="Timeframe"),
    limit: Optional[int] = Query(1000, description="Number of candles to analyze")
):
    """
    Detect market structure (BOS and CHOCH)
    """
    try:
        df = load_candle_data(pair, timeframe, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Get optimal lookback for swings
    swing_lookback_left, swing_lookback_right = get_optimal_lookback(timeframe)
    
    # Detect swings first (required for structure detection)
    from app.smc.swings import SwingDetector
    swing_detector = SwingDetector(lookback_left=swing_lookback_left, lookback_right=swing_lookback_right)
    swing_highs, swing_lows = swing_detector.detect_swings(df)
    
    # Detect market structure
    from app.smc.market_structure import MarketStructureDetector
    structure_detector = MarketStructureDetector()
    structure_events = structure_detector.detect_structure(df, swing_highs, swing_lows)
    
    # Count by type
    bos_count = sum(1 for event in structure_events if event['type'] == 'BOS')
    choch_count = sum(1 for event in structure_events if event['type'] == 'CHOCH')
    
    return MarketStructureAnalysis(
        pair=pair,
        timeframe=timeframe,
        structure_events=structure_events,
        total_events=len(structure_events),
        bos_count=bos_count,
        choch_count=choch_count
    )


@router.get("/fvg", response_model=FVGAnalysis)
async def analyze_fvg(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query(..., description="Timeframe"),
    limit: Optional[int] = Query(1000, description="Number of candles to analyze")
):
    """Detect Fair Value Gaps (imbalance zones)"""
    try:
        df = load_candle_data(pair, timeframe, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    from app.smc.fvg import FVGDetector
    fvg_detector = FVGDetector()
    fvgs = fvg_detector.detect_fvgs(df)
    
    bullish_count = sum(1 for fvg in fvgs if fvg['type'] == 'bullish')
    bearish_count = sum(1 for fvg in fvgs if fvg['type'] == 'bearish')
    
    return FVGAnalysis(
        pair=pair,
        timeframe=timeframe,
        fvgs=fvgs,
        total_fvgs=len(fvgs),
        bullish_fvgs=bullish_count,
        bearish_fvgs=bearish_count
    )


@router.get("/liquidity", response_model=LiquidityAnalysis)
async def analyze_liquidity(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query(..., description="Timeframe"),
    limit: Optional[int] = Query(1000, description="Number of candles to analyze")
):
    """Detect Buy-Side and Sell-Side Liquidity zones"""
    try:
        df = load_candle_data(pair, timeframe, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Detect swings
    swing_length = get_optimal_lookback(timeframe)
    from app.smc.swings import SwingDetector
    swing_detector = SwingDetector(lookback_left=swing_length[0], lookback_right=swing_length[1])
    swing_highs, swing_lows = swing_detector.detect_swings(df)
    
    # Detect liquidity zones
    from app.smc.liquidity import LiquidityDetector
    liq_detector = LiquidityDetector()
    liquidity_zones = liq_detector.detect_liquidity_zones(df, swing_highs, swing_lows)
    
    # Detect FVGs to add their 50% levels as liquidity
    from app.smc.fvg import FVGDetector
    fvg_detector = FVGDetector()
    fair_value_gaps = fvg_detector.detect_fvgs(df)

    # Add FVG 50% levels to liquidity zones
    for fvg in fair_value_gaps:
        if fvg['state'] == 'active':
            mid_price = (fvg['top'] + fvg['bottom']) / 2
            liquidity_zones.append({
                'type': 'buy_side' if fvg['type'] == 'bearish' else 'sell_side', 
                'subtype': 'fvg_mid',
                'price': mid_price,
                'timestamp': fvg['timestamp'],
                'index': fvg['candle_index'],
                'swept': False
            })
            
    # Count by type
    bsl_count = sum(1 for liq in liquidity_zones if liq['type'] == 'buy_side')
    ssl_count = sum(1 for liq in liquidity_zones if liq['type'] == 'sell_side')
    
    return LiquidityAnalysis(
        pair=pair,
        timeframe=timeframe,
        liquidity_zones=liquidity_zones,
        total_zones=len(liquidity_zones),
        bsl_count=bsl_count,
        ssl_count=ssl_count
    )

