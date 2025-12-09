"""Statistical pattern analyzer for market prediction"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class PatternAnalyzer:
    """Analyzes market patterns to predict future price movement"""
    
    def __init__(self):
        self.patterns = []
    
    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """
        Analyze current trend using swing points and momentum
        
        Returns:
            {
                'direction': 'BULLISH' | 'BEARISH' | 'RANGING',
                'strength': 0-100,
                'momentum': float
            }
        """
        if len(df) < 20:
            return {'direction': 'RANGING', 'strength': 0, 'momentum': 0}
        
        # Calculate momentum using rate of change
        recent = df.tail(20)
        momentum = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / recent['close'].iloc[0] * 100
        
        # Detect swing highs and lows
        highs = recent['high'].rolling(window=5, center=True).max()
        lows = recent['low'].rolling(window=5, center=True).min()
        
        # Count higher highs/lows or lower highs/lows
        hh_count = sum(highs.diff() > 0)
        ll_count = sum(lows.diff() < 0)
        lh_count = sum(highs.diff() < 0)
        hl_count = sum(lows.diff() > 0)
        
        # Determine direction
        if hh_count > lh_count and hl_count > ll_count:
            direction = 'BULLISH'
            strength = min(100, (hh_count / len(highs) * 100))
        elif lh_count > hh_count and ll_count > hl_count:
            direction = 'BEARISH'
            strength = min(100, (ll_count / len(lows) * 100))
        else:
            direction = 'RANGING'
            strength = 50
        
        return {
            'direction': direction,
            'strength': strength,
            'momentum': momentum
        }
    
    def identify_support_resistance(self, df: pd.DataFrame) -> Dict:
        """
        Identify key support and resistance levels
        
        Returns:
            {
                'resistance': [price levels],
                'support': [price levels],
                'nearest_resistance': float,
                'nearest_support': float
            }
        """
        recent = df.tail(100)
        current_price = recent['close'].iloc[-1]
        
        # Find local maxima (resistance)
        resistance_levels = []
        for i in range(5, len(recent) - 5):
            if recent['high'].iloc[i] == recent['high'].iloc[i-5:i+5].max():
                resistance_levels.append(recent['high'].iloc[i])
        
        # Find local minima (support)
        support_levels = []
        for i in range(5, len(recent) - 5):
            if recent['low'].iloc[i] == recent['low'].iloc[i-5:i+5].min():
                support_levels.append(recent['low'].iloc[i])
        
        # Filter to significant levels (touched multiple times)
        resistance = self._cluster_levels(resistance_levels)
        support = self._cluster_levels(support_levels)
        
        # Find nearest levels
        resistance_above = [r for r in resistance if r > current_price]
        support_below = [s for s in support if s < current_price]
        
        nearest_resistance = min(resistance_above) if resistance_above else current_price * 1.02
        nearest_support = max(support_below) if support_below else current_price * 0.98
        
        return {
            'resistance': resistance,
            'support': support,
            'nearest_resistance': nearest_resistance,
            'nearest_support': nearest_support
        }
    
    def predict_reversal_zone(self, df: pd.DataFrame, direction: str) -> Tuple[float, float]:
        """
        Predict potential reversal zone based on trend exhaustion
        
        Returns:
            (reversal_price, confidence)
        """
        levels = self.identify_support_resistance(df)
        current_price = df['close'].iloc[-1]
        
        if direction == 'BULLISH':
            # Price likely to reverse at resistance
            reversal_price = levels['nearest_resistance']
            # Check distance to resistance
            distance = (reversal_price - current_price) / current_price * 100
            confidence = min(100, max(0, 100 - distance * 10))
        elif direction == 'BEARISH':
            # Price likely to reverse at support
            reversal_price = levels['nearest_support']
            distance = (current_price - reversal_price) / current_price * 100
            confidence = min(100, max(0, 100 - distance * 10))
        else:
            reversal_price = current_price
            confidence = 50
        
        return reversal_price, confidence
    
    def predict_targets(self, df: pd.DataFrame, direction: str) -> Dict:
        """
        Predict target high and low for next N candles
        
        Returns:
            {
                'target_high': float,
                'target_low': float,
                'confidence': float
            }
        """
        levels = self.identify_support_resistance(df)
        trend = self.analyze_trend(df)
        current_price = df['close'].iloc[-1]
        
        # Calculate ATR for volatility
        atr = self._calculate_atr(df, period=14)
        
        if direction == 'BULLISH':
            target_high = levels['nearest_resistance']
            target_low = current_price - atr * 0.5
        elif direction == 'BEARISH':
            target_high = current_price + atr * 0.5
            target_low = levels['nearest_support']
        else:  # RANGING
            target_high = current_price + atr
            target_low = current_price - atr
        
        confidence = trend['strength']
        
        return {
            'target_high': target_high,
            'target_low': target_low,
            'confidence': confidence
        }
    
    def _cluster_levels(self, levels: List[float], threshold: float = 0.001) -> List[float]:
        """Group nearby price levels into clusters"""
        if not levels:
            return []
        
        levels = sorted(levels)
        clusters = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if (level - current_cluster[-1]) / current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [level]
        
        clusters.append(np.mean(current_cluster))
        return clusters
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else 0
