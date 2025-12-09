import pandas as pd
from datetime import timedelta, datetime
import pytz
from app.models.strategy import Signal, RangeLevel
from app.strategies.base import BaseStrategy
from app.smc.fvg import FVGDetector
from app.smc.liquidity import LiquidityDetector
from app.smc.swings import SwingDetector
from app.smc.smc_analyzer import SMCAnalyzer

class Range4HStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Range 4H Strategy")
        self.smc_analyzer = SMCAnalyzer()

def detect_4h_range(df_4h: pd.DataFrame) -> list[RangeLevel]:
    """
    Identifies the 4H Range based on the first 4H candle of the day.
    Simplified to work with any 4H data structure.
    """
    ranges = []
    
    # Ensure 'time' is datetime and set as index
    if 'time' in df_4h.columns:
        if not pd.api.types.is_datetime64_any_dtype(df_4h['time']):
            df_4h['time'] = pd.to_datetime(df_4h['time'])
        # Localize to UTC if not already timezone-aware
        if df_4h['time'].dt.tz is None:
            df_4h['time'] = df_4h['time'].dt.tz_localize('UTC')
        df_4h = df_4h.set_index('time')
    elif not isinstance(df_4h.index, pd.DatetimeIndex):
        # If no time column and index is not DatetimeIndex, can't process
        return ranges
    elif df_4h.index.tz is None:
        df_4h.index = df_4h.index.tz_localize('UTC')

    # Group by date and take the first candle of each day
    # This works regardless of what hour the data starts at
    df_4h['date'] = df_4h.index.date
    
    for date in df_4h['date'].unique():
        day_data = df_4h[df_4h['date'] == date]
        
        if not day_data.empty:
            # Take the first candle of the day
            candle = day_data.iloc[0]
            start_time = candle.name  # This is the index (timestamp)
            end_time = start_time + timedelta(hours=4)
            
            r = RangeLevel(
                date=str(date),
                high=candle['high'],
                low=candle['low'],
                start_time=start_time,
                end_time=end_time
            )
            ranges.append(r)
    
    # Clean up temporary column
    df_4h.drop('date', axis=1, inplace=True)
            
    return ranges


