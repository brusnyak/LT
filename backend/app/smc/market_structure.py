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
from typing import List, Dict, Literal, Optional
import pandas as pd
from app.models.smc import SwingPoint, MarketStructureEvent # Import SwingPoint and MarketStructureEvent models


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
        classified_swings: List[SwingPoint],
    ) -> List[MarketStructureEvent]:
        """
        Detect market structure shifts (BOS and CHOCH) using classified swing points.
        
        Args:
            df: OHLCV dataframe (used for timestamps and prices)
            classified_swings: List of SwingPoint objects (HH, HL, LH, LL)
            
        Returns:
            List of MarketStructureEvent objects
        """
        structure_events: List[MarketStructureEvent] = []
        
        if len(classified_swings) < 2:
            return structure_events
        
        # Track the current market structure bias
        # 'bullish' (HH, HL sequence), 'bearish' (LH, LL sequence), or 'ranging'
        current_structure_bias: Literal['bullish', 'bearish', 'ranging'] = 'ranging'
        
        # Iterate through classified swings to identify patterns
        for i in range(1, len(classified_swings)):
            prev_swing = classified_swings[i-1]
            current_swing = classified_swings[i]

            # Determine if current_swing is a higher/lower high/low relative to the *previous relevant swing*
            # This logic is simplified by the `classify_swings` method in SwingDetector
            
            # Check for BOS (Break of Structure)
            if current_swing.type == 'HH' and prev_swing.type == 'HL' and current_structure_bias == 'bullish':
                # Bullish BOS: Higher High after a Higher Low in a bullish trend
                structure_events.append(MarketStructureEvent(
                    type='BOS',
                    direction='bullish',
                    index=current_swing.index,
                    price=current_swing.price,
                    timestamp=current_swing.timestamp,
                    description='Bullish Break of Structure (HH)',
                    pivot_index=prev_swing.index,
                    pivot_timestamp=prev_swing.timestamp
                ))
                current_structure_bias = 'bullish' # Confirm bullish continuation
            elif current_swing.type == 'LL' and prev_swing.type == 'LH' and current_structure_bias == 'bearish':
                # Bearish BOS: Lower Low after a Lower High in a bearish trend
                structure_events.append(MarketStructureEvent(
                    type='BOS',
                    direction='bearish',
                    index=current_swing.index,
                    price=current_swing.price,
                    timestamp=current_swing.timestamp,
                    description='Bearish Break of Structure (LL)',
                    pivot_index=prev_swing.index,
                    pivot_timestamp=prev_swing.timestamp
                ))
                current_structure_bias = 'bearish' # Confirm bearish continuation

            # Check for CHOCH (Change of Character)
            # Bullish CHOCH: A bearish trend (LH, LL) is broken by a HL followed by a HH
            if current_swing.type == 'HH' and prev_swing.type == 'HL' and current_structure_bias == 'bearish':
                structure_events.append(MarketStructureEvent(
                    type='CHOCH',
                    direction='bullish',
                    index=current_swing.index,
                    price=current_swing.price,
                    timestamp=current_swing.timestamp,
                    description='Change of Character (Bullish)',
                    pivot_index=prev_swing.index,
                    pivot_timestamp=prev_swing.timestamp
                ))
                current_structure_bias = 'bullish' # Trend has shifted to bullish
            # Bearish CHOCH: A bullish trend (HH, HL) is broken by a LH followed by a LL
            elif current_swing.type == 'LL' and prev_swing.type == 'LH' and current_structure_bias == 'bullish':
                structure_events.append(MarketStructureEvent(
                    type='CHOCH',
                    direction='bearish',
                    index=current_swing.index,
                    price=current_swing.price,
                    timestamp=current_swing.timestamp,
                    description='Change of Character (Bearish)',
                    pivot_index=prev_swing.index,
                    pivot_timestamp=prev_swing.timestamp
                ))
                current_structure_bias = 'bearish' # Trend has shifted to bearish
            
            # Update current_structure_bias if it's ranging or just starting
            if current_structure_bias == 'ranging':
                if current_swing.type == 'HH' or current_swing.type == 'HL':
                    current_structure_bias = 'bullish'
                elif current_swing.type == 'LH' or current_swing.type == 'LL':
                    current_structure_bias = 'bearish'
        
        return structure_events
