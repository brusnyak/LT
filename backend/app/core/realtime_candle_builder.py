import pandas as pd
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional

class RealtimeCandleBuilder:
    """
    Aggregates raw tick data into OHLCV candles for specified timeframes.
    """
    
    def __init__(self, timeframes: List[str], timezone: str = 'Europe/Bratislava'):
        self.timeframes = timeframes
        self.timezone = pytz.timezone(timezone)
        self.buffers: Dict[str, List[Dict]] = {tf: [] for tf in timeframes}
        self.current_candles: Dict[str, Dict] = {tf: None for tf in timeframes}
        self.last_processed_tick_time: Dict[str, datetime] = {tf: None for tf in timeframes}

    def add_tick(self, tick: Dict):
        """
        Adds a new tick to the buffer and processes it for all timeframes.
        Tick format: {'time': datetime_object, 'bid': float, 'ask': float}
        """
        tick_time = tick['time'].astimezone(self.timezone)
        
        for tf in self.timeframes:
            self.buffers[tf].append(tick)
            self._process_buffer(tf, tick_time)

    def _process_buffer(self, timeframe: str, current_tick_time: datetime):
        """
        Processes the buffer for a specific timeframe to build candles.
        """
        interval_minutes = self._timeframe_to_minutes(timeframe)
        if interval_minutes is None:
            return # Invalid timeframe

        # Determine the start of the current candle interval
        # Example: For M5, if tick is 10:03:30, candle starts at 10:00:00
        # For H1, if tick is 10:30:00, candle starts at 10:00:00
        current_candle_start = current_tick_time.replace(
            second=0, microsecond=0
        ) - timedelta(minutes=current_tick_time.minute % interval_minutes)
        
        # If this is the first tick for this timeframe, initialize last_processed_tick_time
        if self.last_processed_tick_time[timeframe] is None:
            self.last_processed_tick_time[timeframe] = current_candle_start

        # Check if a new candle should start
        if current_candle_start > self.last_processed_tick_time[timeframe]:
            # A new candle interval has begun, finalize the previous candle
            if self.current_candles[timeframe] is not None:
                self.current_candles[timeframe]['time_close'] = self.last_processed_tick_time[timeframe] + timedelta(minutes=interval_minutes) - timedelta(microseconds=1)
                # Here you would typically emit the finalized candle
                # For now, we'll just print it or store it
                # print(f"Finalized {timeframe} candle: {self.current_candles[timeframe]}")
            
            # Start a new candle
            self.current_candles[timeframe] = {
                'time': current_candle_start,
                'open': None,
                'high': -float('inf'),
                'low': float('inf'),
                'close': None,
                'volume': 0 # Volume is not directly available from ticks, can be simulated or ignored
            }
            self.last_processed_tick_time[timeframe] = current_candle_start
            
        # Update the current candle with the latest tick
        if self.current_candles[timeframe] is not None:
            # Use mid-price for OHLC
            mid_price = (self.buffers[timeframe][-1]['bid'] + self.buffers[timeframe][-1]['ask']) / 2
            
            if self.current_candles[timeframe]['open'] is None:
                self.current_candles[timeframe]['open'] = mid_price
            self.current_candles[timeframe]['high'] = max(self.current_candles[timeframe]['high'], mid_price)
            self.current_candles[timeframe]['low'] = min(self.current_candles[timeframe]['low'], mid_price)
            self.current_candles[timeframe]['close'] = mid_price
            self.current_candles[timeframe]['volume'] += 1 # Simple tick count as volume

    def get_current_candle(self, timeframe: str) -> Optional[Dict]:
        """
        Returns the currently forming candle for a given timeframe.
        """
        return self.current_candles.get(timeframe)

    def _timeframe_to_minutes(self, timeframe: str) -> Optional[int]:
        """Converts a timeframe string to minutes."""
        tf_map = {
            "M1": 1, "1m": 1, "1M": 1,
            "M5": 5, "5m": 5, "5M": 5,
            "M15": 15, "15m": 15, "15M": 15,
            "M30": 30, "30m": 30, "30M": 30,
            "H1": 60, "1h": 60, "1H": 60,
            "H4": 240, "4h": 240, "4H": 240,
            "D1": 1440, "1d": 1440, "1D": 1440, "d": 1440
        }
        return tf_map.get(timeframe.upper())

# Example Usage (for testing)
if __name__ == "__main__":
    builder = RealtimeCandleBuilder(timeframes=["M1", "M5"])
    
    # Simulate ticks
    base_time = datetime(2025, 1, 1, 9, 59, 50, tzinfo=pytz.utc)
    bratislava_tz = pytz.timezone('Europe/Bratislava')

    # Tick 1: 09:59:50 UTC -> 10:59:50 Bratislava
    tick1_time = base_time
    builder.add_tick({'time': tick1_time, 'bid': 1.1000, 'ask': 1.1005})
    print(f"Tick 1 ({tick1_time.astimezone(bratislava_tz)}): M1 Candle: {builder.get_current_candle('M1')}")
    print(f"Tick 1 ({tick1_time.astimezone(bratislava_tz)}): M5 Candle: {builder.get_current_candle('M5')}")

    # Tick 2: 10:00:05 UTC -> 11:00:05 Bratislava (New M1 candle, still same M5 candle)
    tick2_time = base_time + timedelta(minutes=1, seconds=15)
    builder.add_tick({'time': tick2_time, 'bid': 1.1010, 'ask': 1.1015})
    print(f"Tick 2 ({tick2_time.astimezone(bratislava_tz)}): M1 Candle: {builder.get_current_candle('M1')}")
    print(f"Tick 2 ({tick2_time.astimezone(bratislava_tz)}): M5 Candle: {builder.get_current_candle('M5')}")

    # Tick 3: 10:00:30 UTC -> 11:00:30 Bratislava
    tick3_time = base_time + timedelta(minutes=1, seconds=40)
    builder.add_tick({'time': tick3_time, 'bid': 1.1008, 'ask': 1.1013})
    print(f"Tick 3 ({tick3_time.astimezone(bratislava_tz)}): M1 Candle: {builder.get_current_candle('M1')}")
    print(f"Tick 3 ({tick3_time.astimezone(bratislava_tz)}): M5 Candle: {builder.get_current_candle('M5')}")

    # Tick 4: 10:05:00 UTC -> 11:05:00 Bratislava (New M5 candle)
    tick4_time = base_time + timedelta(minutes=5, seconds=10)
    builder.add_tick({'time': tick4_time, 'bid': 1.1020, 'ask': 1.1025})
    print(f"Tick 4 ({tick4_time.astimezone(bratislava_tz)}): M1 Candle: {builder.get_current_candle('M1')}")
    print(f"Tick 4 ({tick4_time.astimezone(bratislava_tz)}): M5 Candle: {builder.get_current_candle('M5')}")
