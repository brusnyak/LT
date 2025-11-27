"""
Session-based price action analysis module
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, time, timedelta
import pytz

logger = logging.getLogger(__name__)

class SessionAnalyzer:
    """
    Analyzer for session-based price action patterns
    """
    
    def __init__(self):
        """Initialize the session analyzer"""
        # Define session times in UTC
        self.sessions = {
            'asia': {
                'start': time(22, 0),  # 22:00 UTC (00:00 Tokyo)
                'end': time(7, 0)      # 07:00 UTC (09:00 Tokyo)
            },
            'london': {
                'start': time(7, 0),   # 07:00 UTC (08:00 London)
                'end': time(15, 0)     # 15:00 UTC (16:00 London)
            },
            'newyork': {
                'start': time(13, 0),  # 13:00 UTC (08:00 New York)
                'end': time(21, 0)     # 21:00 UTC (16:00 New York)
            }
        }
    
    def _ensure_datetime_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure the dataframe has a datetime index
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Dataframe with datetime index
        """
        # Make a copy to avoid modifying the original
        result_df = df.copy()
        
        # Check if already has datetime index
        if isinstance(result_df.index, pd.DatetimeIndex):
            return result_df
        
        # Try to convert from columns
        if 'datetime' in result_df.columns:
            result_df.set_index('datetime', inplace=True)
            return result_df
        elif 'date' in result_df.columns:
            result_df.set_index('date', inplace=True)
            if not isinstance(result_df.index, pd.DatetimeIndex):
                result_df.index = pd.to_datetime(result_df.index)
            return result_df
        
        # If no datetime column, try to infer from index
        try:
            result_df.index = pd.to_datetime(result_df.index)
            return result_df
        except:
            logger.warning("Could not convert index to datetime")
            return result_df

    def identify_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify which session each candle belongs to
        
        Args:
            df (pd.DataFrame): OHLCV dataframe with datetime index
            
        Returns:
            pd.DataFrame: DataFrame with session columns added
        """
        # Ensure the dataframe has a datetime index
        result_df = self._ensure_datetime_index(df)
        
        # Ensure the index is datetime
        if not isinstance(result_df.index, pd.DatetimeIndex):
            logger.warning("DataFrame index is not DatetimeIndex, cannot identify sessions")
            return result_df
        
        # Convert index to UTC if it has timezone info
        if result_df.index.tz is not None:
            utc_index = result_df.index.tz_convert('UTC')
        else:
            # Assume UTC if no timezone info
            utc_index = result_df.index
        
        # Initialize session columns
        result_df['asia_session'] = False
        result_df['london_session'] = False
        result_df['newyork_session'] = False
        
        # Identify sessions for each candle
        for i, timestamp in enumerate(utc_index):
            hour = timestamp.hour
            minute = timestamp.minute
            current_time = time(hour, minute)
            
            # Check Asia session (crosses midnight)
            if self.sessions['asia']['start'] <= current_time or current_time < self.sessions['asia']['end']:
                result_df.iloc[i, result_df.columns.get_loc('asia_session')] = True
            
            # Check London session
            if self.sessions['london']['start'] <= current_time < self.sessions['london']['end']:
                result_df.iloc[i, result_df.columns.get_loc('london_session')] = True
            
            # Check New York session
            if self.sessions['newyork']['start'] <= current_time < self.sessions['newyork']['end']:
                result_df.iloc[i, result_df.columns.get_loc('newyork_session')] = True
        
        return result_df
    
    def analyze_session_price_action(self, df: pd.DataFrame) -> Dict:
        """
        Analyze price action during different trading sessions
        
        Args:
            df (pd.DataFrame): OHLCV dataframe with session columns
            
        Returns:
            dict: Session price action analysis
        """
        # Add session information if not already present
        if 'asia_session' not in df.columns:
            df = self.identify_sessions(df)
        
        # Group candles by session
        asia_candles = df[df['asia_session']].copy()
        london_candles = df[df['london_session']].copy()
        newyork_candles = df[df['newyork_session']].copy()
        
        # Analyze each session
        asia_analysis = self._analyze_single_session(asia_candles, 'asia')
        london_analysis = self._analyze_single_session(london_candles, 'london')
        newyork_analysis = self._analyze_single_session(newyork_candles, 'newyork')
        
        # Analyze relationships between sessions
        session_relationships = self._analyze_session_relationships(asia_candles, london_candles, newyork_candles)
        
        return {
            'asia': asia_analysis,
            'london': london_analysis,
            'newyork': newyork_analysis,
            'relationships': session_relationships
        }
    
    def _analyze_single_session(self, session_df: pd.DataFrame, session_name: str) -> Dict:
        """
        Analyze price action for a single session
        
        Args:
            session_df (pd.DataFrame): OHLCV dataframe for the session
            session_name (str): Session name
            
        Returns:
            dict: Session analysis
        """
        if session_df.empty:
            return {
                'bias': 'neutral',
                'strength': 0,
                'range': 0,
                'volatility': 0
            }
        
        # Group by date to get daily sessions
        if 'date' not in session_df.columns:
            if isinstance(session_df.index, pd.DatetimeIndex):
                session_df = session_df.copy()  # Create a copy to avoid modifying the original
                session_df['date'] = session_df.index.date
            else:
                # Try to extract date from the first column if it's a string
                try:
                    session_df['date'] = pd.to_datetime(session_df.iloc[:, 0]).dt.date
                except:
                    # Create a dummy date column
                    session_df['date'] = range(len(session_df))
        
        # Calculate session statistics
        daily_sessions = []
        
        for date, group in session_df.groupby('date'):
            if len(group) < 2:
                continue
                
            session_high = group['high'].max()
            session_low = group['low'].min()
            session_open = group.iloc[0]['open']
            session_close = group.iloc[-1]['close']
            session_range = session_high - session_low
            session_body = abs(session_close - session_open)
            
            # Determine session bias
            if session_close > session_open:
                bias = 'bullish'
            elif session_close < session_open:
                bias = 'bearish'
            else:
                bias = 'neutral'
            
            # Calculate session strength
            if session_range > 0:
                strength = (session_body / session_range) * 100
            else:
                strength = 0
            
            daily_sessions.append({
                'date': date,
                'open': session_open,
                'high': session_high,
                'low': session_low,
                'close': session_close,
                'range': session_range,
                'body': session_body,
                'bias': bias,
                'strength': strength
            })
        
        if not daily_sessions:
            return {
                'bias': 'neutral',
                'strength': 0,
                'range': 0,
                'volatility': 0
            }
        
        # Calculate overall session statistics
        recent_sessions = daily_sessions[-5:]  # Last 5 sessions
        
        bullish_count = sum(1 for s in recent_sessions if s['bias'] == 'bullish')
        bearish_count = sum(1 for s in recent_sessions if s['bias'] == 'bearish')
        
        # Determine overall bias
        if bullish_count > bearish_count:
            overall_bias = 'bullish'
            bias_strength = (bullish_count / len(recent_sessions)) * 100
        elif bearish_count > bullish_count:
            overall_bias = 'bearish'
            bias_strength = (bearish_count / len(recent_sessions)) * 100
        else:
            overall_bias = 'neutral'
            bias_strength = 50
        
        # Calculate average range and volatility
        avg_range = sum(s['range'] for s in recent_sessions) / len(recent_sessions)
        avg_body = sum(s['body'] for s in recent_sessions) / len(recent_sessions)
        
        # Calculate volatility as standard deviation of ranges
        if len(recent_sessions) > 1:
            volatility = np.std([s['range'] for s in recent_sessions])
        else:
            volatility = 0
        
        return {
            'bias': overall_bias,
            'strength': bias_strength,
            'range': avg_range,
            'body': avg_body,
            'volatility': volatility,
            'daily_sessions': recent_sessions
        }

    def _analyze_session_relationships(self, asia_df: pd.DataFrame, london_df: pd.DataFrame, newyork_df: pd.DataFrame) -> Dict:
        """
        Analyze relationships between different sessions
        
        Args:
            asia_df (pd.DataFrame): Asia session candles
            london_df (pd.DataFrame): London session candles
            newyork_df (pd.DataFrame): New York session candles
            
        Returns:
            dict: Session relationship analysis
        """
        relationships = {}
        
        # Group by date
        if 'date' not in asia_df.columns and not asia_df.empty:
            if isinstance(asia_df.index, pd.DatetimeIndex):
                asia_df = asia_df.copy()
                asia_df['date'] = asia_df.index.date
        
        if 'date' not in london_df.columns and not london_df.empty:
            if isinstance(london_df.index, pd.DatetimeIndex):
                london_df = london_df.copy()
                london_df['date'] = london_df.index.date
        
        if 'date' not in newyork_df.columns and not newyork_df.empty:
            if isinstance(newyork_df.index, pd.DatetimeIndex):
                newyork_df = newyork_df.copy()
                newyork_df['date'] = newyork_df.index.date
        
        # Get common dates
        asia_dates = set(asia_df['date']) if not asia_df.empty and 'date' in asia_df.columns else set()
        london_dates = set(london_df['date']) if not london_df.empty and 'date' in london_df.columns else set()
        newyork_dates = set(newyork_df['date']) if not newyork_df.empty and 'date' in newyork_df.columns else set()
        
        common_dates = asia_dates.intersection(london_dates).intersection(newyork_dates)
        
        # Analyze Asia to London relationship
        asia_to_london = []
        
        for date in common_dates:
            asia_session = asia_df[asia_df['date'] == date]
            london_session = london_df[london_df['date'] == date]
            
            if asia_session.empty or london_session.empty:
                continue
            
            asia_high = asia_session['high'].max()
            asia_low = asia_session['low'].min()
            asia_close = asia_session.iloc[-1]['close']
            
            london_open = london_session.iloc[0]['open']
            london_high = london_session['high'].max()
            london_low = london_session['low'].min()
            london_close = london_session.iloc[-1]['close']
            
            # Check if London broke above Asia high
            broke_above_asia = london_high > asia_high
            
            # Check if London broke below Asia low
            broke_below_asia = london_low < asia_low
            
            # Determine relationship
            if london_close > asia_close:
                relationship = 'bullish'
            elif london_close < asia_close:
                relationship = 'bearish'
            else:
                relationship = 'neutral'
            
            asia_to_london.append({
                'date': date,
                'relationship': relationship,
                'broke_above_asia': broke_above_asia,
                'broke_below_asia': broke_below_asia
            })
        
        # Analyze London to New York relationship
        london_to_newyork = []
        
        for date in common_dates:
            london_session = london_df[london_df['date'] == date]
            newyork_session = newyork_df[newyork_df['date'] == date]
            
            if london_session.empty or newyork_session.empty:
                continue
            
            london_high = london_session['high'].max()
            london_low = london_session['low'].min()
            london_close = london_session.iloc[-1]['close']
            
            newyork_open = newyork_session.iloc[0]['open']
            newyork_high = newyork_session['high'].max()
            newyork_low = newyork_session['low'].min()
            newyork_close = newyork_session.iloc[-1]['close']
            
            # Check if New York broke above London high
            broke_above_london = newyork_high > london_high
            
            # Check if New York broke below London low
            broke_below_london = newyork_low < london_low
            
            # Determine relationship
            if newyork_close > london_close:
                relationship = 'bullish'
            elif newyork_close < london_close:
                relationship = 'bearish'
            else:
                relationship = 'neutral'
            
            # Check for reversal at New York open
            if london_close > london_session.iloc[0]['open'] and newyork_close < newyork_open:
                reversal = 'bearish'
            elif london_close < london_session.iloc[0]['open'] and newyork_close > newyork_open:
                reversal = 'bullish'
            else:
                reversal = None
            
            london_to_newyork.append({
                'date': date,
                'relationship': relationship,
                'broke_above_london': broke_above_london,
                'broke_below_london': broke_below_london,
                'reversal': reversal
            })
        
        relationships['asia_to_london'] = asia_to_london
        relationships['london_to_newyork'] = london_to_newyork
        
        return relationships

    def identify_classic_buy_sell_day(self, df: pd.DataFrame) -> List[Dict]:
        """
        Identify Classic Buy/Sell Day patterns
        
        Args:
            df (pd.DataFrame): OHLCV dataframe with session columns
            
        Returns:
            list: Classic Buy/Sell Day patterns
        """
        # Add session information if not already present
        if 'asia_session' not in df.columns:
            df = self.identify_sessions(df)
        
        # Ensure we have a date column
        if 'date' not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.copy()  # Create a copy to avoid modifying the original
                df['date'] = df.index.date
            else:
                logger.warning("DataFrame does not have DatetimeIndex and no 'date' column, cannot identify classic patterns")
                return []
        
        # Analyze session relationships
        session_analysis = self.analyze_session_price_action(df)
        relationships = session_analysis['relationships']
        
        # Find Classic Buy/Sell Day patterns
        patterns = []
        
        # Check London to New York relationships
        for london_ny in relationships.get('london_to_newyork', []):
            date = london_ny['date']
            
            # Find corresponding Asia to London relationship
            asia_london = next((r for r in relationships.get('asia_to_london', []) if r['date'] == date), None)
            
            if not asia_london:
                continue
            
            # Classic Buy Day: Asia consolidation or down, London reversal up, New York continuation
            if (asia_london['relationship'] in ['bearish', 'neutral'] and 
                london_ny['relationship'] == 'bullish'):
                
                # Get the day's data
                day_data = df[df['date'] == date]
                
                if day_data.empty:
                    continue
                
                # Get session data
                asia_data = day_data[day_data['asia_session']]
                london_data = day_data[day_data['london_session']]
                ny_data = day_data[day_data['newyork_session']]
                
                if asia_data.empty or london_data.empty or ny_data.empty:
                    continue
                
                # Calculate key levels
                asia_high = asia_data['high'].max()
                asia_low = asia_data['low'].min()
                london_high = london_data['high'].max()
                london_low = london_data['low'].min()
                
                # Check if London broke above Asia high (bullish sign)
                if london_high > asia_high:
                    # Check if New York continued the bullish move
                    if london_ny['relationship'] == 'bullish':
                        patterns.append({
                            'date': date,
                            'type': 'classic_buy_day',
                            'strength': 80,  # High probability setup
                            'entry': london_high,  # Entry above London high
                            'stop_loss': london_low,  # Stop below London low
                            'take_profit': london_high + (london_high - london_low) * 2,  # 2:1 risk-reward
                            'description': 'Classic Buy Day: Asia down/consolidation, London breaks higher, NY continuation'
                        })
            
            # Classic Sell Day: Asia consolidation or up, London reversal down, New York continuation
            elif (asia_london['relationship'] in ['bullish', 'neutral'] and 
                london_ny['relationship'] == 'bearish'):
                
                # Get the day's data
                day_data = df[df['date'] == date]
                
                if day_data.empty:
                    continue
                
                # Get session data
                asia_data = day_data[day_data['asia_session']]
                london_data = day_data[day_data['london_session']]
                ny_data = day_data[day_data['newyork_session']]
                
                if asia_data.empty or london_data.empty or ny_data.empty:
                    continue
                
                # Calculate key levels
                asia_high = asia_data['high'].max()
                asia_low = asia_data['low'].min()
                london_high = london_data['high'].max()
                london_low = london_data['low'].min()
                
                # Check if London broke below Asia low (bearish sign)
                if london_low < asia_low:
                    # Check if New York continued the bearish move
                    if london_ny['relationship'] == 'bearish':
                        patterns.append({
                            'date': date,
                            'type': 'classic_sell_day',
                            'strength': 80,  # High probability setup
                            'entry': london_low,  # Entry below London low
                            'stop_loss': london_high,  # Stop above London high
                            'take_profit': london_low - (london_high - london_low) * 2,  # 2:1 risk-reward
                            'description': 'Classic Sell Day: Asia up/consolidation, London breaks lower, NY continuation'
                        })
        
        return patterns

    def identify_london_swing_to_ny_reversal(self, df: pd.DataFrame) -> List[Dict]:
        """
        Identify London Swing to NY Reversal patterns
        
        Args:
            df (pd.DataFrame): OHLCV dataframe with session columns
            
        Returns:
            list: London Swing to NY Reversal patterns
        """
        # Add session information if not already present
        if 'asia_session' not in df.columns:
            df = self.identify_sessions(df)
        
        # Ensure we have a date column
        if 'date' not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.copy()  # Create a copy to avoid modifying the original
                df['date'] = df.index.date
            else:
                logger.warning("DataFrame does not have DatetimeIndex and no 'date' column, cannot identify reversal patterns")
                return []
        
        # Analyze session relationships
        session_analysis = self.analyze_session_price_action(df)
        relationships = session_analysis['relationships']
        
        # Find London Swing to NY Reversal patterns
        patterns = []
        
        # Check London to New York relationships
        for london_ny in relationships.get('london_to_newyork', []):
            date = london_ny['date']
            
            # Check for reversal at New York open
            if london_ny['reversal'] is not None:
                # Get the day's data
                day_data = df[df['date'] == date]
                
                if day_data.empty:
                    continue
                
                # Get session data
                london_data = day_data[day_data['london_session']]
                ny_data = day_data[day_data['newyork_session']]
                
                if london_data.empty or ny_data.empty:
                    continue
                
                # Calculate key levels
                london_high = london_data['high'].max()
                london_low = london_data['low'].min()
                london_close = london_data.iloc[-1]['close']
                
                ny_open = ny_data.iloc[0]['open']
                ny_high = ny_data['high'].max()
                ny_low = ny_data['low'].min()
                
                # Bullish NY Reversal: London down, NY reverses up
                if london_ny['reversal'] == 'bullish':
                    # Entry above first NY candle high
                    entry = ny_data.iloc[0]['high']
                    # Stop below first NY candle low
                    stop_loss = ny_data.iloc[0]['low']
                    # Take profit at 2:1 risk-reward
                    take_profit = entry + (entry - stop_loss) * 2
                    
                    patterns.append({
                        'date': date,
                        'type': 'london_swing_ny_reversal_buy',
                        'strength': 75,  # High probability setup
                        'entry': entry,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'description': 'London Swing to NY Reversal (Buy): London down, NY reverses up'
                    })
                
                # Bearish NY Reversal: London up, NY reverses down
                elif london_ny['reversal'] == 'bearish':
                    # Entry below first NY candle low
                    entry = ny_data.iloc[0]['low']
                    # Stop above first NY candle high
                    stop_loss = ny_data.iloc[0]['high']
                    # Take profit at 2:1 risk-reward
                    take_profit = entry - (stop_loss - entry) * 2
                    
                    patterns.append({
                        'date': date,
                        'type': 'london_swing_ny_reversal_sell',
                        'strength': 75,  # High probability setup
                        'entry': entry,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'description': 'London Swing to NY Reversal (Sell): London up, NY reverses down'
                    })
        
        return patterns

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Analyze sessions in the provided data
        
        Args:
            df (pd.DataFrame): OHLCV dataframe
            
        Returns:
            dict: Session analysis results
        """
        try:
            # Identify sessions
            df_with_sessions = self.identify_sessions(df)
            
            # Analyze session price action
            session_analysis = self.analyze_session_price_action(df_with_sessions)
            
            # Identify classic patterns
            classic_patterns = self.identify_classic_buy_sell_day(df_with_sessions)
            
            # Identify reversal patterns
            reversal_patterns = self.identify_london_swing_to_ny_reversal(df_with_sessions)
            
            # Combine results
            result = {
                'session_analysis': session_analysis,
                'classic_patterns': classic_patterns,
                'reversal_patterns': reversal_patterns,
                'in_kill_zone': False,  # Default value
                'active_kill_zone': None  # Default value
            }
            
            # Check if current time is in a kill zone
            in_kill_zone, active_kill_zone = self._check_kill_zone(df)
            result['in_kill_zone'] = in_kill_zone
            result['active_kill_zone'] = active_kill_zone
            
            return result
            
        except Exception as e:
            logger.error(f"Error in session analysis: {e}", exc_info=True)
            return {
                'error': str(e),
                'session_analysis': {},
                'classic_patterns': [],
                'reversal_patterns': [],
                'in_kill_zone': False,
                'active_kill_zone': None
            }

    def analyze_with_mtf_context(self, 
                                symbol: str,
                                higher_tf_data: pd.DataFrame,
                                middle_tf_data: pd.DataFrame,
                                lower_tf_data: pd.DataFrame,
                                higher_tf: str = 'H4',
                                middle_tf: str = 'H1',
                                lower_tf: str = 'M5') -> Dict:
        """
        Analyze sessions with multi-timeframe context
        
        Args:
            symbol (str): Trading symbol
            higher_tf_data (pd.DataFrame): Higher timeframe data
            middle_tf_data (pd.DataFrame): Middle timeframe data
            lower_tf_data (pd.DataFrame): Lower timeframe data
            higher_tf (str): Higher timeframe
            middle_tf (str): Middle timeframe
            lower_tf (str): Lower timeframe
            
        Returns:
            dict: Analysis results
        """
        try:
            # Add session information to the lower timeframe data
            session_data = self.identify_sessions(lower_tf_data)
            
            # Check if we're in a kill zone
            in_kill_zone, active_kill_zone = self._check_kill_zone(session_data)
            
            # Analyze session-specific patterns
            session_analysis = self.analyze_session_price_action(session_data)
            
            # Look for Classic Buy/Sell Day patterns
            classic_patterns = self.identify_classic_buy_sell_day(session_data)
            
            # Look for London Swing to NY Reversal patterns
            reversal_patterns = self.identify_london_swing_to_ny_reversal(session_data)
            
            # Analyze Daily Open price action
            daily_open_analysis = self._analyze_daily_open(session_data)
            
            # Get higher timeframe bias
            htf_bias = self._determine_htf_bias(higher_tf_data)
            
            # Get middle timeframe structure
            mtf_structure = self._analyze_mtf_structure(middle_tf_data)
            
            # Combine all analysis
            combined_analysis = {
                'symbol': symbol,
                'higher_tf': higher_tf,
                'middle_tf': middle_tf,
                'lower_tf': lower_tf,
                'htf_bias': htf_bias,
                'mtf_structure': mtf_structure,
                'session_analysis': session_analysis,
                'classic_patterns': classic_patterns,
                'reversal_patterns': reversal_patterns,
                'daily_open_analysis': daily_open_analysis,
                'in_kill_zone': in_kill_zone,
                'active_kill_zone': active_kill_zone
            }
            
            # Generate trade signals based on combined analysis
            trade_signals = self._generate_trade_signals(combined_analysis, symbol)
            combined_analysis['trade_signals'] = trade_signals
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error in session analysis with MTF context: {e}", exc_info=True)
            return {
                'error': str(e),
                'symbol': symbol
            }

    def _check_kill_zone(self, df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """
        Check if current time is in a kill zone
        
        Args:
            df (pd.DataFrame): Price data with datetime index
            
        Returns:
            tuple: (in_kill_zone, active_kill_zone)
        """
        # Define kill zones (high-probability trading windows)
        kill_zones = {
            'london_open': {
                'start': time(7, 0),  # 07:00 UTC (08:00 London)
                'end': time(9, 0)     # 09:00 UTC (10:00 London)
            },
            'new_york_open': {
                'start': time(13, 0),  # 13:00 UTC (08:00 New York)
                'end': time(15, 0)     # 15:00 UTC (10:00 New York)
            },
            'london_new_york_overlap': {
                'start': time(13, 0),  # 13:00 UTC (08:00 New York)
                'end': time(16, 0)     # 16:00 UTC (11:00 New York)
            }
        }
        
        # Get current time in UTC
        now = datetime.now(pytz.UTC).time()
        
        # Check each kill zone
        for zone_name, zone_times in kill_zones.items():
            start_time = zone_times['start']
            end_time = zone_times['end']
            
            # Check if current time is in this kill zone
            if start_time <= now <= end_time:
                return True, zone_name
        
        return False, None

    def _analyze_daily_open(self, df: pd.DataFrame) -> Dict:
        """
        Analyze price action around the daily open
        
        Args:
            df (pd.DataFrame): Price data with datetime index
            
        Returns:
            dict: Daily open analysis
        """
        daily_open_analysis = {}
        
        try:
            # Ensure we have datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                logger.warning("DataFrame does not have DatetimeIndex, cannot analyze daily open")
                return daily_open_analysis
            
            # Group by date to get daily sessions
            df['date'] = df.index.date
            daily_groups = df.groupby('date')
            
            # Analyze each day's open
            daily_opens = []
            
            for date, group in daily_groups:
                # Get the first candle of the day
                first_candle = group.iloc[0]
                daily_open = first_candle['open']
                
                # Get the next 12 candles (approximately 1 hour for 5-minute data)
                initial_period = group.iloc[:12] if len(group) >= 12 else group
                
                # Calculate high, low, and close of initial period
                period_high = initial_period['high'].max()
                period_low = initial_period['low'].min()
                period_close = initial_period.iloc[-1]['close']
                
                # Determine if price moved away from daily open
                if period_close > daily_open:
                    direction = 'bullish'
                    move_away = (period_close - daily_open) / daily_open * 100
                elif period_close < daily_open:
                    direction = 'bearish'
                    move_away = (daily_open - period_close) / daily_open * 100
                else:
                    direction = 'neutral'
                    move_away = 0
                
                # Check if price returned to daily open later in the day
                rest_of_day = group.iloc[12:] if len(group) >= 12 else pd.DataFrame()
                returned_to_open = False
                
                if not rest_of_day.empty:
                    if direction == 'bullish':
                        # Check if price came back down to daily open
                        returned_to_open = (rest_of_day['low'] <= daily_open).any()
                    elif direction == 'bearish':
                        # Check if price came back up to daily open
                        returned_to_open = (rest_of_day['high'] >= daily_open).any()
                
                daily_opens.append({
                    'date': date,
                    'daily_open': daily_open,
                    'direction': direction,
                    'move_away': move_away,
                    'returned_to_open': returned_to_open
                })
            
            # Get the most recent daily open
            if daily_opens:
                recent_daily_open = daily_opens[-1]
                
                # Check if current price is near daily open
                current_price = df.iloc[-1]['close']
                daily_open = recent_daily_open['daily_open']
                
                # Calculate percentage difference
                pct_diff = abs(current_price - daily_open) / daily_open * 100
                near_daily_open = pct_diff < 0.1  # Within 0.1% of daily open
                
                daily_open_analysis = {
                    'recent_daily_open': recent_daily_open,
                    'current_near_daily_open': near_daily_open,
                    'daily_open_value': daily_open,
                    'daily_opens': daily_opens[-5:]  # Last 5 days
                }
            
            return daily_open_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing daily open: {e}", exc_info=True)
            return {}

    def _determine_htf_bias(self, df: pd.DataFrame) -> Dict:
        """
        Determine higher timeframe bias
        
        Args:
            df (pd.DataFrame): Higher timeframe data
            
        Returns:
            dict: Higher timeframe bias
        """
        try:
            if df is None or df.empty:
                return {'direction': 'neutral', 'confidence': 0}
            
            # Calculate EMAs
            ema20 = df['close'].ewm(span=20, adjust=False).mean()
            ema50 = df['close'].ewm(span=50, adjust=False).mean()
            ema200 = df['close'].ewm(span=200, adjust=False).mean()
            
            # Get the most recent values
            last_ema20 = ema20.iloc[-1]
            last_ema50 = ema50.iloc[-1]
            last_ema200 = ema200.iloc[-1]
            
            # Determine trend direction
            if last_ema20 > last_ema50 > last_ema200:
                direction = 'bullish'
                # Calculate confidence based on separation of EMAs
                separation = (last_ema20 - last_ema200) / last_ema200 * 100
                confidence = min(90, int(separation * 10))
            elif last_ema20 < last_ema50 < last_ema200:
                direction = 'bearish'
                # Calculate confidence based on separation of EMAs
                separation = (last_ema200 - last_ema20) / last_ema200 * 100
                confidence = min(90, int(separation * 10))
            else:
                # Mixed signals
                if last_ema20 > last_ema50:
                    direction = 'bullish'
                    confidence = 60
                elif last_ema20 < last_ema50:
                    direction = 'bearish'
                    confidence = 60
                else:
                    direction = 'neutral'
                    confidence = 50
            
            # Check recent price action to confirm bias
            recent_candles = df.tail(5)
            bullish_candles = sum(1 for i in range(len(recent_candles)) if recent_candles.iloc[i]['close'] > recent_candles.iloc[i]['open'])
            bearish_candles = sum(1 for i in range(len(recent_candles)) if recent_candles.iloc[i]['close'] < recent_candles.iloc[i]['open'])
            
            # Adjust confidence based on recent price action
            if direction == 'bullish' and bullish_candles > bearish_candles:
                confidence += 10
            elif direction == 'bearish' and bearish_candles > bullish_candles:
                confidence += 10
            elif direction == 'bullish' and bearish_candles > bullish_candles:
                confidence -= 20
            elif direction == 'bearish' and bullish_candles > bearish_candles:
                confidence -= 20
            
            # Ensure confidence is within bounds
            confidence = max(0, min(100, confidence))
            
            return {
                'direction': direction,
                'confidence': confidence,
                'ema20': last_ema20,
                'ema50': last_ema50,
                'ema200': last_ema200
            }
            
        except Exception as e:
            logger.error(f"Error determining HTF bias: {e}", exc_info=True)
            return {'direction': 'neutral', 'confidence': 0}

    def _analyze_mtf_structure(self, df: pd.DataFrame) -> Dict:
        """
        Analyze middle timeframe market structure
        
        Args:
            df (pd.DataFrame): Middle timeframe data
            
        Returns:
            dict: Market structure analysis
        """
        try:
            if df is None or df.empty:
                return {'structure': 'neutral', 'swing_points': []}
            
            # Find swing highs and lows
            swing_highs, swing_lows = self._find_swing_points(df)
            
            # Determine market structure
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                # Check for higher highs and higher lows (bullish)
                sorted_highs = sorted(swing_highs, key=lambda x: x['index'])
                sorted_lows = sorted(swing_lows, key=lambda x: x['index'])
                
                recent_highs = sorted_highs[-2:]
                recent_lows = sorted_lows[-2:]
                
                if len(recent_highs) == 2 and len(recent_lows) == 2:
                    higher_high = recent_highs[1]['price'] > recent_highs[0]['price']
                    higher_low = recent_lows[1]['price'] > recent_lows[0]['price']
                    
                    lower_high = recent_highs[1]['price'] < recent_highs[0]['price']
                    lower_low = recent_lows[1]['price'] < recent_lows[0]['price']
                    
                    if higher_high and higher_low:
                        structure = 'bullish'
                    elif lower_high and lower_low:
                        structure = 'bearish'
                    else:
                        structure = 'neutral'
                else:
                    structure = 'neutral'
            else:
                structure = 'neutral'
            
            return {
                'structure': structure,
                'swing_highs': swing_highs,
                'swing_lows': swing_lows
            }
            
        except Exception as e:
            logger.error(f"Error analyzing MTF structure: {e}", exc_info=True)
            return {'structure': 'neutral', 'swing_points': []}

    def _find_swing_points(self, df: pd.DataFrame, window: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """
        Find swing highs and lows in the price data
        
        Args:
            df (pd.DataFrame): OHLCV data
            window (int): Window size for swing point detection
            
        Returns:
            tuple: Lists of swing highs and swing lows
        """
        if df is None or len(df) < window * 2:
            return [], []
        
        swing_highs = []
        swing_lows = []
        
        # Find swing highs
        for i in range(window, len(df) - window):
            is_swing_high = True
            for j in range(1, window + 1):
                if df['high'].iloc[i] <= df['high'].iloc[i - j] or df['high'].iloc[i] <= df['high'].iloc[i + j]:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    'price': df['high'].iloc[i],
                    'index': i,
                    'datetime': df.index[i] if hasattr(df, 'index') else None
                })
        
        # Find swing lows
        for i in range(window, len(df) - window):
            is_swing_low = True
            for j in range(1, window + 1):
                if df['low'].iloc[i] >= df['low'].iloc[i - j] or df['low'].iloc[i] >= df['low'].iloc[i + j]:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    'price': df['low'].iloc[i],
                    'index': i,
                    'datetime': df.index[i] if hasattr(df, 'index') else None
                })
        
        return swing_highs, swing_lows

    def _generate_trade_signals(self, combined_analysis: Dict, symbol: str) -> List[Dict]:
        """
        Generate trade signals based on combined analysis
        
        Args:
            combined_analysis (dict): Combined analysis results
            symbol (str): Trading symbol
            
        Returns:
            list: Trade signals
        """
        signals = []
        
        try:
            # Extract key components from analysis
            htf_bias = combined_analysis.get('htf_bias', {}).get('direction', 'neutral')
            htf_confidence = combined_analysis.get('htf_bias', {}).get('confidence', 0)
            mtf_structure = combined_analysis.get('mtf_structure', {}).get('structure', 'neutral')
            session_analysis = combined_analysis.get('session_analysis', {})
            classic_patterns = combined_analysis.get('classic_patterns', [])
            reversal_patterns = combined_analysis.get('reversal_patterns', [])
            daily_open_analysis = combined_analysis.get('daily_open_analysis', {})
            in_kill_zone = combined_analysis.get('in_kill_zone', False)
            active_kill_zone = combined_analysis.get('active_kill_zone', None)
            
            # 1. Check for Classic Buy/Sell Day patterns
            for pattern in classic_patterns:
                direction = pattern.get('direction', 'neutral')
                
                # Only consider if aligned with HTF bias or very strong pattern
                if direction == htf_bias or pattern.get('strength', 0) > 80:
                    entry_price = pattern.get('entry_price')
                    stop_loss = pattern.get('stop_loss')
                    take_profit = pattern.get('take_profit')
                    
                    # Calculate dynamic risk reward
                    if entry_price and stop_loss and take_profit:
                        risk = abs(entry_price - stop_loss)
                        reward = abs(take_profit - entry_price)
                        risk_reward = reward / risk if risk != 0 else 0
                    else:
                        risk_reward = 0
                    
                    signal = {
                        'symbol': symbol,
                        'direction': direction,
                        'pattern_type': 'classic_buy_sell_day',
                        'pattern_name': pattern.get('name', 'Classic Pattern'),
                        'strength': pattern.get('strength', 70),
                        'htf_bias': htf_bias,
                        'htf_confidence': htf_confidence,
                        'mtf_structure': mtf_structure,
                        'in_kill_zone': in_kill_zone,
                        'active_kill_zone': active_kill_zone,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward': risk_reward
                    }
                    
                    # Adjust strength based on alignment with higher timeframes
                    if direction == htf_bias and direction == mtf_structure:
                        signal['strength'] += 15
                    elif direction == htf_bias:
                        signal['strength'] += 10
                    elif direction == mtf_structure:
                        signal['strength'] += 5
                    
                    # Adjust strength based on kill zone
                    if in_kill_zone:
                        signal['strength'] += 10
                    
                    signals.append(signal)
            
            # 2. Check for London Swing to NY Reversal patterns
            for pattern in reversal_patterns:
                direction = pattern.get('direction', 'neutral')
                
                # Only consider if aligned with HTF bias or very strong pattern
                if direction == htf_bias or pattern.get('strength', 0) > 80:
                    entry_price = pattern.get('entry_price')
                    stop_loss = pattern.get('stop_loss')
                    take_profit = pattern.get('take_profit')
                    
                    # Calculate dynamic risk reward
                    if entry_price and stop_loss and take_profit:
                        risk = abs(entry_price - stop_loss)
                        reward = abs(take_profit - entry_price)
                        risk_reward = reward / risk if risk != 0 else 0
                    else:
                        risk_reward = 0
                    
                    signal = {
                        'symbol': symbol,
                        'direction': direction,
                        'pattern_type': 'london_swing_to_ny_reversal',
                        'pattern_name': pattern.get('name', 'London-NY Reversal'),
                        'strength': pattern.get('strength', 75),
                        'htf_bias': htf_bias,
                        'htf_confidence': htf_confidence,
                        'mtf_structure': mtf_structure,
                        'in_kill_zone': in_kill_zone,
                        'active_kill_zone': active_kill_zone,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward': risk_reward
                    }
                    
                    # Adjust strength based on alignment with higher timeframes
                    if direction == htf_bias and direction == mtf_structure:
                        signal['strength'] += 15
                    elif direction == htf_bias:
                        signal['strength'] += 10
                    elif direction == mtf_structure:
                        signal['strength'] += 5
                    
                    # Adjust strength based on kill zone
                    if in_kill_zone and active_kill_zone == 'london_new_york_overlap':
                        signal['strength'] += 15  # Extra boost for this specific pattern in the overlap zone
                    elif in_kill_zone:
                        signal['strength'] += 10
                    
                    signals.append(signal)
            
            # 3. Check for Daily Open trades
            recent_daily_open = daily_open_analysis.get('recent_daily_open', {})
            if recent_daily_open:
                direction = recent_daily_open.get('direction', 'neutral')
                
                # Only consider if aligned with HTF bias
                if direction == htf_bias and direction != 'neutral':
                    # Check if price moved significantly from daily open
                    move_away = recent_daily_open.get('move_away', 0)
                    
                    if move_away > 0.2:  # More than 0.2% move
                        daily_open_value = daily_open_analysis.get('daily_open_value')
                        current_price = combined_analysis.get('current_price', 0)
                        
                        # Calculate entry, stop loss, and take profit
                        if direction == 'bullish':
                            entry_price = current_price
                            stop_loss = daily_open_value * 0.998  # 0.2% below daily open
                            take_profit = entry_price + (entry_price - stop_loss) * 2
                        else:  # bearish
                            entry_price = current_price
                            stop_loss = daily_open_value * 1.002  # 0.2% above daily open
                            take_profit = entry_price - (stop_loss - entry_price) * 2
                        
                        # Calculate dynamic risk reward
                        risk = abs(entry_price - stop_loss)
                        reward = abs(take_profit - entry_price)
                        risk_reward = reward / risk if risk != 0 else 0
                        
                        signal = {
                            'symbol': symbol,
                            'direction': direction,
                            'pattern_type': 'daily_open',
                            'pattern_name': 'Daily Open Momentum',
                            'strength': 65,
                            'htf_bias': htf_bias,
                            'htf_confidence': htf_confidence,
                            'mtf_structure': mtf_structure,
                            'in_kill_zone': in_kill_zone,
                            'active_kill_zone': active_kill_zone,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'risk_reward': risk_reward
                        }
                        
                        # Adjust strength based on alignment with higher timeframes
                        if direction == htf_bias and direction == mtf_structure:
                            signal['strength'] += 15
                        elif direction == htf_bias:
                            signal['strength'] += 10
                        elif direction == mtf_structure:
                            signal['strength'] += 5
                        
                        # Adjust strength based on kill zone
                        if in_kill_zone:
                            signal['strength'] += 10
                        
                        signals.append(signal)
            
            # 4. Check for session-specific patterns
            session_patterns = session_analysis.get('patterns', [])
            for pattern in session_patterns:
                direction = pattern.get('direction', 'neutral')
                pattern_type = pattern.get('type', '')
                
                # Only consider if aligned with HTF bias or very strong pattern
                if direction == htf_bias or pattern.get('strength', 0) > 80:
                    # For Asia range London breakout, we need current price
                    if pattern_type == 'asia_range_london_breakout' and in_kill_zone and active_kill_zone == 'london_open':
                        current_price = combined_analysis.get('current_price', 0)
                        
                        # Get Asia session high and low
                        asia_session = session_analysis.get('asia', {})
                        asia_high = asia_session.get('high', 0)
                        asia_low = asia_session.get('low', 0)
                        
                        # Calculate entry, stop loss, and take profit
                        if direction == 'bullish':
                            entry_price = current_price
                            stop_loss = asia_low * 0.999  # Just below Asia low
                            take_profit = entry_price + (entry_price - stop_loss) * 2
                        else:  # bearish
                            entry_price = current_price
                            stop_loss = asia_high * 1.001  # Just above Asia high
                            take_profit = entry_price - (stop_loss - entry_price) * 2
                        
                        # Calculate dynamic risk reward
                        risk = abs(entry_price - stop_loss)
                        reward = abs(take_profit - entry_price)
                        risk_reward = reward / risk if risk != 0 else 0
                        
                        signal = {
                            'symbol': symbol,
                            'direction': direction,
                            'pattern_type': pattern_type,
                            'pattern_name': 'Asia Range London Breakout',
                            'strength': pattern.get('strength', 70),
                            'htf_bias': htf_bias,
                            'htf_confidence': htf_confidence,
                            'mtf_structure': mtf_structure,
                            'in_kill_zone': in_kill_zone,
                            'active_kill_zone': active_kill_zone,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'risk_reward': risk_reward
                        }
                        
                        # Adjust strength based on alignment with higher timeframes
                        if direction == htf_bias and direction == mtf_structure:
                            signal['strength'] += 15
                        elif direction == htf_bias:
                            signal['strength'] += 10
                        elif direction == mtf_structure:
                            signal['strength'] += 5
                        
                        # Adjust strength based on kill zone
                        if in_kill_zone and active_kill_zone == 'london_open':
                            signal['strength'] += 15  # Extra boost for this specific pattern in London open
                        
                        signals.append(signal)
            
            # Sort signals by strength (descending)
            signals.sort(key=lambda x: x.get('strength', 0), reverse=True)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating trade signals: {e}", exc_info=True)
            return []