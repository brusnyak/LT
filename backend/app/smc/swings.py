"""
Swing Detection Algorithm for SMC Analysis

Swing highs and swing lows are critical for:
- Order block identification
- Market structure (BOS/CHOCH)
- Liquidity zone detection
"""
from typing import List, Tuple, Literal
import pandas as pd
import numpy as np
from app.core.constants import Timeframe
from app.models.smc import SwingPoint # Import the SwingPoint model


class SwingDetector:
    """
    Detects swing points using standard pivot/fractal logic.
    
    A Swing High is a candle with a high greater than 'lookback_left' candles to the left
    and 'lookback_right' candles to the right.
    
    A Swing Low is a candle with a low lower than 'lookback_left' candles to the left
    and 'lookback_right' candles to the right.
    """
    
    def __init__(self, lookback_left: int = 20, lookback_right: int = 20):
        """
        Args:
            lookback_left: Number of bars to look back (left side)
            lookback_right: Number of bars to look forward (right side)
        """
        self.lookback_left = lookback_left
        self.lookback_right = lookback_right

    def detect_swings(self, df: pd.DataFrame) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Detect swing highs and lows and return them as SwingPoint objects.
        
        Returns:
            Tuple of (list_of_swing_high_objects, list_of_swing_low_objects)
        """
        highs = df['high'].values
        lows = df['low'].values
        n = len(df)
        
        swing_highs: List[SwingPoint] = []
        swing_lows: List[SwingPoint] = []
        
        start_idx = self.lookback_left
        end_idx = n - self.lookback_right
        
        for i in range(start_idx, end_idx):
            current_high = highs[i]
            current_low = lows[i]
            
            is_swing_high = True
            for j in range(1, self.lookback_left + 1):
                if highs[i - j] > current_high:
                    is_swing_high = False
                    break
            if is_swing_high:
                for j in range(1, self.lookback_right + 1):
                    if highs[i + j] >= current_high:
                        is_swing_high = False
                        break
            
            if is_swing_high:
                swing_highs.append(SwingPoint(
                    index=int(i),
                    timestamp=df.index[i],
                    price=float(df['high'].iloc[i]),
                    type="swing_high"
                ))
                
            is_swing_low = True
            for j in range(1, self.lookback_left + 1):
                if lows[i - j] < current_low:
                    is_swing_low = False
                    break
            if is_swing_low:
                for j in range(1, self.lookback_right + 1):
                    if lows[i + j] <= current_low:
                        is_swing_low = False
                        break
            
            if is_swing_low:
                swing_lows.append(SwingPoint(
                    index=int(i),
                    timestamp=df.index[i],
                    price=float(df['low'].iloc[i]),
                    type="swing_low"
                ))
                    
        return swing_highs, swing_lows

    def classify_swings(self, swing_highs: List[SwingPoint], swing_lows: List[SwingPoint]) -> List[SwingPoint]:
        """
        Classifies swing points into HH, HL, LH, LL based on their relationship to previous swings.
        Combines and sorts swing highs and lows by timestamp.
        """
        all_swings = sorted(swing_highs + swing_lows, key=lambda x: x.timestamp)
        
        classified_swings: List[SwingPoint] = []
        
        if not all_swings:
            return []

        # Initialize with the first swing point
        classified_swings.append(all_swings[0])

        for i in range(1, len(all_swings)):
            current_swing = all_swings[i]
            previous_swing = classified_swings[-1] # Always compare to the last classified swing

            if current_swing.type == 'swing_high':
                if current_swing.price > previous_swing.price:
                    current_swing.type = 'HH' # Higher High
                else:
                    current_swing.type = 'LH' # Lower High
            elif current_swing.type == 'swing_low':
                if current_swing.price > previous_swing.price:
                    current_swing.type = 'HL' # Higher Low
                else:
                    current_swing.type = 'LL' # Lower Low
            
            classified_swings.append(current_swing)
            
        return classified_swings

    def get_swing_data(self, df: pd.DataFrame) -> dict:
        """
        Get structured swing data including price and timestamp.
        This method now uses the new detect_swings and classify_swings.
        """
        swing_highs, swing_lows = self.detect_swings(df)
        
        # Classify the swings
        classified_swings = self.classify_swings(swing_highs, swing_lows)
            
        return {
            "swing_highs": swing_highs, # Raw swing highs
            "swing_lows": swing_lows,   # Raw swing lows
            "classified_swings": classified_swings # HH, HL, LH, LL
        }

def get_optimal_lookback(timeframe: str) -> Tuple[int, int]:
    """
    Get optimal swing length based on timeframe.
    Returns (lookback_left, lookback_right)
    """
    # Handle both string and Enum
    try:
        tf = Timeframe(timeframe)
    except ValueError:
        # Fallback for string matching if enum fails
        tf_str = str(timeframe).upper()
        if tf_str in ['M1', '1M']: tf = Timeframe.M1
        elif tf_str in ['M5', '5M']: tf = Timeframe.M5
        elif tf_str in ['M15', '15M']: tf = Timeframe.M15
        elif tf_str in ['M30', '30M']: tf = Timeframe.M30
        elif tf_str in ['H1', '1H']: tf = Timeframe.H1
        elif tf_str in ['H4', '4H']: tf = Timeframe.H4
        elif tf_str in ['D1', '1D']: tf = Timeframe.D1
        else: tf = Timeframe.M5 # Default
    
    # Default config (Left, Right)
    # Using smaller right lookback for faster detection (less lag)
    if tf in [Timeframe.M1, Timeframe.M5]:
        return (10, 5) 
    elif tf in [Timeframe.M15, Timeframe.M30]:
        return (5, 3) 
    elif tf in [Timeframe.H1, Timeframe.H4]:
        return (5, 3)
    elif tf == Timeframe.D1:
        return (3, 2)
    else:
        return (5, 3)
