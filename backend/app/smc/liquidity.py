"""
Liquidity Zone Detection

Liquidity zones are areas where stop losses cluster, typically at swing highs/lows.
Smart money targets these zones to "sweep liquidity" before reversing.

Types:
- Buy-Side Liquidity (BSL): Above swing highs (stop losses of shorts)
- Sell-Side Liquidity (SSL): Below swing lows (stop losses of longs)
"""
from typing import List, Dict
import pandas as pd
import numpy as np


class LiquidityDetector:
    """Detect liquidity zones at swing points"""
    
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

    def detect_session_liquidity(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect Session Highs/Lows (Morning: 6-10, Afternoon: 13-16)
        Assumes df index is datetime.
        """
        liquidity_zones = []
        
        # Ensure index is datetime
        if not pd.api.types.is_datetime64_any_dtype(df.index):
            return []
            
        # Group by day
        days = df.groupby(df.index.date)
        
        for date, day_df in days:
            # Morning Session (06:00 - 10:00)
            morning_df = day_df.between_time('06:00', '10:00')
            if not morning_df.empty:
                # Morning High
                m_high_idx = morning_df['high'].idxmax()
                m_high = morning_df['high'].max()
                liquidity_zones.append({
                    'type': 'buy_side',
                    'subtype': 'session_high',
                    'session': 'morning',
                    'price': m_high,
                    'timestamp': m_high_idx,
                    'index': df.index.get_loc(m_high_idx),
                    'swept': False
                })
                # Morning Low
                m_low_idx = morning_df['low'].idxmin()
                m_low = morning_df['low'].min()
                liquidity_zones.append({
                    'type': 'sell_side',
                    'subtype': 'session_low',
                    'session': 'morning',
                    'price': m_low,
                    'timestamp': m_low_idx,
                    'index': df.index.get_loc(m_low_idx),
                    'swept': False
                })
                
            # Afternoon Session (13:00 - 16:00)
            afternoon_df = day_df.between_time('13:00', '16:00')
            if not afternoon_df.empty:
                # Afternoon High
                a_high_idx = afternoon_df['high'].idxmax()
                a_high = afternoon_df['high'].max()
                liquidity_zones.append({
                    'type': 'buy_side',
                    'subtype': 'session_high',
                    'session': 'afternoon',
                    'price': a_high,
                    'timestamp': a_high_idx,
                    'index': df.index.get_loc(a_high_idx),
                    'swept': False
                })
                # Afternoon Low
                a_low_idx = afternoon_df['low'].idxmin()
                a_low = afternoon_df['low'].min()
                liquidity_zones.append({
                    'type': 'sell_side',
                    'subtype': 'session_low',
                    'session': 'afternoon',
                    'price': a_low,
                    'timestamp': a_low_idx,
                    'index': df.index.get_loc(a_low_idx),
                    'swept': False
                })
                
        return liquidity_zones

    def detect_equal_highs_lows(
        self, 
        df: pd.DataFrame, 
        swing_highs: List[int], 
        swing_lows: List[int],
        atr: pd.Series
    ) -> List[Dict]:
        """
        Detect Equal Highs (EQH) and Equal Lows (EQL)
        Logic: Two swings within threshold (0.1 * ATR)
        """
        eq_zones = []
        threshold_multiplier = 0.1
        
        # Check Equal Highs
        sorted_highs = sorted(swing_highs)
        for i in range(len(sorted_highs) - 1):
            idx1 = sorted_highs[i]
            # Look at next few swings to find a match
            for j in range(i + 1, min(i + 5, len(sorted_highs))):
                idx2 = sorted_highs[j]
                
                price1 = df['high'].iloc[idx1]
                price2 = df['high'].iloc[idx2]
                
                # Use ATR from the later candle
                current_atr = atr.iloc[idx2] if not np.isnan(atr.iloc[idx2]) else 0
                threshold = current_atr * threshold_multiplier if current_atr > 0 else 0.0001
                
                if abs(price1 - price2) <= threshold:
                    eq_zones.append({
                        'type': 'buy_side',
                        'subtype': 'eqh',
                        'price': max(price1, price2), # Use the higher one or avg
                        'timestamp': df.index[idx2],
                        'index': idx2,
                        'swept': False,
                        'related_indices': [idx1, idx2]
                    })
        
        # Check Equal Lows
        sorted_lows = sorted(swing_lows)
        for i in range(len(sorted_lows) - 1):
            idx1 = sorted_lows[i]
            # Look at next few swings
            for j in range(i + 1, min(i + 5, len(sorted_lows))):
                idx2 = sorted_lows[j]
                
                price1 = df['low'].iloc[idx1]
                price2 = df['low'].iloc[idx2]
                
                current_atr = atr.iloc[idx2] if not np.isnan(atr.iloc[idx2]) else 0
                threshold = current_atr * threshold_multiplier if current_atr > 0 else 0.0001
                
                if abs(price1 - price2) <= threshold:
                    eq_zones.append({
                        'type': 'sell_side',
                        'subtype': 'eql',
                        'price': min(price1, price2),
                        'timestamp': df.index[idx2],
                        'index': idx2,
                        'swept': False,
                        'related_indices': [idx1, idx2]
                    })
                    
        return eq_zones

    def detect_liquidity_zones(
        self, 
        df: pd.DataFrame,
        swing_highs: List[int],
        swing_lows: List[int]
    ) -> List[Dict]:
        """
        Detect liquidity zones (Swings, Sessions, EQH/EQL)
        """
        liquidity_zones = []
        
        # 1. Swing Highs/Lows (Standard)
        for idx in swing_highs:
            liquidity_zones.append({
                'type': 'buy_side',
                'subtype': 'swing_high',
                'price': df['high'].iloc[idx],
                'timestamp': df.index[idx],
                'index': idx,
                'swept': False
            })
        
        for idx in swing_lows:
            liquidity_zones.append({
                'type': 'sell_side',
                'subtype': 'swing_low',
                'price': df['low'].iloc[idx],
                'timestamp': df.index[idx],
                'index': idx,
                'swept': False
            })
            
        # 2. Session Liquidity
        session_zones = self.detect_session_liquidity(df)
        liquidity_zones.extend(session_zones)
        
        # 3. Equal Highs/Lows
        atr = self._calculate_atr(df)
        eq_zones = self.detect_equal_highs_lows(df, swing_highs, swing_lows, atr)
        liquidity_zones.extend(eq_zones)
        
        # Check if liquidity was swept
        # Sort by index to optimize? No need for now.
        
        for liq in liquidity_zones:
            # Check all candles after the liquidity zone formation
            for i in range(liq['index'] + 1, len(df)):
                candle = df.iloc[i]
                
                if liq['type'] == 'buy_side':
                    # Swept if price went above the high
                    if candle['high'] > liq['price']:
                        liq['swept'] = True
                        break
                else:  # sell_side
                    # Swept if price went below the low
                    if candle['low'] < liq['price']:
                        liq['swept'] = True
                        break
        
        return liquidity_zones
