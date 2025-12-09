"""
Liquidity Zone Detection

Liquidity zones are areas where stop losses cluster, typically at swing highs/lows.
Smart money targets these zones to "sweep liquidity" before reversing.

Types:
- Buy-Side Liquidity (BSL): Above swing highs (stop losses of shorts)
- Sell-Side Liquidity (SSL): Below swing lows (stop losses of longs)
"""
from typing import List, Dict, Literal
import pandas as pd
import numpy as np
from app.models.smc import SwingPoint, LiquidityZone # Import SwingPoint and LiquidityZone models


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
        atr = tr.ewm(span=period, adjust=False).mean() # Use EMA for ATR as in Pine Script
        return atr

    def detect_session_liquidity(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """
        Detect Session Highs/Lows (Morning: 6-10, Afternoon: 13-16 UTC+1)
        Assumes df index is datetime and already in Europe/Bratislava timezone.
        """
        liquidity_zones: List[LiquidityZone] = []
        
        if not pd.api.types.is_datetime64_any_dtype(df.index) or df.empty:
            return []
            
        # Group by day (date part of the timezone-aware index)
        days = df.groupby(df.index.date)
        
        for date, day_df in days:
            # Morning Session (06:00 - 10:00 UTC+1)
            # Pandas between_time is inclusive of start and end by default.
            # If 'include_end' is not supported, we rely on default or adjust.
            # Given the error, we remove include_end.
            morning_df = day_df.between_time('06:00', '10:00')
            if not morning_df.empty:
                # Morning High
                m_high_idx = morning_df['high'].idxmax()
                m_high = morning_df['high'].max()
                liquidity_zones.append(LiquidityZone(
                    type='buy_side',
                    subtype='session_high',
                    session='morning',
                    price=m_high,
                    timestamp=m_high_idx,
                    index=df.index.get_loc(m_high_idx),
                    swept=False
                ))
                # Morning Low
                m_low_idx = morning_df['low'].idxmin()
                m_low = morning_df['low'].min()
                liquidity_zones.append(LiquidityZone(
                    type='sell_side',
                    subtype='session_low',
                    session='morning',
                    price=m_low,
                    timestamp=m_low_idx,
                    index=df.index.get_loc(m_low_idx),
                    swept=False
                ))
                
            # Afternoon Session (13:00 - 16:00 UTC+1)
            afternoon_df = day_df.between_time('13:00', '16:00')
            if not afternoon_df.empty:
                # Afternoon High
                a_high_idx = afternoon_df['high'].idxmax()
                a_high = afternoon_df['high'].max()
                liquidity_zones.append(LiquidityZone(
                    type='buy_side',
                    subtype='session_high',
                    session='afternoon',
                    price=a_high,
                    timestamp=a_high_idx,
                    index=df.index.get_loc(a_high_idx),
                    swept=False
                ))
                # Afternoon Low
                a_low_idx = afternoon_df['low'].idxmin()
                a_low = afternoon_df['low'].min()
                liquidity_zones.append(LiquidityZone(
                    type='sell_side',
                    subtype='session_low',
                    session='afternoon',
                    price=a_low,
                    timestamp=a_low_idx,
                    index=df.index.get_loc(a_low_idx),
                    swept=False
                ))
                
        return liquidity_zones

    def detect_equal_highs_lows(
        self, 
        df: pd.DataFrame, 
        swing_highs: List[SwingPoint], 
        swing_lows: List[SwingPoint],
        atr_series: pd.Series, # Renamed to avoid conflict with method name
        threshold_multiplier: float = 0.1 # From Pine Script's equalHighsLowsThresholdInput
    ) -> List[LiquidityZone]:
        """
        Detect Equal Highs (EQH) and Equal Lows (EQL)
        Logic: Two swings within a dynamic threshold (threshold_multiplier * ATR)
        """
        eq_zones: List[LiquidityZone] = []
        
        # Check Equal Highs
        # Sort by index to ensure chronological processing
        sorted_highs = sorted(swing_highs, key=lambda x: x.index)
        for i in range(len(sorted_highs) - 1):
            sh1 = sorted_highs[i]
            # Look at next few swings to find a match (Pine uses up to 5, let's use a similar window)
            for j in range(i + 1, min(i + 5, len(sorted_highs))):
                sh2 = sorted_highs[j]
                
                price1 = sh1.price
                price2 = sh2.price
                
                # Use ATR from the later swing point
                current_atr = atr_series.iloc[sh2.index] if sh2.index < len(atr_series) and not np.isnan(atr_series.iloc[sh2.index]) else 0
                threshold = current_atr * threshold_multiplier if current_atr > 0 else 0.0001 # Default small threshold
                
                if abs(price1 - price2) <= threshold:
                    eq_zones.append(LiquidityZone(
                        type='buy_side',
                        subtype='eqh',
                        price=(price1 + price2) / 2, # Use average price for the zone
                        timestamp=sh2.timestamp,
                        index=sh2.index,
                        swept=False,
                        related_indices=[sh1.index, sh2.index]
                    ))
        
        # Check Equal Lows
        sorted_lows = sorted(swing_lows, key=lambda x: x.index)
        for i in range(len(sorted_lows) - 1):
            sl1 = sorted_lows[i]
            # Look at next few swings
            for j in range(i + 1, min(i + 5, len(sorted_lows))):
                sl2 = sorted_lows[j]
                
                price1 = sl1.price
                price2 = sl2.price
                
                current_atr = atr_series.iloc[sl2.index] if sl2.index < len(atr_series) and not np.isnan(atr_series.iloc[sl2.index]) else 0
                threshold = current_atr * threshold_multiplier if current_atr > 0 else 0.0001
                
                if abs(price1 - price2) <= threshold:
                    eq_zones.append(LiquidityZone(
                        type='sell_side',
                        subtype='eql',
                        price=(price1 + price2) / 2, # Use average price for the zone
                        timestamp=sl2.timestamp,
                        index=sl2.index,
                        swept=False,
                        related_indices=[sl1.index, sl2.index]
                    ))
                    
        return eq_zones

    def detect_liquidity_sweeps(
        self,
        df: pd.DataFrame,
        liquidity_zones: List[LiquidityZone],
        sweep_threshold_multiplier: float = 0.5 # From Pine Script's sweepThresholdInput
    ) -> List[LiquidityZone]:
        """
        Detects liquidity sweeps (wick-through-and-reject logic) for existing liquidity zones.
        Updates the 'swept' status of the LiquidityZone objects.
        """
        if df.empty or not liquidity_zones:
            return liquidity_zones

        atr_series = self._calculate_atr(df, period=14) # Pine uses ta.atr(14) for atrVal

        for liq_zone in liquidity_zones:
            if liq_zone.swept: # Already swept
                continue

            # Check all candles after the liquidity zone formation
            for i in range(liq_zone.index + 1, len(df)):
                candle_high = df['high'].iloc[i]
                candle_low = df['low'].iloc[i]
                candle_close = df['close'].iloc[i]
                
                current_atr = atr_series.iloc[i] if i < len(atr_series) and not np.isnan(atr_series.iloc[i]) else 0
                sweep_dist = current_atr * sweep_threshold_multiplier

                if liq_zone.type == 'buy_side': # Looking for sweep above price (BSL)
                    # Bullish sweep: wick above level, close back below
                    if candle_high > liq_zone.price and candle_high > liq_zone.price + sweep_dist and candle_close < liq_zone.price:
                        liq_zone.swept = True
                        liq_zone.sweep_time = df.index[i] # Add sweep time for context
                        break
                elif liq_zone.type == 'sell_side': # Looking for sweep below price (SSL)
                    # Bearish sweep: wick below level, close back above
                    if candle_low < liq_zone.price and candle_low < liq_zone.price - sweep_dist and candle_close > liq_zone.price:
                        liq_zone.swept = True
                        liq_zone.sweep_time = df.index[i] # Add sweep time for context
                        break
        return liquidity_zones


    def detect_liquidity_zones(
        self, 
        df: pd.DataFrame,
        swing_highs: List[SwingPoint], # Now takes SwingPoint objects
        swing_lows: List[SwingPoint],  # Now takes SwingPoint objects
        sweep_threshold_multiplier: float = 0.5,
        eqh_eql_threshold_multiplier: float = 0.1
    ) -> List[LiquidityZone]:
        """
        Detect liquidity zones (Swings, Sessions, EQH/EQL) and their sweep status.
        """
        all_liquidity_zones: List[LiquidityZone] = []
        
        # Calculate ATR once for efficiency
        atr_series = self._calculate_atr(df)

        # 1. Swing Highs/Lows (Standard)
        for sp in swing_highs:
            all_liquidity_zones.append(LiquidityZone(
                type='buy_side',
                subtype='swing_high',
                price=sp.price,
                timestamp=sp.timestamp,
                index=sp.index,
                swept=False
            ))
        
        for sp in swing_lows:
            all_liquidity_zones.append(LiquidityZone(
                type='sell_side',
                subtype='swing_low',
                price=sp.price,
                timestamp=sp.timestamp,
                index=sp.index,
                swept=False
            ))
            
        # 2. Session Liquidity
        session_zones = self.detect_session_liquidity(df)
        all_liquidity_zones.extend(session_zones)
        
        # 3. Equal Highs/Lows
        eq_zones = self.detect_equal_highs_lows(df, swing_highs, swing_lows, atr_series, eqh_eql_threshold_multiplier)
        all_liquidity_zones.extend(eq_zones)
        
        # 4. Detect sweeps for all identified liquidity zones
        all_liquidity_zones = self.detect_liquidity_sweeps(df, all_liquidity_zones, sweep_threshold_multiplier)
        
        return all_liquidity_zones
