import pandas as pd
from datetime import timedelta
from app.models.strategy import RangeLevel, Signal
from app.smc.fvg import FVGDetector
from app.smc.liquidity import LiquidityDetector
from app.smc.swings import SwingDetector

def detect_4h_range(df_4h: pd.DataFrame) -> list[RangeLevel]:
    """
    Identifies the 4H Range based on the first 4H candle of the day (00:00).
    Assumes df_4h is indexed by time or has a 'time' column.
    """
    ranges = []
    
    # Ensure 'time' is datetime
    if 'time' in df_4h.columns:
        df_4h['time'] = pd.to_datetime(df_4h['time'])
        df_4h = df_4h.set_index('time')
    
    # Group by day
    unique_dates = df_4h.index.date
    processed_dates = set()
    
    for date in unique_dates:
        if date in processed_dates:
            continue
        
        # Get data for this date
        day_data = df_4h[df_4h.index.date == date]
        
        # Find the 00:00 candle
        first_candle = day_data[day_data.index.hour == 0]
        
        if not first_candle.empty:
            candle = first_candle.iloc[0]
            start_time = candle.name
            end_time = start_time + timedelta(hours=4)
            
            r = RangeLevel(
                date=str(date),
                high=candle['high'],
                low=candle['low'],
                start_time=start_time,
                end_time=end_time
            )
            ranges.append(r)
        
        processed_dates.add(date)
            
    return ranges


def find_dynamic_tp(df_5m: pd.DataFrame, entry_price: float, sl_price: float, 
                    signal_type: str, signal_time, min_rr: float = 1.5) -> float:
    """
    Calculate dynamic TP based on FVG zones and liquidity levels.
    
    Strategy:
    1. Detect nearby FVG zones (50% fill targets)
    2. Detect liquidity zones (equal highs/lows, swing extremes)
    3. Pick nearest valid target with min RR of 1.5-2.0
    4. Max RR of 4.0
    """
    # Calculate risk
    risk = abs(entry_price - sl_price)
    min_tp_distance = risk * min_rr
    max_tp_distance = risk * 4.0
    
    # Get future data (next 100 candles for efficiency)
    future_df = df_5m[df_5m.index > signal_time].head(100)
    if future_df.empty:
        # Fallback to 2R
        return entry_price + (risk * 2.0) if signal_type == 'LONG' else entry_price - (risk * 2.0)
    
    # Detect FVG zones
    fvg_detector = FVGDetector(min_gap_size=0.00005)
    fvgs = fvg_detector.detect_fvgs(future_df)
    
    # Detect swings for liquidity
    swing_detector = SwingDetector(swing_length=10)
    swing_highs, swing_lows = swing_detector.detect_swings(future_df)
    
    # Collect potential TP candidates
    tp_candidates = []
    
    # Add FVG 50% levels
    for fvg in fvgs:
        fvg_50 = (fvg['top'] + fvg['bottom']) / 2
        
        if signal_type == 'LONG':
            if fvg_50 > entry_price:
                distance = fvg_50 - entry_price
                if min_tp_distance <= distance <= max_tp_distance:
                    rr = distance / risk
                    tp_candidates.append({'price': fvg_50, 'rr': rr, 'type': 'FVG_50'})
        else:  # SHORT
            if fvg_50 < entry_price:
                distance = entry_price - fvg_50
                if min_tp_distance <= distance <= max_tp_distance:
                    rr = distance / risk
                    tp_candidates.append({'price': fvg_50, 'rr': rr, 'type': 'FVG_50'})
    
    # Add swing extremes as liquidity targets
    if signal_type == 'LONG':
        for idx in swing_highs:
            swing_price = future_df.iloc[idx]['high']
            if swing_price > entry_price:
                distance = swing_price - entry_price
                if min_tp_distance <= distance <= max_tp_distance:
                    rr = distance / risk
                    tp_candidates.append({'price': swing_price, 'rr': rr, 'type': 'SWING_HIGH'})
    else:  # SHORT
        for idx in swing_lows:
            swing_price = future_df.iloc[idx]['low']
            if swing_price < entry_price:
                distance = entry_price - swing_price
                if min_tp_distance <= distance <= max_tp_distance:
                    rr = distance / risk
                    tp_candidates.append({'price': swing_price, 'rr': rr, 'type': 'SWING_LOW'})
    
    # Pick best candidate (nearest with good RR)
    if tp_candidates:
        # Sort by RR (prefer 2-2.5R targets)
        tp_candidates.sort(key=lambda x: abs(x['rr'] - 2.0))
        return tp_candidates[0]['price']
    
    # Fallback to 2R if no structure found
    return entry_price + (risk * 2.0) if signal_type == 'LONG' else entry_price - (risk * 2.0)


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
    swing_detector = SwingDetector(swing_length=5)
    swing_highs, swing_lows = swing_detector.detect_swings(recent_df)
    
    # Check if entry is near a swing point
    threshold = 0.0005  # ~5 pips tolerance
    
    if signal_type == 'LONG':
        # Check if near a recent swing low
        for idx in swing_lows:
            swing_price = recent_df.iloc[idx]['low']
            if abs(entry_price - swing_price) <= threshold:
                return True
    else:  # SHORT
        # Check if near a recent swing high
        for idx in swing_highs:
            swing_price = recent_df.iloc[idx]['high']
            if abs(entry_price - swing_price) <= threshold:
                return True
    
    return False


def calculate_ema(df: pd.DataFrame, period: int = 200) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return df['close'].ewm(span=period, adjust=False).mean()

