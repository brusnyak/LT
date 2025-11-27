"""
Order Block Detection Algorithm

Order blocks are institutional supply/demand zones where smart money entered positions.

Detection Criteria:
1. A candle must sweep previous liquidity (swing high or swing low)
2. The candle that swept liquidity must become a pivot point (swing reversal)
3. The OB zone is defined by the candle's high/low/mid

Types:
- Bullish OB: Bearish candle that swept sell-side liquidity (SSL) and then price reversed up
- Bearish OB: Bullish candle that swept buy-side liquidity (BSL) and then price reversed down
"""
from typing import List, Dict, Optional
import pandas as pd
import numpy as np


class OrderBlockDetector:
    """
    Detect order blocks based on liquidity sweeps and pivot formation
    
    An order block is valid when:
    1. Price sweeps a previous swing high/low (liquidity grab)
    2. The candle that swept becomes a swing point itself (reversal)
    3. The zone hasn't been fully mitigated
    """
    
    def __init__(self, lookback_window: int = 30):
        """
        Initialize order block detector
        
        Args:
            lookback_window: How many candles to look back for liquidity sweeps
                            30 for M30, 200+ for M5 as per user specs
        """
        self.lookback_window = lookback_window
    
    def detect_liquidity_sweeps(
        self, 
        df: pd.DataFrame, 
        swing_highs: List[int], 
        swing_lows: List[int]
    ) -> Dict[int, Dict]:
        """
        Detect where price swept previous swing highs/lows
        
        Args:
            df: OHLCV dataframe
            swing_highs: Indices of swing high points
            swing_lows: Indices of swing low points
            
        Returns:
            Dictionary mapping candle index to sweep information
        """
        sweeps = {}
        
        # Convert swing lists to sets for faster lookup
        swing_high_set = set(swing_highs)
        swing_low_set = set(swing_lows)
        
        for i in range(len(df)):
            current_high = df['high'].iloc[i]
            current_low = df['low'].iloc[i]
            
            # Look back for liquidity to sweep
            lookback_start = max(0, i - self.lookback_window)
            
            # Check for buy-side liquidity sweep (swept a swing high)
            for sh_idx in swing_highs:
                if lookback_start <= sh_idx < i:
                    swing_high_price = df['high'].iloc[sh_idx]
                    
                    # Current candle's high swept the previous swing high
                    if current_high > swing_high_price:
                        if i not in sweeps:
                            sweeps[i] = {'bsl_swept': [], 'ssl_swept': []}
                        sweeps[i]['bsl_swept'].append({
                            'swing_idx': sh_idx,
                            'swing_price': swing_high_price,
                            'sweep_price': current_high
                        })
            
            # Check for sell-side liquidity sweep (swept a swing low)
            for sl_idx in swing_lows:
                if lookback_start <= sl_idx < i:
                    swing_low_price = df['low'].iloc[sl_idx]
                    
                    # Current candle's low swept the previous swing low
                    if current_low < swing_low_price:
                        if i not in sweeps:
                            sweeps[i] = {'bsl_swept': [], 'ssl_swept': []}
                        sweeps[i]['ssl_swept'].append({
                            'swing_idx': sl_idx,
                            'swing_price': swing_low_price,
                            'sweep_price': current_low
                        })
        
        return sweeps
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def detect_order_blocks(
        self, 
        df: pd.DataFrame, 
        structure_events: List[Dict]
    ) -> List[Dict]:
        """
        Detect order blocks based on market structure breaks (BOS/CHOCH).
        The OB is placed at the origin of the impulse leg that caused the break.
        
        Args:
            df: OHLCV dataframe
            structure_events: List of BOS/CHOCH events from MarketStructureDetector
            
        Returns:
            List of order block dictionaries
        """
        order_blocks = []
        existing_indices = set()
        
        # Calculate ATR for volatility filter (using 200 period as per Pine default)
        atr = self._calculate_atr(df, period=200)
        
        for event in structure_events:
            origin_idx = event.get('impulse_origin_index')
            if origin_idx is None:
                continue
            
            # Deduplication: Don't create multiple OBs at the same candle
            if origin_idx in existing_indices:
                continue
                
            # Volatility Filter:
            # Pine: highVolatilityBar = (high - low) >= (2 * volatilityMeasure)
            # We'll use a slightly looser filter: Range >= 1.0 * ATR to capture more candidates,
            # or stick to Pine's 2.0 if strictness is desired. Let's use 1.5 for balance.
            candle_range = df['high'].iloc[origin_idx] - df['low'].iloc[origin_idx]
            threshold = atr.iloc[origin_idx] if not np.isnan(atr.iloc[origin_idx]) else 0
            
            # If ATR is NaN (start of data), skip filter or accept. Let's accept.
            if threshold > 0 and candle_range < (1.0 * threshold):
                continue
                
            # Bullish Structure Break (BOS/CHOCH Up) -> Bullish OB at Origin (Swing Low)
            if event['direction'] == 'bullish':
                # The origin is a Swing Low. 
                
                ob = {
                    'type': 'bullish',
                    'candle_index': origin_idx,
                    'timestamp': df.index[origin_idx],
                    'high': df['high'].iloc[origin_idx],
                    'low': df['low'].iloc[origin_idx],
                    'open': df['open'].iloc[origin_idx],
                    'close': df['close'].iloc[origin_idx],
                    'mid': (df['high'].iloc[origin_idx] + df['low'].iloc[origin_idx]) / 2,
                    'state': 'active',
                    'mitigation_level': 0, # 0=None, 1=25%, 2=50%, 3=75%, 4=Full
                    'structure_event': event['type'], # BOS or CHOCH
                    'structure_time': event['timestamp'],
                    'volatility_score': candle_range / threshold if threshold > 0 else 1.0
                }
                order_blocks.append(ob)
                existing_indices.add(origin_idx)
                
            # Bearish Structure Break (BOS/CHOCH Down) -> Bearish OB at Origin (Swing High)
            elif event['direction'] == 'bearish':
                # The origin is a Swing High.
                
                ob = {
                    'type': 'bearish',
                    'candle_index': origin_idx,
                    'timestamp': df.index[origin_idx],
                    'high': df['high'].iloc[origin_idx],
                    'low': df['low'].iloc[origin_idx],
                    'open': df['open'].iloc[origin_idx],
                    'close': df['close'].iloc[origin_idx],
                    'mid': (df['high'].iloc[origin_idx] + df['low'].iloc[origin_idx]) / 2,
                    'state': 'active',
                    'mitigation_level': 0,
                    'structure_event': event['type'],
                    'structure_time': event['timestamp'],
                    'volatility_score': candle_range / threshold if threshold > 0 else 1.0
                }
                order_blocks.append(ob)
                existing_indices.add(origin_idx)
        
        return order_blocks
    
    def update_ob_states(self, df: pd.DataFrame, order_blocks: List[Dict]) -> List[Dict]:
        """
        Update order block states based on price interaction.
        Tracks multi-level mitigation (25%, 50%, 75%, Full).
        Handles Breaker Blocks (flipping polarity on full mitigation).
        """
        for ob in order_blocks:
            ob_idx = ob['candle_index']
            ob_high = ob['high']
            ob_low = ob['low']
            ob_range = ob_high - ob_low
            
            if ob_range == 0:
                continue
                
            # Check all candles after the OB formation
            for i in range(ob_idx + 1, len(df)):
                candle_high = df['high'].iloc[i]
                candle_low = df['low'].iloc[i]
                
                # Skip if already fully mitigated/breaker (unless we want to track breaker mitigation too)
                if ob.get('mitigation_level', 0) >= 4:
                    break
                
                if ob['type'] == 'bullish':
                    # Bullish OB: Price comes DOWN into it
                    if candle_low <= ob_high:
                        if ob['state'] == 'active':
                            ob['state'] = 'touched'
                        
                        # Calculate penetration depth
                        penetration = ob_high - candle_low
                        fill_percent = penetration / ob_range
                        
                        # Update mitigation level
                        if fill_percent >= 1.0:
                            ob['mitigation_level'] = 4
                            ob['state'] = 'mitigated'
                            
                            # BREAKER BLOCK LOGIC
                            # Bullish OB broken -> Becomes Bearish Breaker
                            ob['is_breaker'] = True
                            ob['original_type'] = 'bullish'
                            ob['type'] = 'bearish' # Flip polarity
                            ob['breaker_time'] = df.index[i]
                            
                        elif fill_percent >= 0.75:
                            ob['mitigation_level'] = max(ob['mitigation_level'], 3)
                        elif fill_percent >= 0.50:
                            ob['mitigation_level'] = max(ob['mitigation_level'], 2)
                        elif fill_percent >= 0.25:
                            ob['mitigation_level'] = max(ob['mitigation_level'], 1)
                            
                        if ob['state'] == 'mitigated':
                            break
                
                elif ob['type'] == 'bearish':
                    # Bearish OB: Price comes UP into it
                    if candle_high >= ob_low:
                        if ob['state'] == 'active':
                            ob['state'] = 'touched'
                            
                        # Calculate penetration depth
                        penetration = candle_high - ob_low
                        fill_percent = penetration / ob_range
                        
                        # Update mitigation level
                        if fill_percent >= 1.0:
                            ob['mitigation_level'] = 4
                            ob['state'] = 'mitigated'
                            
                            # BREAKER BLOCK LOGIC
                            # Bearish OB broken -> Becomes Bullish Breaker
                            ob['is_breaker'] = True
                            ob['original_type'] = 'bearish'
                            ob['type'] = 'bullish' # Flip polarity
                            ob['breaker_time'] = df.index[i]
                            
                        elif fill_percent >= 0.75:
                            ob['mitigation_level'] = max(ob['mitigation_level'], 3)
                        elif fill_percent >= 0.50:
                            ob['mitigation_level'] = max(ob['mitigation_level'], 2)
                        elif fill_percent >= 0.25:
                            ob['mitigation_level'] = max(ob['mitigation_level'], 1)
                            
                        if ob['state'] == 'mitigated':
                            break
        
        return order_blocks


def get_ob_lookback_window(timeframe: str) -> int:
    """
    Get optimal lookback window for OB detection per timeframe
    
    Args:
        timeframe: Timeframe string
        
    Returns:
        Lookback window in candles
    """
    lookback_config = {
        'M1': 100,
        'M5': 200,   # User specified 200+ for M5
        'M15': 100,
        'M30': 50,   # User specified 50 for M30
        'H1': 30,
        'H4': 20,
        'D1': 15,
    }
    
    return lookback_config.get(timeframe, 50)
