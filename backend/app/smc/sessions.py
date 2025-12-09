"""
Trading Sessions Detection and Analysis

Sessions:
- Asian Session: 00:00 - 09:00 UTC
- London Session: 08:00 - 17:00 UTC  
- New York Session: 13:00 - 22:00 UTC
- London/NY Overlap: 13:00 - 17:00 UTC (high liquidity period)
"""
from typing import Dict, Literal, Optional
from datetime import datetime, time, timedelta
import pytz
import pandas as pd
from app.models.smc import Session # Import Session model


class SessionDetector:
    """
    Detect and analyze trading sessions
    
    Sessions are defined in UTC time:
    - Asian: 00:00 - 09:00
    - London: 08:00 - 17:00
    - New York: 13:00 - 22:00
    - Overlap: 13:00 - 17:00 (London + NY)
    """
    
    # Session times in UTC
    # Session times in Europe/Bratislava (UTC+1)
    SESSIONS = {
        'morning': {'start': time(6, 0), 'end': time(10, 0)},
        'afternoon': {'start': time(13, 0), 'end': time(16, 0)},
        # Add other sessions if needed, but focus on Pine Script's definitions
        # 'london_killzone': {'start': time(9,0), 'end': time(10,0)}, # Example from classic_buy_sell.txt
        # 'ny_killzone': {'start': time(15,0), 'end': time(16,0)},
    }
    
    def __init__(self, timezone: str = 'Europe/Bratislava'):
        """
        Initialize session detector
        
        Args:
            timezone: Timezone for session detection (default: Europe/Bratislava)
        """
        self.timezone = pytz.timezone(timezone)
    
    def identify_session(self, timestamp: datetime) -> Literal['morning', 'afternoon', 'none']:
        """
        Identify which of the Pine Script defined sessions a timestamp belongs to.
        
        Args:
            timestamp: Datetime to check (assumed to be in self.timezone)
            
        Returns:
            Session name: 'morning', 'afternoon', or 'none'
        """
        # Ensure timestamp is in the correct timezone
        if timestamp.tzinfo is None:
            timestamp = self.timezone.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(self.timezone)
            
        current_time = timestamp.time()
        
        for session_name, times in self.SESSIONS.items():
            start = times['start']
            end = times['end']
            
            # Debugging: Print current time and session bounds
            # print(f"DEBUG SessionDetector: Current Time: {current_time}, Checking {session_name} (Start: {start}, End: {end})")

            # Handle overnight sessions (not applicable for current Pine Script sessions, but good practice)
            if start <= end:
                if start <= current_time <= end:
                    # print(f"DEBUG SessionDetector: {current_time} is IN {session_name}")
                    return session_name
            else: # Overnight session, e.g., 22:00 - 06:00
                if current_time >= start or current_time <= end:
                    # print(f"DEBUG SessionDetector: {current_time} is IN {session_name} (overnight)")
                    return session_name
        
        # print(f"DEBUG SessionDetector: {current_time} is NOT IN any session")
        return 'none'
    
    def _is_in_session(self, current_time: time, session_name: str) -> bool:
        """
        Check if time falls within a session (internal helper, uses self.SESSIONS)
        """
        session_times = self.SESSIONS.get(session_name)
        if not session_times:
            return False
            
        start = session_times['start']
        end = session_times['end']
        
        if start <= end:
            return start <= current_time <= end
        else: # Handles overnight sessions
            return current_time >= start or current_time <= end

    def get_current_session_data(self, df: pd.DataFrame, current_candle_index: int) -> Optional[Session]:
        """
        Gets the currently active session's data (high, low, open, close) for the current day.
        Mimics Pine Script's update_session logic.
        
        Args:
            df: OHLCV dataframe with datetime index (in self.timezone)
            current_candle_index: The index of the current candle in the dataframe.
            
        Returns:
            Session object if an active session is found, None otherwise.
        """
        if df.empty or current_candle_index < 0 or current_candle_index >= len(df):
            return None

        current_candle_time = df.index[current_candle_index]
        current_date = current_candle_time.date()

        active_session_name = self.identify_session(current_candle_time)
        
        if active_session_name == 'none':
            return None

        session_times = self.SESSIONS[active_session_name]
        session_start_time_of_day = session_times['start']
        session_end_time_of_day = session_times['end']

        # Construct the full datetime for session start and end for the current day
        session_start_dt = self.timezone.localize(datetime.combine(current_date, session_start_time_of_day))
        session_end_dt = self.timezone.localize(datetime.combine(current_date, session_end_time_of_day))

        # Handle overnight sessions if end time is before start time (e.g., Asia)
        if session_end_dt < session_start_dt:
            session_end_dt += timedelta(days=1)
            # If current time is before start time, it means we are in the *previous* day's overnight session
            if current_candle_time < session_start_dt:
                session_start_dt -= timedelta(days=1)
                session_end_dt -= timedelta(days=1)

        # Filter data for the current active session on the current day
        # Pandas between_time is inclusive of start and end by default.
        # The error indicates 'include_end' is not supported, so we rely on default or adjust.
        # For filtering with >= and <=, it's already inclusive.
        session_df = df[(df.index >= session_start_dt) & (df.index <= session_end_dt)]
        
        if session_df.empty:
            return None

        # Calculate session stats up to the current candle
        current_session_df = session_df[session_df.index <= current_candle_time]

        if current_session_df.empty:
            return None

        session_high = current_session_df['high'].max()
        session_low = current_session_df['low'].min()
        session_open = current_session_df['open'].iloc[0]
        session_close = current_session_df['close'].iloc[-1]

        return Session(
            name=active_session_name,
            start_time=session_start_dt,
            end_time=session_end_dt,
            high=session_high,
            low=session_low,
            open=session_open,
            close=session_close,
            active=True # Always active if we're returning it for the current candle
        )
    
    # Removed get_session_bounds, add_session_column, get_session_stats as they are replaced by get_current_session_data
    # Removed is_overlap, get_ny_session_times, get_london_session_times as they are not directly used by Pine Script
    
    # The original identify_session was checking against UTC, but Pine Script uses Bratislava.
    # The new identify_session checks against self.timezone (Bratislava).
    # The _is_in_session helper is now more generic.
    
    # The get_ny_session_times and get_london_session_times are not directly used in the Pine Script
    # for defining the core strategy sessions, so they can be removed or kept as utility functions
    # if needed elsewhere. For now, I'll remove them to streamline.
