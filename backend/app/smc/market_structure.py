"""
Market Structure Detection (BOS/CHOCH)

Market structure identifies trend direction and reversals:
- BOS (Break of Structure): Continuation of trend (higher high/lower low)
- CHOCH (Change of Character): Potential trend reversal

Detection:
1. Track swing highs and swing lows
2. Compare consecutive swings to identify structure breaks
3. Label as BOS or CHOCH based on pattern
"""
from typing import List, Dict, Literal
import pandas as pd


class MarketStructureDetector:
    """
    Detect market structure shifts (BOS and CHOCH)
    
    BOS (Break of Structure):
    - Bullish: Price makes a higher high (breaks previous swing high)
    - Bearish: Price makes a lower low (breaks previous swing low)
    
    CHOCH (Change of Character):
    - Bullish to Bearish: Price makes a lower high after uptrend
    - Bearish to Bullish: Price makes a higher low after downtrend
    """
    
    def __init__(self):
        pass
    
    def detect_structure(
        self, 
        df: pd.DataFrame,
        swing_highs: List[int],
        swing_lows: List[int],
        confirmation_candles: int = 2
    ) -> List[Dict]:
        """
        Detect market structure shifts using crossover logic with confirmation
        
        BOS/CHOCH is detected when price crosses a swing pivot level:
        - Bullish: Price closes above swing high (with confirmation for CHOCH)
        - Bearish: Price closes below swing low (with confirmation for CHOCH)
        
        Args:
            df: OHLCV dataframe
            swing_highs: Indices of swing high points
            swing_lows: Indices of swing low points
            confirmation_candles: Number of candles to confirm CHOCH (default: 2)
            
        Returns:
            List of structure events (BOS/CHOCH) with line coordinates
        """
        structure_events = []
        
        if len(swing_highs) < 1 or len(swing_lows) < 1:
            return structure_events
        
        # Track current trend
        current_trend = None  # 'bullish' or 'bearish'
        
        # Track which pivots have been crossed
        crossed_highs = set()
        crossed_lows = set()
        
        # Go through each candle
        for i in range(len(df)):
            close_price = df['close'].iloc[i]
            
            # Check for crossover of swing highs (bullish structure)
            for swing_idx in swing_highs:
                if swing_idx >= i:  # Only consider past swings
                    continue
                if swing_idx in crossed_highs:  # Already crossed
                    continue
                    
                swing_high_price = df['high'].iloc[swing_idx]
                
                # Price crossed above swing high
                if close_price > swing_high_price:
                    # Determine if BOS or CHOCH
                    if current_trend == 'bullish':
                        tag = 'BOS'  # Continuation - no confirmation needed
                    else:
                        # CHOCH - need confirmation
                        tag = 'CHOCH'
                        
                        # Check if we have enough candles ahead for confirmation
                        if i + confirmation_candles >= len(df):
                            continue  # Not enough candles to confirm
                        
                        # Verify price stays above for confirmation_candles
                        confirmed = True
                        for j in range(1, confirmation_candles + 1):
                            if df['close'].iloc[i + j] <= swing_high_price:
                                confirmed = False
                                break
                        
                        if not confirmed:
                            continue  # Wait for confirmation
                        
                        current_trend = 'bullish'
                    
                    # Find origin of the move (most recent swing low before this break)
                    # We want the last swing low that is < i
                    origin_idx = None
                    for sl_idx in reversed(swing_lows):
                        if sl_idx < i:
                            origin_idx = sl_idx
                            break
                    
                    structure_events.append({
                        'type': tag,
                        'direction': 'bullish',
                        'index': i,
                        'price': swing_high_price,
                        'timestamp': df.index[i],
                        'description': f'{"Higher High" if tag == "BOS" else "Trend shift to bullish (confirmed)"}',
                        'pivot_index': swing_idx,
                        'pivot_timestamp': df.index[swing_idx],
                        'impulse_origin_index': origin_idx  # Added for OB detection
                    })
                    
                    crossed_highs.add(swing_idx)
                    break  # Only one structure per candle
            
            # Check for crossunder of swing lows (bearish structure)
            for swing_idx in swing_lows:
                if swing_idx >= i:  # Only consider past swings
                    continue
                if swing_idx in crossed_lows:  # Already crossed
                    continue
                    
                swing_low_price = df['low'].iloc[swing_idx]
                
                # Price crossed below swing low
                if close_price < swing_low_price:
                    # Determine if BOS or CHOCH
                    if current_trend == 'bearish':
                        tag = 'BOS'  # Continuation - no confirmation needed
                    else:
                        # CHOCH - need confirmation
                        tag = 'CHOCH'
                        
                        # Check if we have enough candles ahead for confirmation
                        if i + confirmation_candles >= len(df):
                            continue  # Not enough candles to confirm
                        
                        # Verify price stays below for confirmation_candles
                        confirmed = True
                        for j in range(1, confirmation_candles + 1):
                            if df['close'].iloc[i + j] >= swing_low_price:
                                confirmed = False
                                break
                        
                        if not confirmed:
                            continue  # Wait for confirmation
                        
                        current_trend = 'bearish'
                    
                    # Find origin of the move (most recent swing high before this break)
                    # We want the last swing high that is < i
                    origin_idx = None
                    for sh_idx in reversed(swing_highs):
                        if sh_idx < i:
                            origin_idx = sh_idx
                            break

                    structure_events.append({
                        'type': tag,
                        'direction': 'bearish',
                        'index': i,
                        'price': swing_low_price,
                        'timestamp': df.index[i],
                        'description': f'{"Lower Low" if tag == "BOS" else "Trend shift to bearish (confirmed)"}',
                        'pivot_index': swing_idx,
                        'pivot_timestamp': df.index[swing_idx],
                        'impulse_origin_index': origin_idx  # Added for OB detection
                    })
                    
                    crossed_lows.add(swing_idx)
                    break  # Only one structure per candle
        
        return structure_events
