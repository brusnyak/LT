"""SMC Analysis API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.core.data_loader import load_candle_data
from app.core.constants import Pair, Timeframe
from app.smc.swings import SwingDetector, get_optimal_lookback
from app.models.smc import (
    SwingAnalysis, OrderBlockAnalysis, MarketStructureAnalysis,
    FVGAnalysis, LiquidityAnalysis, LiquidityZone, # Import LiquidityZone
    FVGResponse, LiquidityZoneResponse, OrderBlockResponse, MarketStructureEvent  # Add Response models
)
from app.models.strategy import StrategyResponse, Signal
from app.strategies.human_trained_strategy import HumanTrainedStrategy

router = APIRouter()


@router.get("/human-trained", response_model=StrategyResponse)
async def analyze_human_trained(
    pair: str = Query(..., description="Currency pair (e.g., EURUSD, XAUUSD)"),
    timeframe: str = Query("M15", description="Timeframe for analysis"),
    limit: int = Query(1000, description="Number of candles to analyze")
):
    """
    Human-Trained Strategy - SMC-based strategy replicating manual trading
    
    Returns:
    - signals: List of trade setups with Entry/SL/TP
    - analysis: Market structure, POIs, liquidity zones
    """
    try:
        # Load data
        df = load_candle_data(pair, timeframe, limit=limit)
        
        # Initialize strategy
        strategy = HumanTrainedStrategy()
        
        # Generate signals by iterating through history (mini-backtest)
        # This ensures we see past signals on the chart, not just the current one
        raw_signals = []
        
        # Determine start index (look back at most 500 candles for signals to avoid timeout)
        # We need enough history for indicators (e.g. 200 candles)
        min_history = 200
        scan_limit = min(limit, 500)  # Reduced from 2000 to 500 for faster loading
        start_idx = max(min_history, len(df) - scan_limit)
        
        # Iterate with stride of 5 to catch signals while maintaining performance
        # Checking every 5 candles is sufficient for most setups
        stride = 5  # Increased from 1 to 5 for 5x speed improvement
        
        for i in range(start_idx, len(df), stride):
            # Slice data up to current point
            current_df = df.iloc[:i+1]
            
            # Generate signal for this moment
            # We pass the same data for all TFs as a simplification for now
            # In production, we should resample properly
            sigs = strategy.generate_signals(pair, current_df, current_df, current_df)
            
            if sigs:
                raw_signals.extend(sigs)
        
        # Convert to Signal model format
        signals = []
        for sig in raw_signals:
            signals.append(Signal(
                type=sig['type'],
                entry=sig['entry'],
                sl=sig['sl'],
                tp=sig['tp'],
                rr=sig.get('rr', 0),
                # Use signal time if available, otherwise current time (fallback)
                time=sig.get('time', df['time'].iloc[-1] if 'time' in df.columns else None),
                pair=sig.get('symbol', pair),
                confidence=sig.get('strength', 0.8),
                poi_type=sig.get('poi_type', 'OB'),
                structure=sig.get('structure', 'neutral')
            ))
        
        return StrategyResponse(
            pair=pair,
            timeframe=timeframe,
            strategy="Human-Trained",
            signals=signals,
            ranges=[],
            analysis={
                'total_signals': len(signals),
                'strategy_version': '3B',
                'features': ['Structure', 'Shift', 'POI', 'Premium/Discount', 'Liquidity', 'Inducement']
            }
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Data not found for {pair} {timeframe}: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/signals")
async def get_signals(
    pair: str = Query("EURUSD", description="Currency pair"),
    strategy: str = Query("human-trained", description="Strategy name"),
    timeframe: str = Query("M15", description="Timeframe"),
    limit: int = Query(500, description="Number of candles")
):
    """
    Get trading signals - endpoint for Telegram signal monitor
    """
    if strategy == "human-trained":
        result = await analyze_human_trained(pair=pair, timeframe=timeframe, limit=limit)
        return {"signals": [s.dict() for s in result.signals]}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")


@router.get("/journal")
async def get_journal(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query("M15", description="Timeframe")
):
    """
    Journal endpoint - returns recent signals for journaling
    """
    try:
        # Get strategy result
        result = await analyze_human_trained(pair, timeframe, limit=500)
        
        # Load data to get timestamp
        df = load_candle_data(pair, timeframe, limit=10)
        
        return {
            'pair': pair,
            'timeframe': timeframe,
            'signals': [s.dict() for s in result.signals],
            'timestamp': str(df['time'].iloc[-1]) if 'time' in df.columns and len(df) > 0 else None
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    swing_highs, swing_lows = detector.detect_swings(df) # Returns SwingPoint objects
    
    return SwingAnalysis(
        pair=pair,
        timeframe=timeframe,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
        total_swings=len(swing_highs) + len(swing_lows),
        lookback_left=lookback_left,
        lookback_right=lookback_right
    )


@router.get("/order-blocks", response_model=OrderBlockAnalysis)
async def analyze_order_blocks(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query(..., description="Timeframe"),
    lookback_window: Optional[int] = Query(None, description="OB lookback window (auto-calculated if not provided)"),
    limit: Optional[int] = Query(1000, description="Number of candles to analyze"),
    timeframe_ltf: Optional[str] = Query(None, description="Lower timeframe for OB refinement (e.g., M1)")
):
    """
    Detect order blocks based on market structure breaks
    """
    try:
        df = load_candle_data(pair, timeframe, limit=limit)
        df_ltf = None
        if timeframe_ltf:
            df_ltf = load_candle_data(pair, timeframe_ltf, limit=limit * 5) # Load more LTF data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Get optimal lookback for swings
    swing_lookback_left, swing_lookback_right = get_optimal_lookback(timeframe)
    
    # Detect swings first (required for OB detection)
    from app.smc.swings import SwingDetector
    swing_detector = SwingDetector(lookback_left=swing_lookback_left, lookback_right=swing_lookback_right)
    swing_highs, swing_lows = swing_detector.detect_swings(df)
    classified_swings = swing_detector.classify_swings(swing_highs, swing_lows)
    
    # Get optimal OB lookback if not provided
    if lookback_window is None:
        from app.smc.order_blocks import get_ob_lookback_window
        lookback_window = get_ob_lookback_window(timeframe)
    
    # Detect market structure (needed for OBs)
    from app.smc.market_structure import MarketStructureDetector
    structure_detector = MarketStructureDetector()
    structure_events = structure_detector.detect_structure(df, classified_swings) # Pass classified swings

    # Detect order blocks
    from app.smc.order_blocks import OrderBlockDetector
    ob_detector = OrderBlockDetector(lookback_window=lookback_window)
    
    # Pass structure events and LTF data to OB detector
    order_blocks = ob_detector.detect_order_blocks(df, structure_events, df_ltf=df_ltf)
    order_blocks = ob_detector.update_ob_states(df, order_blocks)
    
    # Count by type
    bullish_count = sum(1 for ob in order_blocks if ob.type == 'bullish')
    bearish_count = sum(1 for ob in order_blocks if ob.type == 'bearish')
    
    # Convert to response objects
    ob_responses = [
        OrderBlockResponse(
            type=ob.type,
            candle_index=ob.candle_index,
            timestamp=ob.timestamp,
            high=ob.high,
            low=ob.low,
            mid=ob.mid,
            state=ob.state,
            liquidity_swept=ob.liquidity_swept,
            lookback_candles=ob.lookback_candles
        ) for ob in order_blocks
    ]

    return OrderBlockAnalysis(
        pair=pair,
        timeframe=timeframe,
        order_blocks=ob_responses,
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
    classified_swings = swing_detector.classify_swings(swing_highs, swing_lows)
    
    # Detect market structure
    from app.smc.market_structure import MarketStructureDetector
    structure_detector = MarketStructureDetector()
    structure_events = structure_detector.detect_structure(df, classified_swings) # Pass classified swings
    
    # Count by type
    bos_count = sum(1 for event in structure_events if event.type == 'BOS')
    choch_count = sum(1 for event in structure_events if event.type == 'CHOCH')
    
    # Convert to response objects
    structure_responses = [
        MarketStructureEvent(
            type=event.type,
            direction=event.direction,
            index=event.index,
            price=event.price,
            timestamp=event.timestamp,
            description=event.description,
            pivot_index=event.pivot_index,
            pivot_timestamp=event.pivot_timestamp
        ) for event in structure_events
    ]

    return MarketStructureAnalysis(
        pair=pair,
        timeframe=timeframe,
        structure_events=structure_responses,
        total_events=len(structure_events),
        bos_count=bos_count,
        choch_count=choch_count
    )


@router.get("/fvg", response_model=FVGAnalysis)
async def analyze_fvg(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query(..., description="Timeframe"),
    limit: Optional[int] = Query(1000, description="Number of candles to analyze"),
    use_auto_threshold: Optional[bool] = Query(True, description="Use dynamic threshold for FVG detection")
):
    """Detect Fair Value Gaps (imbalance zones)"""
    try:
        df = load_candle_data(pair, timeframe, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    from app.smc.fvg import FVGDetector
    fvg_detector = FVGDetector()
    fvgs = fvg_detector.detect_fvgs(df, use_auto_threshold=use_auto_threshold) # Pass auto_threshold
    
    bullish_count = sum(1 for fvg in fvgs if fvg.type == 'bullish')
    bearish_count = sum(1 for fvg in fvgs if fvg.type == 'bearish')
    
    # Convert to response objects
    fvg_responses = [
        FVGResponse(
            type=fvg.type,
            start_index=fvg.start_index,
            end_index=fvg.end_index,
            top=fvg.top,
            bottom=fvg.bottom,
            timestamp=fvg.timestamp,
            filled=fvg.filled
        ) for fvg in fvgs
    ]

    return FVGAnalysis(
        pair=pair,
        timeframe=timeframe,
        fvgs=fvg_responses,
        total_fvgs=len(fvgs),
        bullish_fvgs=bullish_count,
        bearish_fvgs=bearish_count
    )


@router.get("/liquidity", response_model=LiquidityAnalysis)
async def analyze_liquidity(
    pair: str = Query(..., description="Currency pair"),
    timeframe: str = Query(..., description="Timeframe"),
    limit: Optional[int] = Query(1000, description="Number of candles to analyze"),
    sweep_threshold: Optional[float] = Query(0.5, description="Multiplier for ATR to determine liquidity sweep threshold."),
    eqh_eql_threshold: Optional[float] = Query(0.1, description="Multiplier for ATR to determine Equal High/Low threshold.")
):
    """Detect Buy-Side and Sell-Side Liquidity zones"""
    try:
        df = load_candle_data(pair, timeframe, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Detect swings
    swing_lookback_left, swing_lookback_right = get_optimal_lookback(timeframe)
    from app.smc.swings import SwingDetector
    swing_detector = SwingDetector(lookback_left=swing_lookback_left, lookback_right=swing_lookback_right)
    swing_highs, swing_lows = swing_detector.detect_swings(df) # Returns SwingPoint objects
    
    # Detect liquidity zones
    from app.smc.liquidity import LiquidityDetector
    liq_detector = LiquidityDetector()
    liquidity_zones = liq_detector.detect_liquidity_zones(
        df, swing_highs, swing_lows, # Pass SwingPoint objects
        sweep_threshold_multiplier=sweep_threshold,
        eqh_eql_threshold_multiplier=eqh_eql_threshold
    )
    
    # Detect FVGs to add their 50% levels as liquidity (FVG objects now)
    from app.smc.fvg import FVGDetector
    fvg_detector = FVGDetector()
    fair_value_gaps = fvg_detector.detect_fvgs(df)

    # Add FVG 50% levels to liquidity zones
    for fvg in fair_value_gaps:
        if fvg.mitigation_level < 4: # Check mitigation_level instead of 'filled'
            mid_price = (fvg.top + fvg.bottom) / 2
            liquidity_zones.append(LiquidityZone( # Append LiquidityZone object
                type='buy_side' if fvg.type == 'bearish' else 'sell_side', 
                subtype='fvg_mid',
                price=mid_price,
                timestamp=fvg.timestamp,
                index=fvg.end_index,
                swept=False
            ))
            
    # Count by type
    bsl_count = sum(1 for liq in liquidity_zones if liq.type == 'buy_side')
    ssl_count = sum(1 for liq in liquidity_zones if liq.type == 'sell_side')
    
    # Convert to response objects
    liq_responses = [
        LiquidityZoneResponse(
            type=liq.type,
            price=liq.price,
            timestamp=liq.timestamp,
            index=liq.index,
            swept=liq.swept,
            sweep_time=liq.sweep_time,
            subtype=liq.subtype
        ) for liq in liquidity_zones
    ]

    return LiquidityAnalysis(
        pair=pair,
        timeframe=timeframe,
        liquidity_zones=liq_responses,
        total_zones=len(liquidity_zones),
        bsl_count=bsl_count,
        ssl_count=ssl_count
    )

# TEMPORARILY DISABLED - Strategy imports broken
# @router.get("/signals/list")
# async def get_signals_list(...):
#     ...
