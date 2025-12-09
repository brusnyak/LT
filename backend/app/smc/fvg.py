"""
Fair Value Gap (FVG) Detection

FVGs are imbalance zones where price moved too quickly, leaving a gap.
They act as magnets for price to return and "fill the gap".

Detection:
- Bullish FVG: Gap between candle[i-2].high and candle[i].low (price gap up)
- Bearish FVG: Gap between candle[i-2].low and candle[i].high (price gap down)
"""
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from app.models.smc import FairValueGap # Import FairValueGap model


class FVGDetector:
    """Detect Fair Value Gaps (imbalance zones)"""
    
    def __init__(self, min_gap_size: float = 0.0001):
        """
        Args:
            min_gap_size: Minimum gap size to consider (in price units)
        """
        self.min_gap_size = min_gap_size
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range using EMA for smoothing."""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()
        return atr

    def detect_fvgs(self, df: pd.DataFrame, use_auto_threshold: bool = True) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps with multi-level mitigation.
        
        Args:
            df: OHLCV dataframe
            use_auto_threshold: If True, uses a dynamic threshold based on ATR.
                                If False, uses self.min_gap_size.
            
        Returns:
            List of FairValueGap objects
        """
        fvgs: List[FairValueGap] = []
        
        if len(df) < 3:
            return fvgs

        # Calculate ATR for dynamic threshold
        atr = self._calculate_atr(df, period=200) # Using 200 period as in Pine Script for volatilityMeasure
        
        for i in range(2, len(df)):
            candle_prev2 = df.iloc[i - 2]
            candle_prev1 = df.iloc[i - 1]
            candle_curr = df.iloc[i]
            
            # Determine dynamic threshold for this candle
            threshold = self.min_gap_size
            if use_auto_threshold and not np.isnan(atr.iloc[i]):
                # Pine script uses `ta.cum(math.abs(newTimeframe ? barDeltaPercent : 0)) / bar_index * 2`
                # A simpler proxy for "significant" gap could be a multiple of ATR or average candle range.
                # Let's use a fraction of ATR for now.
                threshold = atr.iloc[i] * 0.1 # 10% of ATR as minimum gap size
                if threshold == 0: # Avoid division by zero or tiny thresholds
                    threshold = self.min_gap_size 
            
            # Bullish FVG: gap between candle[i-2].high and candle[i].low
            if candle_curr['low'] > candle_prev2['high'] + threshold:
                fvgs.append(FairValueGap(
                    type='bullish',
                    start_index=i - 2,
                    end_index=i,
                    top=candle_curr['low'],
                    bottom=candle_prev2['high'],
                    timestamp=df.index[i],
                    filled=False,
                    mitigation_level=0
                ))
            
            # Bearish FVG: gap between candle[i-2].low and candle[i].high
            elif candle_curr['high'] < candle_prev2['low'] - threshold:
                fvgs.append(FairValueGap(
                    type='bearish',
                    start_index=i - 2,
                    end_index=i,
                    top=candle_prev2['low'],
                    bottom=candle_curr['high'],
                    timestamp=df.index[i],
                    filled=False,
                    mitigation_level=0
                ))
        
        # Update mitigation status for each FVG
        for fvg in fvgs:
            fvg_range = fvg.top - fvg.bottom
            if fvg_range == 0: # Avoid division by zero
                continue

            # Check if any subsequent candle interacted with the FVG
            for j in range(fvg.end_index + 1, len(df)):
                candle_high = df['high'].iloc[j]
                candle_low = df['low'].iloc[j]
                
                if fvg.mitigation_level >= 4: # Already fully mitigated
                    break
                
                if fvg.type == 'bullish':
                    # Bullish FVG: price comes down into it
                    if candle_low <= fvg.top: # Price entered the FVG
                        penetration = fvg.top - candle_low
                        fill_percent = penetration / fvg_range
                        
                        if fill_percent >= 1.0:
                            fvg.mitigation_level = 4 # 100% filled
                            fvg.filled = True
                        elif fill_percent >= 0.75:
                            fvg.mitigation_level = max(fvg.mitigation_level, 3)
                        elif fill_percent >= 0.50:
                            fvg.mitigation_level = max(fvg.mitigation_level, 2)
                        elif fill_percent >= 0.25:
                            fvg.mitigation_level = max(fvg.mitigation_level, 1)
                
                elif fvg.type == 'bearish':
                    # Bearish FVG: price comes up into it
                    if candle_high >= fvg.bottom: # Price entered the FVG
                        penetration = candle_high - fvg.bottom
                        fill_percent = penetration / fvg_range
                        
                        if fill_percent >= 1.0:
                            fvg.mitigation_level = 4 # 100% filled
                            fvg.filled = True
                        elif fill_percent >= 0.75:
                            fvg.mitigation_level = max(fvg.mitigation_level, 3)
                        elif fill_percent >= 0.50:
                            fvg.mitigation_level = max(fvg.mitigation_level, 2)
                        elif fill_percent >= 0.25:
                            fvg.mitigation_level = max(fvg.mitigation_level, 1)
        
        return fvgs
