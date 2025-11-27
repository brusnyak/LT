"""
Unified Trading Strategy Bot
Implements a multi-timeframe approach to trading based on ICT concepts, SMC, and technical analysis.
All logic is self-contained within this single file.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, time
import pandas as pd
import numpy as np
import pytz

logger = logging.getLogger(__name__)

# --- Helper Functions (to be moved or integrated) ---
def standardize_timeframe(timeframe: str) -> str:
    """Standardize timeframe format."""
    tf = timeframe.upper()
    if tf in ['M1', '1M', '1MIN', '1MINUTE']: return 'M1'
    elif tf in ['M3', '3M', '3MIN', '3MINUTE']: return 'M3'
    elif tf in ['M5', '5M', '5MIN', '5MINUTE']: return 'M5'
    elif tf in ['M15', '15M', '15MIN', '15MINUTE']: return 'M15'
    elif tf in ['M30', '30M', '30MIN', '30MINUTE']: return 'M30'
    elif tf in ['H1', '1H', '1HOUR']: return 'H1'
    elif tf in ['H4', '4H', '4HOUR']: return 'H4'
    elif tf in ['D1', '1D', 'DAILY', 'DAY']: return 'D1'
    elif tf in ['W1', '1W', 'WEEKLY', 'WEEK']: return 'W1'
    return tf

def timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe to minutes."""
    tf = standardize_timeframe(timeframe)
    if tf == 'M1': return 1
    elif tf == 'M3': return 3
    elif tf == 'M5': return 5
    elif tf == 'M15': return 15
    elif tf == 'M30': return 30
    elif tf == 'H1': return 60
    elif tf == 'H4': return 240
    elif tf == 'D1': return 1440
    elif tf == 'W1': return 10080
    return 0

def calculate_risk_reward(entry_price: float, stop_loss: float, take_profit: float) -> float:
    """Calculate the risk-reward ratio."""
    if entry_price > stop_loss:  # Long position
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:  # Short position
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
    return reward / risk if risk > 0 else 0

def calculate_position_size(account_size: float, risk_percentage: float, 
                            entry_price: float, stop_loss: float, pair_type: str = 'forex') -> float:
    """Calculate position size based on risk parameters."""
    risk_amount = account_size * (risk_percentage / 100)
    pip_risk = abs(entry_price - stop_loss)
    
    # Adjust pip_risk for different asset types if necessary (e.g., Forex vs Crypto)
    # For simplicity, assuming 1 unit of price movement is 1 pip/point for now.
    # In a real scenario, this would need to be more sophisticated (e.g., pip value per lot).
    
    position_size = risk_amount / pip_risk if pip_risk > 0 else 0
    return position_size