def analyze_5m_signals(df_5m: pd.DataFrame, ranges: list[RangeLevel], 
                       use_dynamic_tp: bool = True,
                       use_swing_filter: bool = True,
                       use_trend_filter: bool = True,
                       min_rr: float = 1.5) -> list[Signal]:
    """
    Detects signals on 5M data based on 4H ranges.
    Signal: Breakout (Close outside) -> Re-entry (Close inside).
    Also calculates position close based on TP/SL hits.
    
    Args:
        use_dynamic_tp: If True, use FVG/liquidity-based TP. If False, use fixed 2R.
        use_swing_filter: If True, only enter near swing points (quality filter).
        use_trend_filter: If True, only trade with the trend (Price > EMA200 for Long).
        min_rr: Minimum Risk-Reward ratio required to take the trade.
    """
    signals = []
    
    if 'time' in df_5m.columns:
        df_5m['time'] = pd.to_datetime(df_5m['time'])
        df_5m = df_5m.set_index('time')
        
    # Calculate EMA for trend filter
    if use_trend_filter:
        ema200 = calculate_ema(df_5m, 200)
    
    # Sort ranges by date for easier lookup
    ranges_by_date = {r.date: r for r in ranges}
    
    # State tracking per day
    current_date = None
    current_range = None
    breakout_high = False
    breakout_low = False
    
    for time, row in df_5m.iterrows():
        date_str = str(time.date())
        
        if date_str != current_date:
            current_date = date_str
            current_range = ranges_by_date.get(date_str)
            breakout_high = False
            breakout_low = False
            
        if not current_range:
            continue
            
        # Check if we are past the range formation (after 04:00)
        if time < current_range.end_time:
            continue
            
        # Logic
        close = row['close']
        high = row['high']
        low = row['low']
        
        # 1. Check Breakout
        if not breakout_high and close > current_range.high:
            breakout_high = True
            
        if not breakout_low and close < current_range.low:
            breakout_low = False
            
        # 2. Check Re-entry (Signal)
        # SHORT Signal: Breakout High happened, now Close < High
        if breakout_high and close < current_range.high:
            # Trend Filter: Only Short if Price < EMA200
            if use_trend_filter and close > ema200.loc[time]:
                continue

            # Quality filter: Check if near swing structure
            if use_swing_filter:
                if not check_swing_confirmation(df_5m, time, close, 'SHORT'):
                    continue  # Skip this signal - not near structure
            
            sl = high  # Simplified SL
            
            if use_dynamic_tp:
                tp = find_dynamic_tp(df_5m, close, sl, 'SHORT', time, min_rr=min_rr)
            else:
                tp = close - (sl - close) * 2  # Fixed 2R
            
            # Check if TP meets min_rr
            risk = abs(close - sl)
            reward = abs(close - tp)
            if risk > 0 and (reward / risk) < min_rr:
                continue # Skip trade if RR is too low
            
            signals.append(Signal(
                time=time,
                type='SHORT',
                price=close,
                sl=sl,
                tp=tp,
                reason="Re-entry after High Breakout (Swing+Trend)" if use_trend_filter else "Re-entry after High Breakout"
            ))
            breakout_high = False
            
        # LONG Signal: Breakout Low happened, now Close > Low
        if breakout_low and close > current_range.low:
            # Trend Filter: Only Long if Price > EMA200
            if use_trend_filter and close < ema200.loc[time]:
                continue

            # Quality filter: Check if near swing structure
            if use_swing_filter:
                if not check_swing_confirmation(df_5m, time, close, 'LONG'):
                    continue  # Skip this signal - not near structure
            
            sl = low
            
            if use_dynamic_tp:
                tp = find_dynamic_tp(df_5m, close, sl, 'LONG', time, min_rr=min_rr)
            else:
                tp = close + (close - sl) * 2  # Fixed 2R
            
            # Check RR
            risk = abs(close - sl)
            reward = abs(close - tp)
            if risk > 0 and (reward / risk) < min_rr:
                continue # Skip trade
            
            signals.append(Signal(
                time=time,
                type='LONG',
                price=close,
                sl=sl,
                tp=tp,
                reason="Re-entry after Low Breakout (Swing+Trend)" if use_trend_filter else "Re-entry after Low Breakout"
            ))
            breakout_low = False
    
    # Now calculate position closes
    signals_with_closes = []
    for signal in signals:
        # Find candles after this signal
        future_candles = df_5m[df_5m.index > signal.time]
        
        close_time = None
        close_price = None
        outcome = None
        
        for time, row in future_candles.iterrows():
            if signal.type == 'LONG':
                # Check if TP hit
                if row['high'] >= signal.tp:
                    close_time = time
                    close_price = signal.tp
                    outcome = 'TP_HIT'
                    break
                # Check if SL hit
                elif row['low'] <= signal.sl:
                    close_time = time
                    close_price = signal.sl
                    outcome = 'SL_HIT'
                    break
            else:  # SHORT
                # Check if TP hit
                if row['low'] <= signal.tp:
                    close_time = time
                    close_price = signal.tp
                    outcome = 'TP_HIT'
                    break
                # Check if SL hit
                elif row['high'] >= signal.sl:
                    close_time = time
                    close_price = signal.sl
                    outcome = 'SL_HIT'
                    break
        
        # Create updated signal with close info
        signal_dict = signal.model_dump()
        signal_dict['close_time'] = close_time
        signal_dict['close_price'] = close_price
        signal_dict['outcome'] = outcome
        signal_dict['status'] = 'CLOSED' if outcome else 'ACTIVE'
        
        signals_with_closes.append(Signal(**signal_dict))
            
    return signals_with_closes