def find_dynamic_tp(df_5m: pd.DataFrame, entry_price: float, sl_price: float, 
                    signal_type: str, signal_time, min_rr: float = 1.5, 
                    prefer_higher_rr: bool = False) -> tuple[float, float]:
    """
    Calculate dynamic TP based on FVG zones and liquidity levels.
    
    Strategy:
    1. Detect nearby FVG zones (50% fill targets)
    2. Detect liquidity zones (equal highs/lows, swing extremes)
    3. Pick nearest valid target with min RR of 1.5-2.0
    4. Max RR of 4.0
    
    Args:
        prefer_higher_rr: If True, prefer swing targets (higher RR) over FVG (V7 mode)
    """
    # Calculate risk
    risk = abs(entry_price - sl_price)
    min_tp_distance = risk * min_rr
    max_tp_distance = risk * 4.0
    
    # Get future data (next 200 candles for better TP finding)
    future_df = df_5m[df_5m.index > signal_time].head(200)
    if future_df.empty:
        # Fallback to 2R
        return entry_price + (risk * 2.0) if signal_type == 'LONG' else entry_price - (risk * 2.0)
    
    # Detect FVG zones
    fvg_detector = FVGDetector(min_gap_size=0.00005)
    fvgs = fvg_detector.detect_fvgs(future_df) # Returns FairValueGap objects
    
    # Detect swings for liquidity
    swing_detector = SwingDetector(lookback_left=10, lookback_right=10)
    swing_highs, swing_lows = swing_detector.detect_swings(future_df) # Returns SwingPoint objects
    
    # Collect potential TP candidates
    tp_candidates = []
    
    # Add FVG 50% levels (lower priority in V7)
    for fvg in fvgs:
        fvg_50 = (fvg.top + fvg.bottom) / 2 # Access attributes directly
        
        if signal_type == 'LONG':
            if fvg_50 > entry_price:
                distance = fvg_50 - entry_price
                if min_tp_distance <= distance <= max_tp_distance:
                    rr = distance / risk
                    priority = 1 if prefer_higher_rr else 0  # Lower priority in V7
                    tp_candidates.append({'price': fvg_50, 'rr': rr, 'type': 'FVG_50', 'priority': priority})
        else:  # SHORT
            if fvg_50 < entry_price:
                distance = entry_price - fvg_50
                if min_tp_distance <= distance <= max_tp_distance:
                    rr = distance / risk
                    priority = 1 if prefer_higher_rr else 0
                    tp_candidates.append({'price': fvg_50, 'rr': rr, 'type': 'FVG_50', 'priority': priority})
    
    # Add swing extremes as liquidity targets (higher priority in V7)
    if signal_type == 'LONG':
        for swing_point in swing_highs: # Iterate over SwingPoint objects
            swing_price = swing_point.price # Access price attribute
            if swing_price > entry_price:
                distance = swing_price - entry_price
                if min_tp_distance <= distance <= max_tp_distance:
                    rr = distance / risk
                    priority = 0 if prefer_higher_rr else 1  # Higher priority in V7
                    tp_candidates.append({'price': swing_price, 'rr': rr, 'type': 'SWING_HIGH', 'priority': priority})
    else:  # SHORT
        for swing_point in swing_lows: # Iterate over SwingPoint objects
            swing_price = swing_point.price # Access price attribute
            if swing_price < entry_price:
                distance = entry_price - swing_price
                if min_tp_distance <= distance <= max_tp_distance:
                    rr = distance / risk
                    priority = 0 if prefer_higher_rr else 1
                    tp_candidates.append({'price': swing_price, 'rr': rr, 'type': 'SWING_LOW', 'priority': priority})
    
    # Pick best candidates
    tp1 = None
    tp2 = None
    
    if tp_candidates:
        # Sort by RR
        tp_candidates.sort(key=lambda x: x['rr'])
        
        # TP1: Conservative (nearest valid target > min_rr)
        # Filter for RR >= min_rr
        valid_candidates = [c for c in tp_candidates if c['rr'] >= min_rr]
        
        if valid_candidates:
            tp1 = valid_candidates[0]['price']
            
            # TP2: Aggressive (further target, ideally > 2R or > TP1)
            # Look for a target with significantly better RR
            better_candidates = [c for c in valid_candidates if c['rr'] >= valid_candidates[0]['rr'] + 1.0]
            if better_candidates:
                 tp2 = better_candidates[0]['price']
            elif len(valid_candidates) > 1:
                 # Just take the next best one if it exists and is somewhat further
                 tp2 = valid_candidates[-1]['price']
    
    # Fallback logic
    if not tp1:
        tp1 = entry_price + (risk * 2.0) if signal_type == 'LONG' else entry_price - (risk * 2.0)
        
    if not tp2:
        # If no TP2 found, set it to 3R or 1.5x TP1 distance
        tp2 = entry_price + (risk * 3.0) if signal_type == 'LONG' else entry_price - (risk * 3.0)
        
    return tp1, tp2


def check_swing_confirmation(df_5m: pd.DataFrame, entry_time, entry_price: float, 
                             signal_type: str, lookback_candles: int = 20) -> bool:
    """
    Check if entry aligns with recent swing structure (proxy for OB).
    
    Strategy:
    - For LONG: Price should be near a recent swing low (support)
    - For SHORT: Price should be near a recent swing high (resistance)
    
    This filters out entries in the middle of nowhere.
    """
    # Get recent data before entry
    recent_df = df_5m[df_5m.index < entry_time].tail(lookback_candles)
    if len(recent_df) < 10:
        return False  # Not enough data
    
    # Detect swings
    swing_detector = SwingDetector(lookback_left=5, lookback_right=5)
    swing_highs, swing_lows = swing_detector.detect_swings(recent_df) # Returns SwingPoint objects
    
    # Check if entry is near a swing point
    threshold = 0.001  # ~10 pips tolerance (was 0.0005 = 5 pips)
    
    if signal_type == 'LONG':
        # Check if near a recent swing low
        for swing_point in swing_lows: # Iterate over SwingPoint objects
            swing_price = swing_point.price # Access price attribute
            if abs(entry_price - swing_price) <= threshold:
                return True
    else:  # SHORT
        # Check if near a recent swing high
        for swing_point in swing_highs: # Iterate over SwingPoint objects
            swing_price = swing_point.price # Access price attribute
            if abs(entry_price - swing_price) <= threshold:
                return True
    
    return False