class UnifiedStrategyBot:
    """
    Unified trading strategy that implements a multi-timeframe approach
    based on ICT concepts and intraday trading requirements.
    All analysis logic is self-contained.
    """
    
    def __init__(self):
        """Initialize the unified strategy bot."""
        self.name = "Unified Strategy Bot"
        
        # Define timeframe hierarchy
        self.timeframe_hierarchy = ['M1', 'M3', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']
        
        # Define key trading sessions (UTC)
        self.sessions = {
            'london': (time(7, 0), time(16, 0)),
            'new_york': (time(12, 0), time(21, 0)),
            'tokyo': (time(0, 0), time(9, 0)),
            'sydney': (time(22, 0), time(7, 0))
        }
        
        # Define key trading windows (UTC)
        self.trading_windows = {
            'london_open': (time(7, 0), time(9, 0)),
            'london_ny_overlap': (time(12, 0), time(16, 0)),
            'ny_close': (time(19, 0), time(21, 0)),
            'key_intraday': [(time(10, 0), time(12, 0)), (time(15, 0), time(17, 0))]
        }

    def _get_timeframe_hierarchy(self, base_timeframe: str) -> Tuple[str, str, str]:
        """Determine higher, middle, and lower timeframes based on a base timeframe."""
        std_tf = standardize_timeframe(base_timeframe)
        try:
            idx = self.timeframe_hierarchy.index(std_tf)
        except ValueError:
            logger.warning(f"Timeframe {base_timeframe} not found in hierarchy, defaulting to H1.")
            idx = self.timeframe_hierarchy.index('H1') # Default to H1 if not found

        higher_tf = self.timeframe_hierarchy[min(idx + 1, len(self.timeframe_hierarchy) - 1)]
        middle_tf = self.timeframe_hierarchy[idx]
        lower_tf = self.timeframe_hierarchy[max(idx - 1, 0)]
        
        # Special handling for very low/high timeframes to ensure a valid hierarchy
        if idx == 0: # M1
            higher_tf = self.timeframe_hierarchy[idx + 2] if idx + 2 < len(self.timeframe_hierarchy) else self.timeframe_hierarchy[-1]
            middle_tf = self.timeframe_hierarchy[idx + 1] if idx + 1 < len(self.timeframe_hierarchy) else self.timeframe_hierarchy[-1]
            lower_tf = self.timeframe_hierarchy[idx]
        elif idx == len(self.timeframe_hierarchy) - 1: # Highest TF
            higher_tf = self.timeframe_hierarchy[idx]
            middle_tf = self.timeframe_hierarchy[idx - 1]
            lower_tf = self.timeframe_hierarchy[idx - 2] if idx - 2 >= 0 else self.timeframe_hierarchy[0]

        return higher_tf, middle_tf, lower_tf

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range."""
        if df.empty or len(df) < period:
            return 0.0
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.ewm(span=period, adjust=False).mean() # Use EMA for ATR smoothing
        return atr.iloc[-1] if not atr.empty else 0.0

    def _is_in_kill_zone(self, timestamp: datetime) -> Tuple[bool, Optional[str]]:
        """Check if the current time is in a kill zone (UTC)."""
        if not isinstance(timestamp, datetime):
            return False, None
        
        # Ensure timestamp is timezone-aware, convert to UTC if not
        if timestamp.tzinfo is None:
            timestamp = pytz.utc.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(pytz.utc)

        hour = timestamp.hour
        
        # London morning session: 7:00-9:00 UTC
        if 7 <= hour < 9:
            return True, 'london_morning'
        # London/NY overlap: 12:00-15:00 UTC
        elif 12 <= hour < 15:
            return True, 'london_ny_overlap'
        # NY afternoon: 17:00-19:00 UTC
        elif 17 <= hour < 19:
            return True, 'ny_afternoon'
        # Asian session: 22:00-1:00 UTC (covers midnight)
        elif hour >= 22 or hour < 1:
            return True, 'asian_session'
            
        return False, None

    def _get_market_type(self, symbol: str) -> str:
        """Determine the market type based on the symbol."""
        if symbol.endswith('USD') or symbol.endswith('JPY') or symbol.endswith('GBP') or symbol.endswith('CAD') or symbol.endswith('CHF') or symbol.endswith('AUD') or symbol.endswith('NZD'):
            if not symbol.startswith('XAU') and not symbol.startswith('XAG'):
                return 'forex'
        if symbol.startswith('XAU') or symbol.startswith('XAG'):
            return 'metals'
        if symbol.endswith('USDT') or symbol in ['BTCUSD', 'ETHUSD', 'XRPUSD', 'ADAUSD', 'SOLUSD']:
            return 'crypto'
        if symbol in ['US30', 'USA30IDXUSD', 'US500', 'USA500IDXUSD', 'USTEC', 'USATECHIDXUSD', 'NAS100', 'SPX500']:
            return 'indices'
        return 'forex' # Default

    # --- SMC/ICT/Technical Analysis Components (Integrated) ---

    def _identify_swing_points(self, df: pd.DataFrame, window: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """Identify swing highs and lows."""
        swing_highs = []
        swing_lows = []
        if len(df) < window * 2 + 1:
            return swing_highs, swing_lows

        for i in range(window, len(df) - window):
            # Swing high
            if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, window+1)):
                swing_highs.append({'index': i, 'price': df['high'].iloc[i], 'date': df.index[i]})
            
            # Swing low
            if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, window+1)):
                swing_lows.append({'index': i, 'price': df['low'].iloc[i], 'date': df.index[i]})
        return swing_highs, swing_lows

    def _identify_market_structure(self, df: pd.DataFrame) -> Dict:
        """Identify market structure (trend, BOS, CHoCH)."""
        swing_highs, swing_lows = self._identify_swing_points(df)
        
        trend = 'neutral'
        structure = 'undefined'
        bos_choch = []

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Simple trend based on last two swings
            last_high = swing_highs[-1]['price']
            second_last_high = swing_highs[-2]['price']
            last_low = swing_lows[-1]['price']
            second_last_low = swing_lows[-2]['price']

            if last_high > second_last_high and last_low > second_last_low:
                trend = 'bullish'
                structure = 'uptrend'
            elif last_high < second_last_high and last_low < second_last_low:
                trend = 'bearish'
                structure = 'downtrend'
            else:
                structure = 'consolidation'
            
            # Identify BOS/CHoCH (simplified)
            if trend == 'bullish':
                # CHoCH if a previous swing low is broken
                if df['close'].iloc[-1] < swing_lows[-1]['price'] and len(swing_lows) > 1:
                    bos_choch.append({'type': 'CHoCH', 'direction': 'bearish', 'price': swing_lows[-1]['price'], 'date': df.index[-1]})
                # BOS if a previous swing high is broken
                elif df['close'].iloc[-1] > swing_highs[-1]['price'] and len(swing_highs) > 1:
                    bos_choch.append({'type': 'BOS', 'direction': 'bullish', 'price': swing_highs[-1]['price'], 'date': df.index[-1]})
            elif trend == 'bearish':
                # CHoCH if a previous swing high is broken
                if df['close'].iloc[-1] > swing_highs[-1]['price'] and len(swing_highs) > 1:
                    bos_choch.append({'type': 'CHoCH', 'direction': 'bullish', 'price': swing_highs[-1]['price'], 'date': df.index[-1]})
                # BOS if a previous swing low is broken
                elif df['close'].iloc[-1] < swing_lows[-1]['price'] and len(swing_lows) > 1:
                    bos_choch.append({'type': 'BOS', 'direction': 'bearish', 'price': swing_lows[-1]['price'], 'date': df.index[-1]})

        return {
            'trend': trend,
            'structure': structure,
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'bos_choch': bos_choch
        }

    def _identify_order_blocks(self, df: pd.DataFrame) -> List[Dict]:
        """Identify order blocks (simplified)."""
        order_blocks = []
        if len(df) < 5: return order_blocks

        for i in range(1, len(df) - 1):
            # Bullish OB: Bearish candle followed by strong bullish candle
            if df['close'].iloc[i-1] < df['open'].iloc[i-1] and \
               df['close'].iloc[i] > df['open'].iloc[i] and \
               df['close'].iloc[i] > df['high'].iloc[i-1]:
                order_blocks.append({
                    'type': 'bullish',
                    'top': df['open'].iloc[i-1],
                    'bottom': df['low'].iloc[i-1], # Use low of bearish candle
                    'date': df.index[i-1],
                    'strength': int((df['high'].iloc[i] - df['low'].iloc[i]) / self._calculate_atr(df) * 10), # Dynamic strength based on candle size relative to ATR
                    'age': len(df) - i
                })
            # Bearish OB: Bullish candle followed by strong bearish candle
            elif df['close'].iloc[i-1] > df['open'].iloc[i-1] and \
                 df['close'].iloc[i] < df['open'].iloc[i] and \
                 df['close'].iloc[i] < df['low'].iloc[i-1]:
                order_blocks.append({
                    'type': 'bearish',
                    'top': df['high'].iloc[i-1], # Use high of bullish candle
                    'bottom': df['open'].iloc[i-1],
                    'date': df.index[i-1],
                    'strength': int((df['high'].iloc[i] - df['low'].iloc[i]) / self._calculate_atr(df) * 10), # Dynamic strength based on candle size relative to ATR
                    'age': len(df) - i
                })
        return sorted(order_blocks, key=lambda x: x['age']) # Sort by age, newest first

    def _identify_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict]:
        """Identify fair value gaps (FVG)."""
        fair_value_gaps = []
        if len(df) < 3: return fair_value_gaps

        for i in range(1, len(df) - 1):
            # Bullish FVG: Low of current candle > High of previous candle
            if df['low'].iloc[i+1] > df['high'].iloc[i-1]:
                fair_value_gaps.append({
                    'type': 'bullish',
                    'top': df['low'].iloc[i+1],
                    'bottom': df['high'].iloc[i-1],
                    'date': df.index[i],
                    'filled': False, 
                    'age': len(df) - i
                })
            # Bearish FVG: High of current candle < Low of previous candle
            elif df['high'].iloc[i+1] < df['low'].iloc[i-1]:
                fair_value_gaps.append({
                    'type': 'bearish',
                    'top': df['low'].iloc[i-1],
                    'bottom': df['high'].iloc[i+1],
                    'date': df.index[i],
                    'filled': False,
                    'age': len(df) - i
                })
        return sorted(fair_value_gaps, key=lambda x: x['age'])

    def _identify_liquidity_sweeps(self, df: pd.DataFrame, market_structure: Dict) -> List[Dict]:
        """Identify liquidity sweeps."""
        liquidity_sweeps = []
        swing_highs = market_structure.get('swing_highs', [])
        swing_lows = market_structure.get('swing_lows', [])
        
        if len(df) < 5: return liquidity_sweeps

        # Look for high sweeps (price breaks above a swing high then reverses)
        for high in swing_highs:
            high_idx = high['index']
            high_price = high['price']
            for i in range(high_idx + 1, min(high_idx + 5, len(df) - 1)): # Check next 5 candles
                if df['high'].iloc[i] > high_price and df['close'].iloc[i] < high_price: # Wick above, close below
                    liquidity_sweeps.append({
                        'type': 'high_sweep',
                        'price': high_price,
                        'date': df.index[i],
                        'strength': 80,
                        'candle_index': i
                    })
                    break # Only one sweep per swing high for simplicity
        
        # Look for low sweeps (price breaks below a swing low then reverses)
        for low in swing_lows:
            low_idx = low['index']
            low_price = low['price']
            for i in range(low_idx + 1, min(low_idx + 5, len(df) - 1)): # Check next 5 candles
                if df['low'].iloc[i] < low_price and df['close'].iloc[i] > low_price: # Wick below, close above
                    liquidity_sweeps.append({
                        'type': 'low_sweep',
                        'price': low_price,
                        'date': df.index[i],
                        'strength': 80,
                        'candle_index': i
                    })
                    break # Only one sweep per swing low for simplicity
        return sorted(liquidity_sweeps, key=lambda x: x['candle_index'])

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate common technical indicators."""
        indicators = {}
        if df.empty: return indicators

        # Moving Averages
        indicators['sma20'] = df['close'].rolling(window=20).mean()
        indicators['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # RSI (14)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(span=14, adjust=False).mean()
        avg_loss = loss.ewm(span=14, adjust=False).mean()
        rs = avg_gain / avg_loss
        indicators['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR (14)
        indicators['atr'] = self._calculate_atr(df, 14)

        return indicators

    def _generate_technical_signals(self, df: pd.DataFrame, indicators: Dict) -> List[Dict]:
        """Generate trading signals based on technical indicators."""
        signals = []
        if df.empty or indicators.get('rsi', pd.Series()).empty: return signals

        latest_rsi = indicators['rsi'].iloc[-1]
        latest_close = df['close'].iloc[-1]
        latest_sma20 = indicators['sma20'].iloc[-1] if not indicators['sma20'].empty else np.nan
        latest_ema50 = indicators['ema50'].iloc[-1] if not indicators['ema50'].empty else np.nan

        # RSI signals
        if latest_rsi < 30:
            signals.append({'type': 'bullish', 'indicator': 'RSI', 'description': 'RSI oversold', 'strength': 60})
        if latest_rsi > 70:
            signals.append({'type': 'bearish', 'indicator': 'RSI', 'description': 'RSI overbought', 'strength': 60})
        
        # MA crossover (simplified)
        if not np.isnan(latest_sma20) and not np.isnan(latest_ema50):
            if latest_sma20 > latest_ema50 and df['close'].iloc[-2] < latest_ema50: # Price crosses above EMA50
                signals.append({'type': 'bullish', 'indicator': 'MA', 'description': 'Price above EMA50', 'strength': 65})
            elif latest_sma20 < latest_ema50 and df['close'].iloc[-2] > latest_ema50: # Price crosses below EMA50
                signals.append({'type': 'bearish', 'indicator': 'MA', 'description': 'Price below EMA50', 'strength': 65})

        return signals

    # --- Multi-Timeframe Analysis & Signal Generation ---

    def analyze_multi_timeframe(self, dfs: Dict[str, pd.DataFrame], symbol: str, 
                                base_timeframe: str) -> Dict:
        """
        Perform multi-timeframe analysis and generate signals.
        
        Args:
            dfs (Dict[str, pd.DataFrame]): Dictionary of OHLCV dataframes for different timeframes.
            symbol (str): Trading symbol.
            base_timeframe (str): The primary timeframe for signal generation.
            
        Returns:
            Dict: Comprehensive analysis results and trade setups.
        """
        higher_tf, middle_tf, lower_tf = self._get_timeframe_hierarchy(base_timeframe)
        
        higher_tf_data = dfs.get(higher_tf)
        middle_tf_data = dfs.get(middle_tf)
        lower_tf_data = dfs.get(lower_tf)

        if higher_tf_data is None or higher_tf_data.empty:
            logger.error(f"Missing or empty data for higher timeframe {higher_tf}")
            return {'error': f"Missing data for {higher_tf}"}
        if middle_tf_data is None or middle_tf_data.empty:
            logger.error(f"Missing or empty data for middle timeframe {middle_tf}")
            return {'error': f"Missing data for {middle_tf}"}
        if lower_tf_data is None or lower_tf_data.empty:
            logger.warning(f"Missing or empty data for lower timeframe {lower_tf}, proceeding without it.")
            
        current_time = middle_tf_data.index[-1] if not middle_tf_data.empty else datetime.utcnow()
        in_kill_zone, kill_zone_name = self._is_in_kill_zone(current_time)
        market_type = self._get_market_type(symbol)
        
        # 1. Higher Timeframe Analysis (Directional Bias)
        higher_ms = self._identify_market_structure(higher_tf_data)
        higher_indicators = self._calculate_technical_indicators(higher_tf_data)
        higher_bias = higher_ms['trend']
        
        # 2. Middle Timeframe Analysis (Liquidity, Interest Zones)
        middle_ms = self._identify_market_structure(middle_tf_data)
        middle_obs = self._identify_order_blocks(middle_tf_data)
        middle_fvgs = self._identify_fair_value_gaps(middle_tf_data)
        middle_sweeps = self._identify_liquidity_sweeps(middle_tf_data, middle_ms)
        
        interest_zones = []
        for ob in middle_obs:
            if (higher_bias == 'bullish' and ob['type'] == 'bullish') or \
               (higher_bias == 'bearish' and ob['type'] == 'bearish'):
                interest_zones.append({'type': 'order_block', 'price_range': [ob['bottom'], ob['top']], 'bias': ob['type'], 'strength': ob['strength']})
        for fvg in middle_fvgs:
            if (higher_bias == 'bullish' and fvg['type'] == 'bullish') or \
               (higher_bias == 'bearish' and fvg['type'] == 'bearish'):
                interest_zones.append({'type': 'fvg', 'price_range': [fvg['bottom'], fvg['top']], 'bias': fvg['type'], 'strength': 65})
        
        # 3. Lower Timeframe Analysis (Entry Triggers)
        entry_signals = []
        if lower_tf_data is not None and not lower_tf_data.empty:
            lower_indicators = self._calculate_technical_indicators(lower_tf_data)
            lower_tech_signals = self._generate_technical_signals(lower_tf_data, lower_indicators)
            
            current_price = lower_tf_data['close'].iloc[-1]
            atr = self._calculate_atr(lower_tf_data)

            # Entry logic: Confluence of higher TF bias, middle TF interest zones/sweeps, and lower TF signals
            for signal in lower_tech_signals:
                if (signal['type'] == 'bullish' and higher_bias == 'bullish') or \
                   (signal['type'] == 'bearish' and higher_bias == 'bearish'):
                    
                    # Check for proximity to interest zones
                    for zone in interest_zones:
                        if zone['price_range'][0] <= current_price <= zone['price_range'][1]:
                            # Found a setup!
                            stop_loss = current_price - (atr * 1.5) if signal['type'] == 'bullish' else current_price + (atr * 1.5)
                            take_profit = current_price + (atr * 3) if signal['type'] == 'bullish' else current_price - (atr * 3)
                            
                            rr = calculate_risk_reward(current_price, stop_loss, take_profit)
                            if rr >= 1.5: # Minimum 1.5 R:R
                                entry_signals.append({
                                    'type': signal['type'],
                                    'entry_price': current_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'risk_reward': rr,
                                    'strength': signal['strength'] + zone['strength'] / 10 + (20 if in_kill_zone else 0),
                                    'reason': f"Confluence: {signal['description']} in {zone['type']} zone, aligned with {higher_bias} HTF bias.",
                                    'timeframe': base_timeframe,
                                    'in_kill_zone': in_kill_zone
                                })
                    
                    # Check for liquidity sweep reversal
                    for sweep in middle_sweeps:
                        if (sweep['type'] == 'low_sweep' and signal['type'] == 'bullish' and higher_bias == 'bullish' and current_price > sweep['price']) or \
                           (sweep['type'] == 'high_sweep' and signal['type'] == 'bearish' and higher_bias == 'bearish' and current_price < sweep['price']):
                            
                            stop_loss = sweep['price'] - (atr * 0.5) if signal['type'] == 'bullish' else sweep['price'] + (atr * 0.5)
                            take_profit = current_price + (current_price - stop_loss) * 2 if signal['type'] == 'bullish' else current_price - (stop_loss - current_price) * 2
                            
                            rr = calculate_risk_reward(current_price, stop_loss, take_profit)
                            if rr >= 1.5:
                                entry_signals.append({
                                    'type': signal['type'],
                                    'entry_price': current_price,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit,
                                    'risk_reward': rr,
                                    'strength': signal['strength'] + sweep['strength'] / 10 + (20 if in_kill_zone else 0),
                                    'reason': f"Confluence: {signal['description']} after {sweep['type']} reversal, aligned with {higher_bias} HTF bias.",
                                    'timeframe': base_timeframe,
                                    'in_kill_zone': in_kill_zone
                                })
        
        # Sort signals by strength
        entry_signals.sort(key=lambda x: x.get('strength', 0), reverse=True)

        return {
            'symbol': symbol,
            'base_timeframe': base_timeframe,
            'current_time': current_time,
            'market_type': market_type,
            'in_kill_zone': in_kill_zone,
            'kill_zone_name': kill_zone_name,
            'higher_tf_bias': higher_bias,
            'higher_tf_structure': higher_ms['structure'],
            'middle_tf_interest_zones': interest_zones,
            'middle_tf_liquidity_sweeps': middle_sweeps,
            'trade_setups': entry_signals[:5] # Return top 5 setups
        }

    def generate_trade_setup(self, analysis_result: Dict, account_size: float, risk_percentage: float) -> Optional[Dict]:
        """
        Generate a complete trade setup from the best signal in the analysis result.
        Includes position sizing.
        """
        if not analysis_result or not analysis_result.get('trade_setups'):
            return None
        
        best_signal = analysis_result['trade_setups'][0] # Take the strongest signal
        
        entry_price = best_signal['entry_price']
        stop_loss = best_signal['stop_loss']
        
        position_sizing = calculate_position_size(
            account_size, risk_percentage, entry_price, stop_loss, analysis_result['market_type']
        )
        
        trade_setup = {
            'symbol': analysis_result['symbol'],
            'direction': best_signal['type'].upper(),
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': best_signal['take_profit'],
            'risk_reward': best_signal['risk_reward'],
            'position_size': position_sizing,
            'strategy': self.name,
            'timeframe': best_signal['timeframe'],
            'signal_strength': best_signal['strength'],
            'reason': best_signal['reason'],
            'timestamp': analysis_result['current_time'].isoformat()
        }
        return trade_setup
