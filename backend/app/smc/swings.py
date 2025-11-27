"""
Swing Detection Algorithm for SMC Analysis

Swing highs and swing lows are critical for:
- Order block identification
- Market structure (BOS/CHOCH)
- Liquidity zone detection
"""
from typing import List, Tuple
import pandas as pd
import numpy as np
from app.core.constants import Timeframe


class SwingDetector:
    """
    Detects swing points using 'Leg' based logic from Pine Script.
    
    Logic:
    - A Swing High is confirmed when high[size] > highest(high, size) (right side confirmation)
    - A Swing Low is confirmed when low[size] < lowest(low, size) (right side confirmation)
    - Tracks 'Leg' state (Bullish/Bearish) to identify trend direction.
    """
    
    def __init__(self, swing_length: int = 50):
        """
        Args:
            swing_length: Number of bars to look back/forward (the 'size' parameter in Pine)
        """
        self.swing_length = swing_length

    def detect_swings(self, df: pd.DataFrame) -> Tuple[List[int], List[int]]:
        """
        Detect swing highs and lows.
        
        Returns:
            Tuple of (swing_high_indices, swing_low_indices)
        """
        highs = df['high'].values
        lows = df['low'].values
        n = len(df)
        
        swing_highs = []
        swing_lows = []
        
        # Current leg state (0 = Bearish, 1 = Bullish)
        # Initialize with 0 (Bearish) or 1 (Bullish) - doesn't matter much for start
        current_leg = 0 
        
        for i in range(self.swing_length, n):
            # Index of the potential swing point (size bars ago)
            swing_idx = i - self.swing_length
            
            # Get the potential swing high/low values
            potential_high = highs[swing_idx]
            potential_low = lows[swing_idx]
            
            # Check right side (from swing_idx + 1 to i)
            # We want to know if potential_high is strictly greater than all highs in [swing_idx+1 ... i]
            # In Python slices: highs[swing_idx+1 : i+1]
            right_side_highs = highs[swing_idx+1 : i+1]
            right_side_lows = lows[swing_idx+1 : i+1]
            
            if len(right_side_highs) == 0:
                continue
                
            is_highest_right = potential_high > np.max(right_side_highs)
            is_lowest_right = potential_low < np.min(right_side_lows)
            
            # Determine new leg state
            # If confirmed high -> Start of Bearish Leg -> leg = 0
            # If confirmed low -> Start of Bullish Leg -> leg = 1
            
            previous_leg = current_leg
            
            if is_highest_right:
                current_leg = 0 # BEARISH_LEG
            elif is_lowest_right:
                current_leg = 1 # BULLISH_LEG
                
            # Check for change in leg (Pivot Confirmation)
            if current_leg != previous_leg:
                if current_leg == 0: # Changed to Bearish -> Confirmed Swing High (Start of Bearish Leg)
                    swing_highs.append(swing_idx)
                    
                elif current_leg == 1: # Changed to Bullish -> Confirmed Swing Low (Start of Bullish Leg)
                    swing_lows.append(swing_idx)
                    
        return swing_highs, swing_lows


def get_optimal_lookback(timeframe: str) -> int:
    """
    Get optimal swing length based on timeframe.
    Matches Pine Script 'swingsLengthInput' default or adjustments.
    """
    tf = Timeframe(timeframe)
    
    # Default from Pine Script is 50
    if tf in [Timeframe.M1, Timeframe.M5]:
        return 50 # Larger lookback for noise
    elif tf in [Timeframe.M15, Timeframe.M30]:
        return 20 # Standard
    elif tf in [Timeframe.H1, Timeframe.H4]:
        return 10 # Shorter for HTF
    elif tf == Timeframe.D1:
        return 5
    else:
        return 20