def calculate_ema(df: pd.DataFrame, period: int = 200) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return df['close'].ewm(span=period, adjust=False).mean()

def analyze_5m_signals(self, df_5m: pd.DataFrame, ranges: list[RangeLevel], 
                       use_dynamic_tp: bool = True,
                       use_swing_filter: bool = True,
                       use_trend_filter: bool = True,
                       min_rr: float = 1.5,
                       prefer_higher_rr: bool = False) -> list[Signal]:
    """
    Detects signals on 5M data based on 4H ranges and SMC concepts.
    Strategy: Liquidity Sweep of Range -> MS Break -> OB Entry.
    """
    signals = []
    
    # 1. Prepare Data
    if 'time' in df_5m.columns:
        df_5m['time'] = pd.to_datetime(df_5m['time'])
        if df_5m['time'].dt.tz is None:
            df_5m['time'] = df_5m['time'].dt.tz_localize('UTC')
        df_5m = df_5m.set_index('time')
        
    # 2. Run SMC Analysis (Pre-calculate features)
    # We run this once to get all structures, OBs, etc.
    # Note: In a real live bot, this would be updated incrementally.
    analysis = self.smc_analyzer.analyze_chart(df_5m)
    
    # Extract features and index them by time for fast lookup
    obs = analysis.get('order_blocks', [])
    # Sort OBs by time
    obs.sort(key=lambda x: x['date'] if x['date'] else pd.Timestamp.min)
    
    # 3. Iterate through data to simulate real-time detection
    # Sort ranges by date
    ranges_by_date = {r.date: r for r in ranges}
    
    current_date = None
    current_range = None
    
    # State variables for setup tracking
    # 'setup': {'type': 'LONG'/'SHORT', 'stage': 'SWEEP'/'MS_BREAK'/'OB_WAIT', 'ob': ...}
    active_setup = None
    
    # EMA for trend filter
    ema200 = calculate_ema(df_5m, 200)
    
    for i in range(len(df_5m)):
        time = df_5m.index[i]
        row = df_5m.iloc[i]
        date_str = str(time.date())
        
        # Update current range
        if date_str != current_date:
            current_date = date_str
            current_range = ranges_by_date.get(date_str)
            active_setup = None # Reset setup on new day
            
        if not current_range:
            continue
            
        # Skip if within range formation time
        if time < current_range.end_time:
            continue
            
        close = row['close']
        high = row['high']
        low = row['low']
        
        # --- PHASE 1: DETECT SWEEP ---
        if active_setup is None:
            # Check for Sweep of Range High (Potential SHORT)
            if high > current_range.high:
                # To confirm sweep, we need price to close back inside OR show rejection
                # Simple check: Close < Range High (Fakeout)
                if close < current_range.high:
                    # Trend Filter
                    if use_trend_filter and close > ema200.iloc[i]:
                        continue
                        
                    active_setup = {
                        'type': 'SHORT',
                        'stage': 'OB_WAIT', # Skip MS break for now to simplify, look for OB immediately
                        'sweep_time': time,
                        'range_level': current_range.high
                    }
            
            # Check for Sweep of Range Low (Potential LONG)
            elif low < current_range.low:
                if close > current_range.low:
                    # Trend Filter
                    if use_trend_filter and close < ema200.iloc[i]:
                        continue
                        
                    active_setup = {
                        'type': 'LONG',
                        'stage': 'OB_WAIT',
                        'sweep_time': time,
                        'range_level': current_range.low
                    }
        
        # --- PHASE 2: FIND ENTRY OB ---
        if active_setup and active_setup['stage'] == 'OB_WAIT':
            # Look for a recent OB created AFTER the sweep started (or slightly before)
            # We look at the list of OBs detected by analyzer
            
            # Filter OBs that are:
            # 1. Created recently (last 10 candles)
            # 2. Match direction (Bearish OB for SHORT, Bullish OB for LONG)
            # 3. Not breached yet
            
            relevant_obs = [
                ob for ob in obs 
                if ob['date'] <= time and ob['date'] >= active_setup['sweep_time'] - timedelta(minutes=60) # Look back 1 hour
                and ((active_setup['type'] == 'SHORT' and ob['type'] == 'bearish') or 
                     (active_setup['type'] == 'LONG' and ob['type'] == 'bullish'))
            ]
            
            if relevant_obs:
                # Pick the most recent strong OB
                best_ob = relevant_obs[-1] # Most recent
                active_setup['ob'] = best_ob
                active_setup['stage'] = 'ENTRY_WAIT'
                
            # Timeout if no OB found within reasonable time (e.g., 4 hours)
            if time - active_setup['sweep_time'] > timedelta(hours=4):
                active_setup = None
                
        # --- PHASE 3: ENTRY ON RETEST ---
        if active_setup and active_setup['stage'] == 'ENTRY_WAIT':
            ob = active_setup['ob']
            
            # Check if price hits OB
            # LONG: Price dips into Bullish OB (Low <= OB Top)
            # SHORT: Price rallies into Bearish OB (High >= OB Bottom)
            
            entry_signal = False
            entry_price = 0
            sl_price = 0
            
            if active_setup['type'] == 'LONG':
                if low <= ob['top'] and high >= ob['bottom']: # Touched OB
                    entry_signal = True
                    entry_price = ob['top'] # Limit entry at top of OB
                    sl_price = ob['bottom'] - (ob['top'] - ob['bottom']) * 0.5 # SL below OB
            else: # SHORT
                if high >= ob['bottom'] and low <= ob['top']: # Touched OB
                    entry_signal = True
                    entry_price = ob['bottom'] # Limit entry at bottom of OB
                    sl_price = ob['top'] + (ob['top'] - ob['bottom']) * 0.5 # SL above OB
            
            if entry_signal:
                # Generate Signal
                
                # Dynamic TP
                if use_dynamic_tp:
                    tp1, tp2 = find_dynamic_tp(df_5m, entry_price, sl_price, active_setup['type'], time, min_rr=min_rr, prefer_higher_rr=prefer_higher_rr)
                else:
                    risk = abs(entry_price - sl_price)
                    tp1 = entry_price + (risk * 2) if active_setup['type'] == 'LONG' else entry_price - (risk * 2)
                    tp2 = entry_price + (risk * 3) if active_setup['type'] == 'LONG' else entry_price - (risk * 3)
                
                # Check Min RR
                risk = abs(entry_price - sl_price)
                reward = abs(entry_price - tp1)
                if risk > 0 and (reward / risk) >= min_rr:
                    signals.append(Signal(
                        time=time,
                        type=active_setup['type'],
                        price=entry_price,
                        sl=sl_price,
                        tp=tp1,
                        tp2=tp2,
                        reason=f"Sweep of 4H Range -> OB Entry ({active_setup['type']})"
                    ))
                
                # Reset setup after entry (or we could allow multiple entries, but let's be conservative)
                active_setup = None
            
            # Timeout if entry doesn't happen
            if time - active_setup['sweep_time'] > timedelta(hours=12):
                active_setup = None
                
    # Calculate closes (same as before)
    signals_with_closes = []
    for signal in signals:
        future_candles = df_5m[df_5m.index > signal.time]
        close_time = None
        close_price = None
        outcome = None
        status = 'ACTIVE'
        tp1_hit = False
        current_sl = signal.sl
        
        for time, row in future_candles.iterrows():
            if signal.type == 'LONG':
                if signal.tp2 and row['high'] >= signal.tp2:
                    close_time = time; close_price = signal.tp2; outcome = 'TP2_HIT'; status = 'CLOSED'; break
                elif not tp1_hit and row['high'] >= signal.tp:
                    tp1_hit = True; current_sl = signal.price
                elif row['low'] <= current_sl:
                    close_time = time; close_price = current_sl; outcome = 'SL_HIT' if not tp1_hit else 'TP1_HIT'; status = 'CLOSED'; break
            else:
                if signal.tp2 and row['low'] <= signal.tp2:
                    close_time = time; close_price = signal.tp2; outcome = 'TP2_HIT'; status = 'CLOSED'; break
                elif not tp1_hit and row['low'] <= signal.tp:
                    tp1_hit = True; current_sl = signal.price
                elif row['high'] >= current_sl:
                    close_time = time; close_price = current_sl; outcome = 'SL_HIT' if not tp1_hit else 'TP1_HIT'; status = 'CLOSED'; break
        
        signal_dict = signal.model_dump()
        signal_dict['close_time'] = close_time
        signal_dict['close_price'] = close_price
        signal_dict['outcome'] = outcome
        signal_dict['status'] = status
        signals_with_closes.append(Signal(**signal_dict))
            
    return signals_with_closes
