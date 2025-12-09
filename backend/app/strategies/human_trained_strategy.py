"""
Human-Trained Strategy
Replicates manual trading decisions using SMC methodology
Based on analysis of 71 manual trades with 4.51 avg R:R
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app.strategies.base import BaseStrategy


class HumanTrainedStrategy(BaseStrategy):
    """
    Strategy that mimics human trading decisions
    Pattern: Structure (H4) → Shift (M15) → POI (M5) → Entry
    """
    
    def __init__(self):
        super().__init__(
            "Human-Trained Strategy",
            "Strategy that replicates manual trading decisions using SMC methodology"
        )
        
        # Manual trade statistics (from analysis)
        self.target_rr = 4.5  # Average R:R from manual trades
        self.avg_sl_pips = 6.4
        self.avg_tp_pips = 24.0
        
        # Timeframes
        self.structure_tf = 'H4'
        self.shift_tf = 'M15'
        self.entry_tf = 'M5'
    
    def get_config_schema(self) -> Dict:
        """Return configuration schema for the strategy"""
        return {
            'target_rr': {
                'type': 'float',
                'default': 4.5,
                'description': 'Target risk:reward ratio'
            },
            'avg_sl_pips': {
                'type': 'float',
                'default': 6.4,
                'description': 'Average stop loss in pips'
            },
            'avg_tp_pips': {
                'type': 'float',
                'default': 24.0,
                'description': 'Average take profit in pips'
            }
        }
        
    def analyze(self, symbol: str, timeframe: str = 'M15') -> Dict:
        """
        Main analysis method
        Returns trading signals based on SMC methodology
        """
        try:
            # For now, return basic structure
            # Full implementation will follow
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'bias': 'neutral',
                'signals': [],
                'structure': {},
                'shift': {},
                'poi': [],
                'liquidity': []
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size based on symbol"""
        if 'JPY' in symbol:
            return 0.01
        elif 'XAU' in symbol or 'GOLD' in symbol:
            # Gold: Standard pip is 0.1 (e.g. 2000.00 -> 2000.10)
            return 0.1
        else:
            return 0.0001

    def _get_sl_tp_pips(self, symbol: str) -> Tuple[float, float]:
        """Get SL and TP pips based on symbol volatility"""
        if 'XAU' in symbol or 'GOLD' in symbol:
            # Gold needs wider stops. 
            # Manual stats: ~30 pips ($3.00) SL, ~120 pips ($12.00) TP
            return 30.0, 120.0
        else:
            # Forex default (from manual analysis)
            return self.avg_sl_pips, self.avg_tp_pips

    def identify_premium_discount(self, df_h4: pd.DataFrame, structure: Dict) -> Dict:
        """
        Identify Premium and Discount zones based on H4 range
        """
        if not structure.get('swings'):
            return {'status': 'neutral'}
            
        last_high = structure.get('last_high')
        last_low = structure.get('last_low')
        
        if not last_high or not last_low:
            return {'status': 'neutral'}
            
        # Calculate 50% equilibrium
        equilibrium = (last_high + last_low) / 2
        
        return {
            'premium_zone': [equilibrium, last_high],
            'discount_zone': [last_low, equilibrium],
            'equilibrium': equilibrium,
            'range_high': last_high,
            'range_low': last_low
        }
    
    def identify_structure(self, df_h4: pd.DataFrame) -> Dict:
        """
        Identify market structure on H4
        Returns: trend direction, swing highs/lows
        """
        if df_h4 is None or len(df_h4) < 50:
            return {'trend': 'neutral', 'swings': []}
        
        # Find swing highs and lows (local extrema)
        swing_highs = []
        swing_lows = []
        lookback = 5  # Look 5 candles left and right
        
        for i in range(lookback, len(df_h4) - lookback):
            # Swing high: highest point in window
            is_swing_high = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and df_h4['high'].iloc[j] >= df_h4['high'].iloc[i]:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    'index': i,
                    'price': df_h4['high'].iloc[i],
                    'time': df_h4['time'].iloc[i] if 'time' in df_h4.columns else i
                })
            
            # Swing low: lowest point in window
            is_swing_low = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and df_h4['low'].iloc[j] <= df_h4['low'].iloc[i]:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    'index': i,
                    'price': df_h4['low'].iloc[i],
                    'time': df_h4['time'].iloc[i] if 'time' in df_h4.columns else i
                })
        
        # Determine trend based on recent swings
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {'trend': 'neutral', 'swings': {'highs': swing_highs, 'lows': swing_lows}}
        
        # Get last 5 swing highs and lows for better trend detection
        recent_highs = swing_highs[-5:] if len(swing_highs) >= 5 else swing_highs
        recent_lows = swing_lows[-5:] if len(swing_lows) >= 5 else swing_lows
        
        # Instead of requiring perfect HH/HL, check overall bias
        # Compare most recent swings to older swings
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            # Bullish: Recent highs/lows are generally higher than older ones
            recent_high_avg = sum(h['price'] for h in recent_highs[-2:]) / 2
            older_high_avg = sum(h['price'] for h in recent_highs[:2]) / 2
            
            recent_low_avg = sum(l['price'] for l in recent_lows[-2:]) / 2
            older_low_avg = sum(l['price'] for l in recent_lows[:2]) / 2
            
            # Calculate bias strength
            high_bias = (recent_high_avg - older_high_avg) / older_high_avg if older_high_avg > 0 else 0
            low_bias = (recent_low_avg - older_low_avg) / older_low_avg if older_low_avg > 0 else 0
            
            # Threshold for trend detection (0.2% move - relaxed for better signal generation)
            threshold = 0.002
            
            # print(f"DEBUG Structure: high_bias={high_bias:.4f}, low_bias={low_bias:.4f}, threshold={threshold}")
            
            if high_bias > threshold and low_bias > threshold:
                trend = 'bullish'
            elif high_bias < -threshold and low_bias < -threshold:
                trend = 'bearish'
            else:
                trend = 'ranging'
        else:
            trend = 'ranging'
        
        return {
            'trend': trend,
            'swings': {
                'highs': swing_highs,
                'lows': swing_lows
            },
            'last_high': swing_highs[-1]['price'] if swing_highs else None,
            'last_low': swing_lows[-1]['price'] if swing_lows else None,
        }
    
    def detect_shift(self, df_m15: pd.DataFrame, structure: Dict) -> Dict:
        """
        Detect Break of Structure (BOS) or Change of Character (ChoCh) on M15
        Now detects M15-level breaks instead of H4 breaks for more signals
        """
        if df_m15 is None or len(df_m15) < 50:
            return {'shift_detected': False}
        
        trend = structure.get('trend', 'neutral')
        
        if trend == 'neutral' or trend == 'ranging':
            return {'shift_detected': False}
        
        # Find M15 swing highs and lows (last 100 candles for recent context)
        lookback_window = min(100, len(df_m15) - 10)
        recent_m15 = df_m15.iloc[-lookback_window:]
        
        m15_swing_highs = []
        m15_swing_lows = []
        lookback = 3  # Smaller lookback for M15 (more sensitive)
        
        for i in range(lookback, len(recent_m15) - lookback):
            # Swing high
            is_swing_high = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and recent_m15['high'].iloc[j] >= recent_m15['high'].iloc[i]:
                    is_swing_high = False
                    break
            if is_swing_high:
                m15_swing_highs.append({
                    'index': i,
                    'price': recent_m15['high'].iloc[i]
                })
            
            # Swing low
            is_swing_low = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and recent_m15['low'].iloc[j] <= recent_m15['low'].iloc[i]:
                    is_swing_low = False
                    break
            if is_swing_low:
                m15_swing_lows.append({
                    'index': i,
                    'price': recent_m15['low'].iloc[i]
                })
        
        if not m15_swing_highs or not m15_swing_lows:
            # print(f"DEBUG Shift: No M15 swings found (highs={len(m15_swing_highs)}, lows={len(m15_swing_lows)})")
            return {'shift_detected': False}
        
        # Get current price
        current_price = df_m15['close'].iloc[-1]
        
        # print(f"DEBUG Shift: Found {len(m15_swing_highs)} M15 highs, {len(m15_swing_lows)} M15 lows")
        
        # For bullish H4 trend: Look for M15 BOS up (break above recent M15 swing high)
        if trend == 'bullish':
            last_m15_high = m15_swing_highs[-1]['price'] if m15_swing_highs else None
            # print(f"DEBUG Shift: Bullish, last_m15_high={last_m15_high}, current={current_price}")
            if last_m15_high and current_price > last_m15_high:
                return {
                    'shift_detected': True,
                    'type': 'BOS_UP',
                    'level': last_m15_high,
                    'break_candle_index': len(df_m15) - 1
                }
        
        # For bearish H4 trend: Look for M15 BOS down (break below recent M15 swing low)
        elif trend == 'bearish':
            last_m15_low = m15_swing_lows[-1]['price'] if m15_swing_lows else None
            # print(f"DEBUG Shift: Bearish, last_m15_low={last_m15_low}, current={current_price}")
            if last_m15_low and current_price < last_m15_low:
                return {
                    'shift_detected': True,
                    'type': 'BOS_DOWN',
                    'level': last_m15_low,
                    'break_candle_index': len(df_m15) - 1
                }
        
        return {'shift_detected': False}
    
    def identify_poi(self, df_m5: pd.DataFrame, shift: Dict) -> List[Dict]:
        """
        Identify Points of Interest (Order Blocks + Fair Value Gaps) on M5
        """
        poi_list = []
        
        if df_m5 is None or len(df_m5) < 20:
            return poi_list
        
        if not shift.get('shift_detected'):
            return poi_list
        
        shift_type = shift.get('type')
        shift_index = shift.get('break_candle_index', len(df_m5) - 1)
        
        # Look back from shift point to find POIs
        lookback_start = max(0, shift_index - 50)
        
        # 1. Find Order Blocks (last opposite candle before strong move)
        for i in range(lookback_start, shift_index - 1):
            if i < 1:
                continue
            
            current_candle = df_m5.iloc[i]
            next_candle = df_m5.iloc[i + 1]
            
            # Calculate candle bodies
            current_body = abs(current_candle['close'] - current_candle['open'])
            next_body = abs(next_candle['close'] - next_candle['open'])
            
            # Bullish OB: bearish candle followed by strong bullish move
            if shift_type == 'BOS_UP':
                is_bearish = current_candle['close'] < current_candle['open']
                is_strong_bullish = (next_candle['close'] > next_candle['open'] and 
                                    next_body > current_body * 1.5)
                
                if is_bearish and is_strong_bullish:
                    poi_list.append({
                        'type': 'OB',
                        'direction': 'bullish',
                        'high': current_candle['high'],
                        'low': current_candle['low'],
                        'index': i,
                        'strength': next_body / current_body if current_body > 0 else 1
                    })
            
            # Bearish OB: bullish candle followed by strong bearish move
            elif shift_type == 'BOS_DOWN':
                is_bullish = current_candle['close'] > current_candle['open']
                is_strong_bearish = (next_candle['close'] < next_candle['open'] and 
                                    next_body > current_body * 1.5)
                
                if is_bullish and is_strong_bearish:
                    poi_list.append({
                        'type': 'OB',
                        'direction': 'bearish',
                        'high': current_candle['high'],
                        'low': current_candle['low'],
                        'index': i,
                        'strength': next_body / current_body if current_body > 0 else 1
                    })
        
        # 2. Find Fair Value Gaps (imbalance/gap between candles)
        for i in range(lookback_start + 1, shift_index - 1):
            if i < 2:
                continue
            
            candle_before = df_m5.iloc[i - 1]
            candle_current = df_m5.iloc[i]
            candle_after = df_m5.iloc[i + 1]
            
            # Bullish FVG: gap up (low of after > high of before)
            if shift_type == 'BOS_UP':
                gap_up = candle_after['low'] > candle_before['high']
                if gap_up:
                    gap_size = candle_after['low'] - candle_before['high']
                    poi_list.append({
                        'type': 'FVG',
                        'direction': 'bullish',
                        'high': candle_after['low'],
                        'low': candle_before['high'],
                        'index': i,
                        'strength': gap_size * 10000  # Convert to pips
                    })
            
            # Bearish FVG: gap down (high of after < low of before)
            elif shift_type == 'BOS_DOWN':
                gap_down = candle_after['high'] < candle_before['low']
                if gap_down:
                    gap_size = candle_before['low'] - candle_after['high']
                    poi_list.append({
                        'type': 'FVG',
                        'direction': 'bearish',
                        'high': candle_before['low'],
                        'low': candle_after['high'],
                        'index': i,
                        'strength': gap_size * 10000  # Convert to pips
                    })
        
        # Sort by strength and return top 5
        poi_list.sort(key=lambda x: x['strength'], reverse=True)
        return poi_list[:5]
    
    def identify_liquidity(self, df_m15: pd.DataFrame) -> List[Dict]:
        """
        Identify liquidity pools (equal highs/lows, trendline liquidity)
        """
        liquidity = []
        if df_m15 is None or len(df_m15) < 50:
            return liquidity
            
        # Find Equal Highs (Resistance Liquidity)
        highs = df_m15['high'].values
        for i in range(10, len(highs)-5):
            # Check if current high is close to a previous high (within 2 pips)
            for j in range(i-20, i-2):
                if abs(highs[i] - highs[j]) < 0.0002:
                    liquidity.append({
                        'type': 'EQH', # Equal Highs
                        'price': highs[i],
                        'index': i,
                        'strength': 'high'
                    })
                    break
                    
        # Find Equal Lows (Support Liquidity)
        lows = df_m15['low'].values
        for i in range(10, len(lows)-5):
            for j in range(i-20, i-2):
                if abs(lows[i] - lows[j]) < 0.0002:
                    liquidity.append({
                        'type': 'EQL', # Equal Lows
                        'price': lows[i],
                        'index': i,
                        'strength': 'high'
                    })
                    break
                    
        return liquidity[-5:] # Return last 5

    def detect_inducement(self, df_m5: pd.DataFrame, poi_list: List[Dict]) -> bool:
        """
        Check if there is inducement (fake move) before the POI
        """
        if not poi_list or len(df_m5) < 10:
            return False
            
        # Simple inducement: price created a minor pullback just before POI
        # This acts as "bait" for early traders
        
        # For now, we'll assume inducement exists if we have multiple POIs close together
        if len(poi_list) >= 2:
            return True
            
        return False
    
    def calculate_entry(self, poi: Dict, current_price: float, symbol: str) -> Optional[Dict]:
        """
        Calculate entry, SL, and TP based on POI
        Target: 4.5 R:R (from manual trades)
        """
        if not poi:
            return None
        
        direction = poi.get('direction')
        pip_size = self._get_pip_size(symbol)
        sl_pips, tp_pips = self._get_sl_tp_pips(symbol)
        
        if direction == 'bullish':
            # Enter at POI low, SL below, TP above
            entry = poi['low']
            sl = entry - (sl_pips * pip_size)
            tp = entry + (tp_pips * pip_size)
            
            return {
                'type': 'LONG',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'rr': (tp - entry) / (entry - sl)
            }
        
        elif direction == 'bearish':
            # Enter at POI high, SL above, TP below
            entry = poi['high']
            sl = entry + (sl_pips * pip_size)
            tp = entry - (tp_pips * pip_size)
            
            return {
                'type': 'SHORT',
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'rr': (entry - tp) / (sl - entry)
            }
        
        return None
    
    def generate_signals(self, symbol: str, df_h4: pd.DataFrame, 
                        df_m15: pd.DataFrame, df_m5: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals using multi-timeframe analysis
        Phase 3B: Includes Premium/Discount, Liquidity, Inducement
        """
        signals = []
        
        # Step 1: Identify structure (H4)
        structure = self.identify_structure(df_h4)
        # print(f"DEBUG: Structure Trend: {structure.get('trend')}")
        
        # Step 2: Identify Premium/Discount Zones
        zones = self.identify_premium_discount(df_h4, structure)
        
        # Step 3: Detect shift (M15)
        shift = self.detect_shift(df_m15, structure)
        
        if shift.get('shift_detected'):
            # print(f"DEBUG: Shift Detected! Type: {shift.get('type')} at {df_m15.index[-1]}")
            pass
        else:
            # print(f"DEBUG: No shift detected. Structure trend: {structure.get('trend')}")
            return signals
            
        # Step 4: Identify Liquidity (M15)
        liquidity = self.identify_liquidity(df_m15)
        
        # Step 5: Identify POI (M5)
        poi_list = self.identify_poi(df_m5, shift)
        if poi_list:
            print(f"DEBUG: Found {len(poi_list)} POIs")
        
        # Step 6: Check Inducement
        has_inducement = self.detect_inducement(df_m5, poi_list)
        
        # Step 7: Generate entry signals
        current_price = df_m5['close'].iloc[-1]
        equilibrium = zones.get('equilibrium')
        
        for poi in poi_list:
            # Filter by Premium/Discount
            if equilibrium:
                # Only Buy in Discount (POI below equilibrium)
                if poi['direction'] == 'bullish' and poi['low'] > equilibrium:
                    continue
                
                # Only Sell in Premium (POI above equilibrium)
                if poi['direction'] == 'bearish' and poi['high'] < equilibrium:
                    continue
            
            # Boost signal if inducement exists
            if has_inducement:
                poi['strength'] *= 1.2
                
            entry_signal = self.calculate_entry(poi, current_price, symbol)
            if entry_signal:
                entry_signal['symbol'] = symbol
                entry_signal['poi_type'] = poi['type']
                entry_signal['structure'] = structure['trend']
                entry_signal['has_inducement'] = has_inducement
                # Add timestamp
                entry_signal['time'] = df_m5['time'].iloc[-1] if 'time' in df_m5.columns else df_m5.index[-1]
                signals.append(entry_signal)
        
        return signals
