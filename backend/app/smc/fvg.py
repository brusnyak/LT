"""
Fair Value Gap (FVG) Detection

FVGs are imbalance zones where price moved too quickly, leaving a gap.
They act as magnets for price to return and "fill the gap".

Detection:
- Bullish FVG: Gap between candle[i-2].high and candle[i].low (price gap up)
- Bearish FVG: Gap between candle[i-2].low and candle[i].high (price gap down)
"""
from typing import List, Dict
import pandas as pd


class FVGDetector:
    """Detect Fair Value Gaps (imbalance zones)"""
    
    def __init__(self, min_gap_size: float = 0.0001):
        """
        Args:
            min_gap_size: Minimum gap size to consider (in price units)
        """
        self.min_gap_size = min_gap_size
    
    def detect_fvgs(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect Fair Value Gaps
        
        Args:
            df: OHLCV dataframe
            
        Returns:
            List of FVG dictionaries
        """
        fvgs = []
        
        # Need at least 3 candles
        for i in range(2, len(df)):
            candle_prev2 = df.iloc[i - 2]
            candle_prev1 = df.iloc[i - 1]
            candle_curr = df.iloc[i]
            
            # Bullish FVG: gap between candle[i-2].high and candle[i].low
            if candle_curr['low'] > candle_prev2['high'] + self.min_gap_size:
                fvgs.append({
                    'type': 'bullish',
                    'start_index': i - 2,
                    'end_index': i,
                    'top': candle_curr['low'],
                    'bottom': candle_prev2['high'],
                    'timestamp': df.index[i],
                    'filled': False
                })
            
            # Bearish FVG: gap between candle[i-2].low and candle[i].high
            elif candle_curr['high'] < candle_prev2['low'] - self.min_gap_size:
                fvgs.append({
                    'type': 'bearish',
                    'start_index': i - 2,
                    'end_index': i,
                    'top': candle_prev2['low'],
                    'bottom': candle_curr['high'],
                    'timestamp': df.index[i],
                    'filled': False
                })
        
        # Check fill status for each FVG
        for fvg in fvgs:
            # Check if any subsequent candle filled the gap
            for j in range(fvg['end_index'] + 1, len(df)):
                candle = df.iloc[j]
                
                if fvg['type'] == 'bullish':
                    # Filled if price went back down into the gap
                    if candle['low'] <= fvg['bottom']:
                        fvg['filled'] = True
                        break
                else:  # bearish
                    # Filled if price went back up into the gap
                    if candle['high'] >= fvg['top']:
                        fvg['filled'] = True
                        break
        
        return fvgs
