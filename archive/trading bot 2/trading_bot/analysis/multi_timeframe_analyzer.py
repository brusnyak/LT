"""
Multi-timeframe analyzer module
Implements advanced multi-timeframe analysis for trading
"""

import logging
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
from datetime import datetime, time
import pytz

from trading_bot.analysis.ict_analyzer import ICTAnalyzer
from trading_bot.analysis.technical import TechnicalAnalyzer
from trading_bot.analysis.smc_analyzer import SMCAnalyzer

logger = logging.getLogger(__name__)

class MultiTimeframeAnalyzer:
    """
    Advanced multi-timeframe analyzer that combines ICT concepts
    with technical analysis across multiple timeframes
    """
    
    def __init__(self):
        """Initialize the multi-timeframe analyzer"""
        self.ict_analyzer = ICTAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.smc_analyzer = SMCAnalyzer()
    
    def analyze(self, 
        symbol: str,
        higher_tf_data: pd.DataFrame,
        middle_tf_data: pd.DataFrame,
        lower_tf_data: pd.DataFrame,
        higher_tf: str = 'H4',
        middle_tf: str = 'H1',
        lower_tf: str = 'M5',
        market_type: str = 'forex',
        current_time: Optional[datetime] = None) -> Dict:
        """
        Perform multi-timeframe analysis
        
        Args:
            symbol (str): Trading symbol
            higher_tf_data (pd.DataFrame): Higher timeframe data
            middle_tf_data (pd.DataFrame): Middle timeframe data
            lower_tf_data (pd.DataFrame): Lower timeframe data
            higher_tf (str): Higher timeframe name
            middle_tf (str): Middle timeframe name
            lower_tf (str): Lower timeframe name
            market_type (str): Market type
            current_time (datetime, optional): Current time for analysis
            
        Returns:
            dict: Multi-timeframe analysis results
        """
        try:
            logger.info(f"Performing multi-timeframe analysis for {symbol} using {higher_tf}/{middle_tf}/{lower_tf}")
            
            # Validate inputs
            if not isinstance(symbol, str):
                logger.error(f"Symbol must be a string, got {type(symbol)}")
                return {'error': f"Symbol must be a string, got {type(symbol)}"}
                
            if not isinstance(higher_tf, str):
                logger.error(f"Higher timeframe must be a string, got {type(higher_tf)}")
                return {'error': f"Higher timeframe must be a string, got {type(higher_tf)}"}
                
            if not isinstance(middle_tf, str):
                logger.error(f"Middle timeframe must be a string, got {type(middle_tf)}")
                return {'error': f"Middle timeframe must be a string, got {type(middle_tf)}"}
                
            if not isinstance(lower_tf, str):
                logger.error(f"Lower timeframe must be a string, got {type(lower_tf)}")
                return {'error': f"Lower timeframe must be a string, got {type(lower_tf)}"}
            
            # Check if we have valid data
            if higher_tf_data is None or higher_tf_data.empty:
                logger.warning(f"No higher timeframe data for {symbol} on {higher_tf}")
                return {'error': f"No higher timeframe data for {symbol} on {higher_tf}"}
            
            if middle_tf_data is None or middle_tf_data.empty:
                logger.warning(f"No middle timeframe data for {symbol} on {middle_tf}")
                return {'error': f"No middle timeframe data for {symbol} on {middle_tf}"}
            
            if lower_tf_data is None or lower_tf_data.empty:
                logger.warning(f"No lower timeframe data for {symbol} on {lower_tf}")
                return {'error': f"No lower timeframe data for {symbol} on {lower_tf}"}
            
            # Use current time or get it from the latest data point
            if current_time is None:
                try:
                    if isinstance(lower_tf_data.index, pd.DatetimeIndex):
                        current_time = lower_tf_data.index[-1].to_pydatetime()
                    else:
                        current_time = datetime.now()
                except Exception as e:
                    logger.warning(f"Error getting current time from data: {e}")
                    current_time = datetime.now()
            
            # Check if current time is in a kill zone
            in_kill_zone_time = self._is_in_kill_zone_time(current_time)
            
            # Step 1: Analyze higher timeframe for bias and key levels
            try:
                higher_tf_analysis = self._analyze_higher_timeframe(higher_tf_data, symbol, higher_tf)
            except Exception as e:
                logger.error(f"Error in higher timeframe analysis: {e}", exc_info=True)
                higher_tf_analysis = {
                    'bias': {'direction': 'neutral', 'strength': 0, 'confidence': 0},
                    'error': str(e),
                    'timeframe': higher_tf
                }
            
            # Step 2: Analyze middle timeframe for zones of interest
            try:
                # Get bias direction with error handling
                htf_bias_direction = higher_tf_analysis.get('bias', {}).get('direction', 'neutral')
                
                middle_tf_analysis = self._analyze_middle_timeframe(
                    middle_tf_data, 
                    symbol, 
                    middle_tf, 
                    htf_bias_direction
                )
            except Exception as e:
                logger.error(f"Error in middle timeframe analysis: {e}", exc_info=True)
                middle_tf_analysis = {
                    'error': str(e),
                    'zones_of_interest': [],
                    'in_kill_zone': False,
                    'timeframe': middle_tf
                }
            
            # Step 3: Analyze lower timeframe for entry opportunities
            try:
                # Get bias direction with error handling
                htf_bias_direction = higher_tf_analysis.get('bias', {}).get('direction', 'neutral')
                
                # Get zones of interest with error handling
                zones_of_interest = middle_tf_analysis.get('zones_of_interest', [])
                
                lower_tf_analysis = self._analyze_lower_timeframe(
                    lower_tf_data,
                    symbol,
                    lower_tf,
                    htf_bias_direction,
                    zones_of_interest
                )
            except Exception as e:
                logger.error(f"Error in lower timeframe analysis: {e}", exc_info=True)
                lower_tf_analysis = {
                    'error': str(e),
                    'entry_opportunities': [],
                    'in_kill_zone': False,
                    'timeframe': lower_tf
                }
            
            # Step 4: Generate trade signals
            try:
                trade_signals = self._generate_trade_signals(
                    higher_tf_analysis,
                    middle_tf_analysis,
                    lower_tf_analysis,
                    in_kill_zone_time
                )
            except Exception as e:
                logger.error(f"Error generating trade signals: {e}", exc_info=True)
                trade_signals = []
            
            # Combine all analysis
            analysis = {
                'symbol': symbol,
                'market_type': market_type,
                'timeframes': {
                    'higher': higher_tf,
                    'middle': middle_tf,
                    'lower': lower_tf
                },
                'higher_timeframe': higher_tf_analysis,
                'middle_timeframe': middle_tf_analysis,
                'lower_timeframe': lower_tf_analysis,
                'trade_signals': trade_signals,
                'overall_bias': higher_tf_analysis.get('bias', {}).get('direction', 'neutral'),
                'in_kill_zone_time': in_kill_zone_time,
                'timestamp': datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis: {e}", exc_info=True)
            return {
                'symbol': symbol,
                'error': str(e),
                'timeframes': {
                    'higher': higher_tf,
                    'middle': middle_tf,
                    'lower': lower_tf
                },
                'trade_signals': []
            }
    
    def _analyze_higher_timeframe(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Dict:
        """
        Analyze higher timeframe for bias and key levels
        
        Args:
            df (pd.DataFrame): Price data
            symbol (str): Trading symbol
            timeframe (str): Timeframe
            
        Returns:
            dict: Higher timeframe analysis
        """
        try:
            # Add technical indicators
            df_with_indicators = self.technical_analyzer.add_indicators(df)
            
            # Get market structure
            market_structure = self.ict_analyzer.analyze_market_structure(df_with_indicators)
            
            # Get key levels - Use try-except to handle potential missing method
            try:
                key_levels = self.ict_analyzer.identify_key_levels(df_with_indicators)
            except AttributeError:
                logger.warning("ICTAnalyzer missing identify_key_levels method, using SMCAnalyzer instead")
                key_levels = self.smc_analyzer.identify_key_levels(df_with_indicators)
            
            # Get SMC order blocks
            order_blocks = self.smc_analyzer.identify_order_blocks(df_with_indicators)
            
            # Get fair value gaps
            fair_value_gaps = self.smc_analyzer.identify_fair_value_gaps(df_with_indicators)
            
            # Determine market bias
            bias = self._determine_market_bias(df_with_indicators, market_structure, key_levels)
            
            # Identify points of interest (POI)
            poi = self._identify_points_of_interest(
                df_with_indicators, 
                key_levels, 
                order_blocks, 
                fair_value_gaps,
                bias.get('direction', 'neutral')
            )
            
            return {
                'bias': bias,
                'market_structure': market_structure,
                'key_levels': key_levels,
                'order_blocks': order_blocks,
                'fair_value_gaps': fair_value_gaps,
                'poi': poi,
                'timeframe': timeframe
            }
            
        except Exception as e:
            logger.error(f"Error analyzing higher timeframe: {e}", exc_info=True)
            return {
                'bias': {'direction': 'neutral', 'strength': 0, 'confidence': 0},
                'error': str(e),
                'timeframe': timeframe
            }

    def _analyze_middle_timeframe(self, df: pd.DataFrame, symbol: str, timeframe: str, htf_bias: str) -> Dict:
        """
        Analyze middle timeframe for zones of interest
        
        Args:
            df (pd.DataFrame): Price data
            symbol (str): Trading symbol
            timeframe (str): Timeframe
            htf_bias (str): Higher timeframe bias
            
        Returns:
            dict: Middle timeframe analysis
        """
        try:
            # Add technical indicators
            df_with_indicators = self.technical_analyzer.add_indicators(df)
            
            # Get market structure
            market_structure = self.ict_analyzer.analyze_market_structure(df_with_indicators)
            
            # Get liquidity levels
            liquidity_levels = self.ict_analyzer.identify_liquidity_levels(df_with_indicators)
            
            # Get SMC order blocks
            order_blocks = self.smc_analyzer.identify_order_blocks(df_with_indicators)
            
            # Get fair value gaps
            fair_value_gaps = self.smc_analyzer.identify_fair_value_gaps(df_with_indicators)
            
            # Get breaker blocks - Use try-except to handle potential missing method
            try:
                breaker_blocks = self.smc_analyzer.identify_breaker_blocks(df_with_indicators)
            except AttributeError:
                logger.warning("SMCAnalyzer missing identify_breaker_blocks method, using _identify_breaker_blocks instead")
                breaker_blocks = self.smc_analyzer._identify_breaker_blocks(df_with_indicators)
            
            # Identify zones of interest
            zones_of_interest = self._identify_zones_of_interest(
                df_with_indicators,
                liquidity_levels,
                order_blocks,
                fair_value_gaps,
                breaker_blocks,
                htf_bias
            )
            
            # Determine if current price is in a kill zone
            current_price = df['close'].iloc[-1] if len(df) > 0 else None
            in_kill_zone = self._is_in_kill_zone(current_price, zones_of_interest)
            
            return {
                'market_structure': market_structure,
                'liquidity_levels': liquidity_levels,
                'order_blocks': order_blocks,
                'fair_value_gaps': fair_value_gaps,
                'breaker_blocks': breaker_blocks,
                'zones_of_interest': zones_of_interest,
                'in_kill_zone': in_kill_zone,
                'timeframe': timeframe
            }
            
        except Exception as e:
            logger.error(f"Error analyzing middle timeframe: {e}", exc_info=True)
            return {
                'error': str(e),
                'zones_of_interest': [],
                'in_kill_zone': False,
                'timeframe': timeframe
            }

    def _analyze_lower_timeframe(self, df: pd.DataFrame, symbol: str, timeframe: str, 
                                htf_bias: str, zones_of_interest: List[Dict]) -> Dict:
        """
        Analyze lower timeframe for entry opportunities
        
        Args:
            df (pd.DataFrame): Price data
            symbol (str): Trading symbol
            timeframe (str): Timeframe
            htf_bias (str): Higher timeframe bias
            zones_of_interest (list): Zones of interest from middle timeframe
            
        Returns:
            dict: Lower timeframe analysis
        """
        try:
            # Add technical indicators
            df_with_indicators = self.technical_analyzer.add_indicators(df)
            
            # Get market structure
            market_structure = self.ict_analyzer.analyze_market_structure(df_with_indicators)
            
            # Get market shifts (BOS, CHoCH)
            market_shifts = self._identify_market_shifts(df_with_indicators)
            
            # Check if we're in a kill zone
            current_price = df['close'].iloc[-1] if len(df) > 0 else None
            in_kill_zone = self._is_in_kill_zone(current_price, zones_of_interest)
            
            # Identify entry opportunities
            entry_opportunities = self._identify_entry_opportunities(
                df_with_indicators,
                htf_bias,
                zones_of_interest,
                in_kill_zone
            )
            
            return {
                'market_structure': market_structure,
                'market_shifts': market_shifts,
                'entry_opportunities': entry_opportunities,
                'in_kill_zone': in_kill_zone,
                'timeframe': timeframe
            }
            
        except Exception as e:
            logger.error(f"Error analyzing lower timeframe: {e}", exc_info=True)
            return {
                'error': str(e),
                'entry_opportunities': [],
                'in_kill_zone': False,
                'timeframe': timeframe
            }
    
    def _determine_market_bias(self, df: pd.DataFrame, market_structure: Dict, key_levels: List[Dict]) -> Dict:
        """
        Determine market bias based on technical analysis
        
        Args:
            df (pd.DataFrame): Price data with indicators
            market_structure (dict): Market structure analysis
            key_levels (list): Key levels
            
        Returns:
            dict: Market bias
        """
        # Default bias
        bias = {
            'direction': 'neutral',
            'strength': 0,
            'confidence': 0
        }
        
        try:
            if df.empty:
                return bias
            
            # Get the current price
            current_price = df['close'].iloc[-1]
            
            # Check trend using EMAs
            ema_trend = 'neutral'
            ema_strength = 0
            
            if 'ema20' in df.columns and 'ema50' in df.columns and 'ema200' in df.columns:
                ema20 = df['ema20'].iloc[-1]
                ema50 = df['ema50'].iloc[-1]
                ema200 = df['ema200'].iloc[-1]
                
                # Check if price is above/below EMAs
                price_above_ema20 = current_price > ema20
                price_above_ema50 = current_price > ema50
                price_above_ema200 = current_price > ema200
                
                # Check if EMAs are aligned
                ema_aligned_bullish = ema20 > ema50 > ema200
                ema_aligned_bearish = ema20 < ema50 < ema200
                
                # Determine trend based on EMAs
                if price_above_ema20 and price_above_ema50 and price_above_ema200 and ema_aligned_bullish:
                    ema_trend = 'bullish'
                    ema_strength = 100
                elif price_above_ema20 and price_above_ema50 and price_above_ema200:
                    ema_trend = 'bullish'
                    ema_strength = 80
                elif price_above_ema20 and price_above_ema50:
                    ema_trend = 'bullish'
                    ema_strength = 60
                elif price_above_ema20:
                    ema_trend = 'bullish'
                    ema_strength = 40
                elif not price_above_ema20 and not price_above_ema50 and not price_above_ema200 and ema_aligned_bearish:
                    ema_trend = 'bearish'
                    ema_strength = 100
                elif not price_above_ema20 and not price_above_ema50 and not price_above_ema200:
                    ema_trend = 'bearish'
                    ema_strength = 80
                elif not price_above_ema20 and not price_above_ema50:
                    ema_trend = 'bearish'
                    ema_strength = 60
                elif not price_above_ema20:
                    ema_trend = 'bearish'
                    ema_strength = 40
                else:
                    ema_trend = 'neutral'
                    ema_strength = 20
            
            # Check market structure
            structure_trend = market_structure.get('trend', 'neutral')
            structure_strength = 0
            
            if structure_trend == 'bullish':
                # Check for higher highs and higher lows
                has_higher_highs = market_structure.get('has_higher_highs', False)
                has_higher_lows = market_structure.get('has_higher_lows', False)
                
                if has_higher_highs and has_higher_lows:
                    structure_strength = 100
                elif has_higher_highs:
                    structure_strength = 70
                elif has_higher_lows:
                    structure_strength = 50
                else:
                    structure_strength = 30
            elif structure_trend == 'bearish':
                # Check for lower highs and lower lows
                has_lower_highs = market_structure.get('has_lower_highs', False)
                has_lower_lows = market_structure.get('has_lower_lows', False)
                
                if has_lower_highs and has_lower_lows:
                    structure_strength = 100
                elif has_lower_lows:
                    structure_strength = 70
                elif has_lower_highs:
                    structure_strength = 50
                else:
                    structure_strength = 30
            
            # Check key levels
            level_bias = 'neutral'
            level_strength = 0
            
            if key_levels:
                # Count support and resistance levels
                support_levels = [level for level in key_levels if level.get('type') == 'support']
                resistance_levels = [level for level in key_levels if level.get('type') == 'resistance']
                
                # Find closest support and resistance
                closest_support = None
                closest_resistance = None
                
                for level in support_levels:
                    level_price = level.get('price', 0)
                    if level_price < current_price:
                        if closest_support is None or level_price > closest_support.get('price', 0):
                            closest_support = level
                
                for level in resistance_levels:
                    level_price = level.get('price', 0)
                    if level_price > current_price:
                        if closest_resistance is None or level_price < closest_resistance.get('price', 0):
                            closest_resistance = level
                
                # Calculate distance to closest support and resistance
                if closest_support and closest_resistance:
                    support_distance = (current_price - closest_support.get('price', 0)) / current_price
                    resistance_distance = (closest_resistance.get('price', 0) - current_price) / current_price
                    
                    # Determine bias based on relative distance
                    if support_distance < resistance_distance:
                        level_bias = 'bullish'
                        level_strength = 50 + 50 * (1 - support_distance / (support_distance + resistance_distance))
                    else:
                        level_bias = 'bearish'
                        level_strength = 50 + 50 * (1 - resistance_distance / (support_distance + resistance_distance))
            
            # Combine all factors to determine overall bias
            factors = [
                {'bias': ema_trend, 'strength': ema_strength, 'weight': 0.4},
                {'bias': structure_trend, 'strength': structure_strength, 'weight': 0.4},
                {'bias': level_bias, 'strength': level_strength, 'weight': 0.2}
            ]
            
            # Calculate weighted bias
            bullish_score = 0
            bearish_score = 0
            total_weight = 0
            
            for factor in factors:
                if factor['bias'] == 'bullish':
                    bullish_score += factor['strength'] * factor['weight']
                elif factor['bias'] == 'bearish':
                    bearish_score += factor['strength'] * factor['weight']
                total_weight += factor['weight']
            
            # Normalize scores
            if total_weight > 0:
                bullish_score /= total_weight
                bearish_score /= total_weight
            
            # Determine overall bias
            if bullish_score > bearish_score:
                bias['direction'] = 'bullish'
                bias['strength'] = bullish_score
                bias['confidence'] = (bullish_score - bearish_score) / max(1, bullish_score + bearish_score) * 100
            elif bearish_score > bullish_score:
                bias['direction'] = 'bearish'
                bias['strength'] = bearish_score
                bias['confidence'] = (bearish_score - bullish_score) / max(1, bullish_score + bearish_score) * 100
            else:
                bias['direction'] = 'neutral'
                bias['strength'] = 0
                bias['confidence'] = 0
            
            return bias
            
        except Exception as e:
            logger.error(f"Error determining market bias: {e}", exc_info=True)
            return bias
    
    def _identify_points_of_interest(self, df: pd.DataFrame, key_levels: List[Dict], 
                                    order_blocks: List[Dict], fair_value_gaps: List[Dict], 
                                    bias: str) -> List[Dict]:
        """
        Identify points of interest (POI) on higher timeframe
        
        Args:
            df (pd.DataFrame): Price data with indicators
            key_levels (list): Key levels
            order_blocks (list): Order blocks
            fair_value_gaps (list): Fair value gaps
            bias (str): Market bias
            
        Returns:
            list: Points of interest
        """
        poi = []
        
        try:
            if df.empty:
                return poi
            
            # Get the current price
            current_price = df['close'].iloc[-1]
            
            # Add key levels as POI
            for level in key_levels:
                level_type = level.get('type')
                level_price = level.get('price', 0)
                
                # Only include levels that align with bias
                if (bias == 'bullish' and level_type == 'support') or \
                   (bias == 'bearish' and level_type == 'resistance') or \
                   bias == 'neutral':
                    
                    poi.append({
                        'type': 'key_level',
                        'subtype': level_type,
                        'price': level_price,
                        'strength': level.get('strength', 50),
                        'description': f"{level_type.capitalize()} level at {level_price:.5f}"
                    })
            
            # Add order blocks as POI
            for ob in order_blocks:
                ob_type = ob.get('type')
                ob_top = ob.get('top', 0)
                ob_bottom = ob.get('bottom', 0)
                ob_middle = (ob_top + ob_bottom) / 2
                
                # Only include order blocks that align with bias
                if (bias == 'bullish' and ob_type == 'bullish') or \
                   (bias == 'bearish' and ob_type == 'bearish') or \
                   bias == 'neutral':
                    
                    poi.append({
                        'type': 'order_block',
                        'subtype': ob_type,
                        'top': ob_top,
                        'bottom': ob_bottom,
                        'middle': ob_middle,
                        'strength': ob.get('strength', 50),
                        'description': f"{ob_type.capitalize()} order block ({ob_bottom:.5f} - {ob_top:.5f})"
                    })
            
            # Add fair value gaps as POI
            for fvg in fair_value_gaps:
                fvg_type = fvg.get('type')
                fvg_top = fvg.get('top', 0)
                fvg_bottom = fvg.get('bottom', 0)
                fvg_middle = (fvg_top + fvg_bottom) / 2
                
                # Only include FVGs that align with bias
                if (bias == 'bullish' and fvg_type == 'bullish') or \
                   (bias == 'bearish' and fvg_type == 'bearish') or \
                   bias == 'neutral':
                    
                    poi.append({
                        'type': 'fair_value_gap',
                        'subtype': fvg_type,
                        'top': fvg_top,
                        'bottom': fvg_bottom,
                        'middle': fvg_middle,
                        'strength': fvg.get('strength', 50),
                        'description': f"{fvg_type.capitalize()} fair value gap ({fvg_bottom:.5f} - {fvg_top:.5f})"
                    })
            
            # Sort POI by strength (descending)
            poi.sort(key=lambda x: x.get('strength', 0), reverse=True)
            
            return poi
            
        except Exception as e:
            logger.error(f"Error identifying points of interest: {e}", exc_info=True)
            return poi
    
    def _identify_zones_of_interest(self, df: pd.DataFrame, liquidity_levels: List[Dict],
                                   order_blocks: List[Dict], fair_value_gaps: List[Dict],
                                   breaker_blocks: List[Dict], htf_bias: str) -> List[Dict]:
        """
        Identify zones of interest on middle timeframe
        
        Args:
            df (pd.DataFrame): Price data with indicators
            liquidity_levels (list): Liquidity levels
            order_blocks (list): Order blocks
            fair_value_gaps (list): Fair value gaps
            breaker_blocks (list): Breaker blocks
            htf_bias (str): Higher timeframe bias
            
        Returns:
            list: Zones of interest
        """
        zones = []
        
        try:
            if df.empty:
                return zones
            
            # Get the current price
            current_price = df['close'].iloc[-1]
            
            # Add liquidity levels as zones
            for level in liquidity_levels:
                level_type = level.get('type')
                level_price = level.get('price', 0)
                
                # Only include levels that align with bias
                if (htf_bias == 'bullish' and level_type == 'buy_side_liquidity') or \
                   (htf_bias == 'bearish' and level_type == 'sell_side_liquidity') or \
                   htf_bias == 'neutral':
                    
                    zones.append({
                        'type': 'liquidity',
                        'subtype': level_type,
                        'price': level_price,
                        'strength': level.get('strength', 50),
                        'description': level.get('description', f"Liquidity at {level_price:.5f}")
                    })
            
            # Add order blocks as zones
            for ob in order_blocks:
                ob_type = ob.get('type')
                ob_top = ob.get('top', 0)
                ob_bottom = ob.get('bottom', 0)
                ob_middle = (ob_top + ob_bottom) / 2
                
                # Only include order blocks that align with bias
                if (htf_bias == 'bullish' and ob_type == 'bullish') or \
                   (htf_bias == 'bearish' and ob_type == 'bearish') or \
                   htf_bias == 'neutral':
                    
                    zones.append({
                        'type': 'order_block',
                        'subtype': ob_type,
                        'top': ob_top,
                        'bottom': ob_bottom,
                        'middle': ob_middle,
                        'strength': ob.get('strength', 50),
                        'description': f"{ob_type.capitalize()} order block ({ob_bottom:.5f} - {ob_top:.5f})"
                    })
            
            # Add fair value gaps as zones
            for fvg in fair_value_gaps:
                fvg_type = fvg.get('type')
                fvg_top = fvg.get('top', 0)
                fvg_bottom = fvg.get('bottom', 0)
                fvg_middle = (fvg_top + fvg_bottom) / 2
                
                # Only include FVGs that align with bias
                if (htf_bias == 'bullish' and fvg_type == 'bullish') or \
                   (htf_bias == 'bearish' and fvg_type == 'bearish') or \
                   htf_bias == 'neutral':
                    
                    zones.append({
                        'type': 'fair_value_gap',
                        'subtype': fvg_type,
                        'top': fvg_top,
                        'bottom': fvg_bottom,
                        'middle': fvg_middle,
                        'strength': fvg.get('strength', 50),
                        'description': f"{fvg_type.capitalize()} fair value gap ({fvg_bottom:.5f} - {fvg_top:.5f})"
                    })
            
            # Add breaker blocks as zones (highest priority)
            for bb in breaker_blocks:
                bb_type = bb.get('type')
                bb_top = bb.get('top', 0)
                bb_bottom = bb.get('bottom', 0)
                bb_middle = (bb_top + bb_bottom) / 2
                
                # Only include breaker blocks that align with bias
                if (htf_bias == 'bullish' and bb_type == 'bullish') or \
                   (htf_bias == 'bearish' and bb_type == 'bearish') or \
                   htf_bias == 'neutral':
                    
                    zones.append({
                        'type': 'breaker_block',
                        'subtype': bb_type,
                        'top': bb_top,
                        'bottom': bb_bottom,
                        'middle': bb_middle,
                        'strength': bb.get('strength', 70),  # Breaker blocks are stronger
                        'description': f"{bb_type.capitalize()} breaker block ({bb_bottom:.5f} - {bb_top:.5f})"
                    })
            
            # Sort zones by strength (descending)
            zones.sort(key=lambda x: x.get('strength', 0), reverse=True)
            
            return zones
            
        except Exception as e:
            logger.error(f"Error identifying zones of interest: {e}", exc_info=True)
            return zones
    
    def _identify_market_shifts(self, df: pd.DataFrame) -> List[Dict]:
        """
        Identify market structure shifts (BOS, CHoCH)
        
        Args:
            df (pd.DataFrame): Price data with indicators
            
        Returns:
            list: Market structure shifts
        """
        shifts = []
        
        try:
            if df.empty or len(df) < 10:
                return shifts
            
            # Find swing highs and lows
            swing_highs, swing_lows = self._find_swing_points(df)
            
            # Identify BOS (Break of Structure)
            bos_shifts = self._identify_break_of_structure(df, swing_highs, swing_lows)
            shifts.extend(bos_shifts)
            
            # Identify CHoCH (Change of Character)
            choch_shifts = self._identify_change_of_character(df, swing_highs, swing_lows)
            shifts.extend(choch_shifts)
            
            # Sort shifts by index (most recent first)
            shifts.sort(key=lambda x: x.get('index', 0), reverse=True)
            
            return shifts
            
        except Exception as e:
            logger.error(f"Error identifying market shifts: {e}", exc_info=True)
            return shifts
    
    def _find_swing_points(self, df: pd.DataFrame, window: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """
        Find swing highs and lows in price data
        
        Args:
            df (pd.DataFrame): Price data
            window (int): Window size for swing detection
            
        Returns:
            tuple: Lists of swing highs and swing lows
        """
        swing_highs = []
        swing_lows = []
        
        try:
            if df.empty or len(df) < 2 * window + 1:
                return swing_highs, swing_lows
            
            # Find swing highs
            for i in range(window, len(df) - window):
                is_swing_high = True
                for j in range(1, window + 1):
                    if df['high'].iloc[i] <= df['high'].iloc[i - j] or df['high'].iloc[i] <= df['high'].iloc[i + j]:
                        is_swing_high = False
                        break
                
                if is_swing_high:
                    swing_highs.append({
                        'index': i,
                        'price': df['high'].iloc[i],
                        'datetime': df.index[i] if hasattr(df.index, 'date') else None
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
                        'index': i,
                        'price': df['low'].iloc[i],
                        'datetime': df.index[i] if hasattr(df.index, 'date') else None
                    })
            
            return swing_highs, swing_lows
            
        except Exception as e:
            logger.error(f"Error finding swing points: {e}", exc_info=True)
            return [], []
    
    def _identify_break_of_structure(self, df: pd.DataFrame, 
                                    swing_highs: List[Dict], 
                                    swing_lows: List[Dict]) -> List[Dict]:
        """
        Identify break of structure (BOS) events
        
        Args:
            df (pd.DataFrame): Price data
            swing_highs (list): Swing high points
            swing_lows (list): Swing low points
            
        Returns:
            list: Break of structure events
        """
        bos_events = []
        
        try:
            if df.empty or len(swing_highs) < 2 or len(swing_lows) < 2:
                return bos_events
            
            # Sort swing points by index
            sorted_highs = sorted(swing_highs, key=lambda x: x['index'])
            sorted_lows = sorted(swing_lows, key=lambda x: x['index'])
            
            # Identify bullish BOS (price breaks above previous swing high)
            for i in range(1, len(sorted_highs)):
                current_high = sorted_highs[i]
                previous_high = sorted_highs[i-1]
                
                # Find the candle that broke the previous high
                break_index = None
                for j in range(previous_high['index'] + 1, current_high['index'] + 1):
                    if j < len(df) and df['high'].iloc[j] > previous_high['price']:
                        break_index = j
                        break
                
                if break_index is not None:
                    bos_events.append({
                        'type': 'bos',
                        'direction': 'bullish',
                        'index': break_index,
                        'price': previous_high['price'],
                        'strength': 80,
                        'description': f"Bullish BOS at {previous_high['price']:.5f}"
                    })
            
            # Identify bearish BOS (price breaks below previous swing low)
            for i in range(1, len(sorted_lows)):
                current_low = sorted_lows[i]
                previous_low = sorted_lows[i-1]
                
                # Find the candle that broke the previous low
                break_index = None
                for j in range(previous_low['index'] + 1, current_low['index'] + 1):
                    if j < len(df) and df['low'].iloc[j] < previous_low['price']:
                        break_index = j
                        break
                
                if break_index is not None:
                    bos_events.append({
                        'type': 'bos',
                        'direction': 'bearish',
                        'index': break_index,
                        'price': previous_low['price'],
                        'strength': 80,
                        'description': f"Bearish BOS at {previous_low['price']:.5f}"
                    })
            
            return bos_events
            
        except Exception as e:
            logger.error(f"Error identifying break of structure: {e}", exc_info=True)
            return bos_events
    
    def _identify_change_of_character(self, df: pd.DataFrame, 
                                     swing_highs: List[Dict], 
                                     swing_lows: List[Dict]) -> List[Dict]:
        """
        Identify change of character (CHoCH) events
        
        Args:
            df (pd.DataFrame): Price data
            swing_highs (list): Swing high points
            swing_lows (list): Swing low points
            
        Returns:
            list: Change of character events
        """
        choch_events = []
        
        try:
            if df.empty or len(swing_highs) < 3 or len(swing_lows) < 3:
                return choch_events
            
            # Sort swing points by index
            sorted_highs = sorted(swing_highs, key=lambda x: x['index'])
            sorted_lows = sorted(swing_lows, key=lambda x: x['index'])
            
            # Identify bullish CHoCH (higher low followed by break of previous high)
            for i in range(1, len(sorted_lows)):
                current_low = sorted_lows[i]
                previous_low = sorted_lows[i-1]
                
                # Check if this is a higher low
                if current_low['price'] > previous_low['price']:
                    # Find the most recent swing high before this low
                    previous_high = None
                    for high in reversed(sorted_highs):
                        if high['index'] < current_low['index']:
                            previous_high = high
                            break
                    
                    if previous_high is not None:
                        # Check if price broke above this high after the higher low
                        for j in range(current_low['index'] + 1, len(df)):
                            if df['high'].iloc[j] > previous_high['price']:
                                choch_events.append({
                                    'type': 'choch',
                                    'direction': 'bullish',
                                    'index': j,
                                    'price': previous_high['price'],
                                    'strength': 90,  # CHoCH is stronger than BOS
                                    'description': f"Bullish CHoCH at {previous_high['price']:.5f}"
                                })
                                break
            
            # Identify bearish CHoCH (lower high followed by break of previous low)
            for i in range(1, len(sorted_highs)):
                current_high = sorted_highs[i]
                previous_high = sorted_highs[i-1]
                
                # Check if this is a lower high
                if current_high['price'] < previous_high['price']:
                    # Find the most recent swing low before this high
                    previous_low = None
                    for low in reversed(sorted_lows):
                        if low['index'] < current_high['index']:
                            previous_low = low
                            break
                    
                    if previous_low is not None:
                        # Check if price broke below this low after the lower high
                        for j in range(current_high['index'] + 1, len(df)):
                            if df['low'].iloc[j] < previous_low['price']:
                                choch_events.append({
                                    'type': 'choch',
                                    'direction': 'bearish',
                                    'index': j,
                                    'price': previous_low['price'],
                                    'strength': 90,  # CHoCH is stronger than BOS
                                    'description': f"Bearish CHoCH at {previous_low['price']:.5f}"
                                })
                                break
            
            return choch_events
            
        except Exception as e:
            logger.error(f"Error identifying change of character: {e}", exc_info=True)
            return choch_events
    
    # Add this method to the MultiTimeframeAnalyzer class
    def _is_in_kill_zone_time(self, current_time=None):
        """
        Check if the current time is in a kill zone time window
        
        Args:
            current_time (datetime, optional): Time to check, defaults to current time
            
        Returns:
            bool: Whether the current time is in a kill zone
        """
        try:
            # Use provided time or current time
            if current_time is None:
                current_time = datetime.now(pytz.UTC)
            
            # Convert to UTC if it has a timezone, otherwise assume it's UTC
            if current_time.tzinfo is None:
                current_time = pytz.UTC.localize(current_time)
            
            # Convert to London time (UTC+0/+1 depending on DST)
            london_tz = pytz.timezone('Europe/London')
            london_time = current_time.astimezone(london_tz)
            
            # Convert to NY time (UTC-5/-4 depending on DST)
            ny_tz = pytz.timezone('America/New_York')
            ny_time = current_time.astimezone(ny_tz)
            
            # Define kill zones in London time
            london_morning_start = time(10, 0)
            london_morning_end = time(12, 0)
            london_afternoon_start = time(15, 0)
            london_afternoon_end = time(17, 0)
            
            # Define kill zones in NY time
            ny_morning_start = time(8, 0)
            ny_morning_end = time(10, 0)
            ny_afternoon_start = time(14, 0)
            ny_afternoon_end = time(16, 0)
            
            # Check if current time is in any kill zone
            london_morning_kill_zone = (
                london_time.time() >= london_morning_start and 
                london_time.time() <= london_morning_end
            )
            
            london_afternoon_kill_zone = (
                london_time.time() >= london_afternoon_start and 
                london_time.time() <= london_afternoon_end
            )
            
            ny_morning_kill_zone = (
                ny_time.time() >= ny_morning_start and 
                ny_time.time() <= ny_morning_end
            )
            
            ny_afternoon_kill_zone = (
                ny_time.time() >= ny_afternoon_start and 
                ny_time.time() <= ny_afternoon_end
            )
            
            return (
                london_morning_kill_zone or 
                london_afternoon_kill_zone or 
                ny_morning_kill_zone or 
                ny_afternoon_kill_zone
            )
        except Exception as e:
            logger.error(f"Error checking kill zone time: {e}", exc_info=True)
            return False

    def _is_in_kill_zone(self, current_price, zones_of_interest):
        """
        Check if the current price is in a kill zone
        
        Args:
            current_price (float): Current price
            zones_of_interest (list): Zones of interest
            
        Returns:
            bool: Whether the current price is in a kill zone
        """
        try:
            if current_price is None or not zones_of_interest:
                return False
            
            # Check if price is near any zone of interest
            for zone in zones_of_interest:
                if 'type' not in zone:
                    continue
                    
                # Check different zone types
                if zone['type'] in ['order_block', 'fair_value_gap', 'breaker_block']:
                    # These zones have top and bottom
                    if 'top' in zone and 'bottom' in zone:
                        # Check if price is within or very close to the zone
                        zone_top = zone['top']
                        zone_bottom = zone['bottom']
                        zone_height = zone_top - zone_bottom
                        
                        # Consider price in kill zone if it's within the zone or very close to it
                        buffer = zone_height * 0.1  # 10% buffer
                        if (zone_bottom - buffer) <= current_price <= (zone_top + buffer):
                            return True
                elif zone['type'] in ['liquidity', 'key_level']:
                    # These zones have a single price level
                    if 'price' in zone:
                        zone_price = zone['price']
                        
                        # Calculate a buffer based on price (0.1% of price)
                        buffer = zone_price * 0.001
                        
                        # Check if price is close to the level
                        if abs(current_price - zone_price) <= buffer:
                            return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking if price is in kill zone: {e}", exc_info=True)
            return False

    def _identify_entry_opportunities(self, df: pd.DataFrame, htf_bias: str, 
                                    zones_of_interest: List[Dict], 
                                    in_kill_zone: bool) -> List[Dict]:
        """
        Identify entry opportunities on lower timeframe with improved precision
        
        Args:
            df (pd.DataFrame): Price data with indicators
            htf_bias (str): Higher timeframe bias
            zones_of_interest (list): Zones of interest from middle timeframe
            in_kill_zone (bool): Whether current price is in a kill zone
            
        Returns:
            list: Entry opportunities
        """
        entries = []
        
        try:
            if df.empty or len(df) < 20:
                return entries
            
            # Get the current price and recent price action
            current_price = df['close'].iloc[-1]
            recent_df = df.iloc[-30:]  # Increased from 20 to 30 for better context
            
            # Find recent market shifts
            recent_shifts = self._identify_market_shifts(recent_df)
            
            # Get technical indicators for confirmation
            if 'rsi' not in df.columns or 'macd' not in df.columns:
                # Add indicators if not present
                df = self.technical_analyzer.add_indicators(df)
            
            # Only consider entries that align with higher timeframe bias
            if htf_bias == 'bullish':
                # Look for bullish entry opportunities
                
                # 1. Check for bullish market shifts
                bullish_shifts = [shift for shift in recent_shifts if shift.get('direction') == 'bullish']
                
                # 2. Check if we're in a zone of interest
                in_support_zone = False
                closest_support = None
                support_strength = 0
                
                for zone in zones_of_interest:
                    if zone.get('type') in ['support', 'order_block', 'fair_value_gap', 'breaker_block']:
                        if zone.get('subtype', '') == 'bullish' or zone.get('type') == 'support':
                            # For zones with top/bottom
                            if 'top' in zone and 'bottom' in zone:
                                zone_top = zone.get('top')
                                zone_bottom = zone.get('bottom')
                                
                                # Check if price is in or near the zone
                                if zone_bottom * 0.995 <= current_price <= zone_top * 1.005:
                                    in_support_zone = True
                                    if closest_support is None or zone.get('strength', 0) > support_strength:
                                        closest_support = zone
                                        support_strength = zone.get('strength', 0)
                            # For single price levels
                            elif 'price' in zone:
                                zone_price = zone.get('price')
                                
                                # Check if price is near the level
                                if zone_price * 0.995 <= current_price <= zone_price * 1.005:
                                    in_support_zone = True
                                    if closest_support is None or zone.get('strength', 0) > support_strength:
                                        closest_support = zone
                                        support_strength = zone.get('strength', 0)
                
                # 3. Check for confirmation from indicators
                rsi_oversold = False
                macd_bullish = False
                
                if 'rsi' in df.columns:
                    rsi = df['rsi'].iloc[-1]
                    rsi_oversold = rsi < 40  # Not strictly oversold but showing strength
                
                if 'macd' in df.columns and 'macd_signal' in df.columns:
                    macd = df['macd'].iloc[-1]
                    macd_signal = df['macd_signal'].iloc[-1]
                    macd_prev = df['macd'].iloc[-2]
                    macd_signal_prev = df['macd_signal'].iloc[-2]
                    
                    # Check for MACD crossover or positive momentum
                    macd_bullish = (macd_prev < macd_signal_prev and macd > macd_signal) or (macd > 0 and macd > macd_prev)
                
                # 4. Check for bullish candlestick patterns
                bullish_pattern = False
                
                # Check for bullish engulfing
                if len(df) >= 2:
                    prev_candle_range = abs(df['open'].iloc[-2] - df['close'].iloc[-2])
                    curr_candle_range = abs(df['open'].iloc[-1] - df['close'].iloc[-1])
                    
                    bullish_engulfing = (
                        df['close'].iloc[-2] < df['open'].iloc[-2] and  # Previous candle is bearish
                        df['close'].iloc[-1] > df['open'].iloc[-1] and  # Current candle is bullish
                        df['close'].iloc[-1] > df['open'].iloc[-2] and  # Current close above previous open
                        df['open'].iloc[-1] < df['close'].iloc[-2] and  # Current open below previous close
                        curr_candle_range > prev_candle_range  # Current candle engulfs previous
                    )
                    
                    # Check for hammer
                    if not bullish_engulfing:
                        body_size = abs(df['open'].iloc[-1] - df['close'].iloc[-1])
                        lower_wick = min(df['open'].iloc[-1], df['close'].iloc[-1]) - df['low'].iloc[-1]
                        upper_wick = df['high'].iloc[-1] - max(df['open'].iloc[-1], df['close'].iloc[-1])
                        
                        hammer = (
                            df['close'].iloc[-1] > df['open'].iloc[-1] and  # Bullish candle
                            lower_wick > 2 * body_size and  # Long lower wick
                            upper_wick < 0.5 * body_size  # Short or no upper wick
                        )
                        
                        bullish_pattern = bullish_engulfing or hammer
                
                # Generate entry if we have enough confirmation
                entry_score = 0
                if bullish_shifts:
                    entry_score += 30  # Market shift is a strong signal
                if in_support_zone:
                    entry_score += 30  # Price in support zone is a strong signal
                if in_kill_zone:
                    entry_score += 20  # Kill zone adds significance
                if rsi_oversold:
                    entry_score += 10  # RSI confirmation
                if macd_bullish:
                    entry_score += 10  # MACD confirmation
                if bullish_pattern:
                    entry_score += 20  # Candlestick pattern confirmation
                
                # Only generate entry if score is high enough
                if entry_score >= 50:
                    # Calculate potential entry, stop loss, and take profit
                    entry_price = current_price
                    
                    # Find recent swing low for stop loss
                    _, swing_lows = self._find_swing_points(recent_df)
                    if swing_lows:
                        # Use the most recent swing low
                        sorted_lows = sorted(swing_lows, key=lambda x: x['index'], reverse=True)
                        stop_loss = sorted_lows[0]['price'] * 0.998  # Slightly below swing low
                    else:
                        # Use a default stop loss based on ATR
                        atr = self._calculate_atr(recent_df)
                        stop_loss = entry_price - 2 * atr
                    
                    # Calculate take profit based on risk-reward ratio
                    risk = entry_price - stop_loss
                    take_profit = entry_price + 2 * risk  # 1:2 risk-reward ratio
                    
                    # Calculate risk-reward ratio
                    risk_reward = round((take_profit - entry_price) / (entry_price - stop_loss), 2)
                    
                    entries.append({
                        'type': 'entry',
                        'direction': 'buy',
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward': risk_reward,
                        'strength': entry_score,
                        'description': f"Bullish entry at {entry_price:.5f} (SL: {stop_loss:.5f}, TP: {take_profit:.5f})",
                        'confirmations': {
                            'market_shift': bool(bullish_shifts),
                            'support_zone': in_support_zone,
                            'kill_zone': in_kill_zone,
                            'rsi_oversold': rsi_oversold,
                            'macd_bullish': macd_bullish,
                            'bullish_pattern': bullish_pattern
                        }
                    })
            
            elif htf_bias == 'bearish':
                # Look for bearish entry opportunities
                
                # 1. Check for bearish market shifts
                bearish_shifts = [shift for shift in recent_shifts if shift.get('direction') == 'bearish']
                
                # 2. Check if we're in a zone of interest
                in_resistance_zone = False
                closest_resistance = None
                resistance_strength = 0
                
                for zone in zones_of_interest:
                    if zone.get('type') in ['resistance', 'order_block', 'fair_value_gap', 'breaker_block']:
                        if zone.get('subtype', '') == 'bearish' or zone.get('type') == 'resistance':
                            # For zones with top/bottom
                            if 'top' in zone and 'bottom' in zone:
                                zone_top = zone.get('top')
                                zone_bottom = zone.get('bottom')
                                
                                # Check if price is in or near the zone
                                if zone_bottom * 0.995 <= current_price <= zone_top * 1.005:
                                    in_resistance_zone = True
                                    if closest_resistance is None or zone.get('strength', 0) > resistance_strength:
                                        closest_resistance = zone
                                        resistance_strength = zone.get('strength', 0)
                            # For single price levels
                            elif 'price' in zone:
                                zone_price = zone.get('price')
                                
                                # Check if price is near the level
                                if zone_price * 0.995 <= current_price <= zone_price * 1.005:
                                    in_resistance_zone = True
                                    if closest_resistance is None or zone.get('strength', 0) > resistance_strength:
                                        closest_resistance = zone
                                        resistance_strength = zone.get('strength', 0)
                
                # 3. Check for confirmation from indicators
                rsi_overbought = False
                macd_bearish = False
                
                if 'rsi' in df.columns:
                    rsi = df['rsi'].iloc[-1]
                    rsi_overbought = rsi > 60  # Not strictly overbought but showing weakness
                
                if 'macd' in df.columns and 'macd_signal' in df.columns:
                    macd = df['macd'].iloc[-1]
                    macd_signal = df['macd_signal'].iloc[-1]
                    macd_prev = df['macd'].iloc[-2]
                    macd_signal_prev = df['macd_signal'].iloc[-2]
                    
                    # Check for MACD crossover or negative momentum
                    macd_bearish = (macd_prev > macd_signal_prev and macd < macd_signal) or (macd < 0 and macd < macd_prev)
                
                # 4. Check for bearish candlestick patterns
                bearish_pattern = False
                
                # Check for bearish engulfing
                if len(df) >= 2:
                    prev_candle_range = abs(df['open'].iloc[-2] - df['close'].iloc[-2])
                    curr_candle_range = abs(df['open'].iloc[-1] - df['close'].iloc[-1])
                    
                    bearish_engulfing = (
                        df['close'].iloc[-2] > df['open'].iloc[-2] and  # Previous candle is bullish
                        df['close'].iloc[-1] < df['open'].iloc[-1] and  # Current candle is bearish
                        df['close'].iloc[-1] < df['open'].iloc[-2] and  # Current close below previous open
                        df['open'].iloc[-1] > df['close'].iloc[-2] and  # Current open above previous close
                        curr_candle_range > prev_candle_range  # Current candle engulfs previous
                    )
                    
                    # Check for shooting star
                    if not bearish_engulfing:
                        body_size = abs(df['open'].iloc[-1] - df['close'].iloc[-1])
                        lower_wick = min(df['open'].iloc[-1], df['close'].iloc[-1]) - df['low'].iloc[-1]
                        upper_wick = df['high'].iloc[-1] - max(df['open'].iloc[-1], df['close'].iloc[-1])
                        
                        shooting_star = (
                            df['close'].iloc[-1] < df['open'].iloc[-1] and  # Bearish candle
                            upper_wick > 2 * body_size and  # Long upper wick
                            lower_wick < 0.5 * body_size  # Short or no lower wick
                        )
                        
                        bearish_pattern = bearish_engulfing or shooting_star
                
                # Generate entry if we have enough confirmation
                entry_score = 0
                if bearish_shifts:
                    entry_score += 30  # Market shift is a strong signal
                if in_resistance_zone:
                    entry_score += 30  # Price in resistance zone is a strong signal
                if in_kill_zone:
                    entry_score += 20  # Kill zone adds significance
                if rsi_overbought:
                    entry_score += 10  # RSI confirmation
                if macd_bearish:
                    entry_score += 10  # MACD confirmation
                if bearish_pattern:
                    entry_score += 20  # Candlestick pattern confirmation
                
                # Only generate entry if score is high enough
                if entry_score >= 50:
                    # Calculate potential entry, stop loss, and take profit
                    entry_price = current_price
                    
                    # Find recent swing high for stop loss
                    swing_highs, _ = self._find_swing_points(recent_df)
                    if swing_highs:
                        # Use the most recent swing high
                        sorted_highs = sorted(swing_highs, key=lambda x: x['index'], reverse=True)
                        stop_loss = sorted_highs[0]['price'] * 1.002  # Slightly above swing high
                    else:
                        # Use a default stop loss based on ATR
                        atr = self._calculate_atr(recent_df)
                        stop_loss = entry_price + 2 * atr
                    
                    # Calculate take profit based on risk-reward ratio
                    risk = stop_loss - entry_price
                    take_profit = entry_price - 2 * risk  # 1:2 risk-reward ratio
                    
                    # Calculate risk-reward ratio
                    risk_reward = round((entry_price - take_profit) / (stop_loss - entry_price), 2)
                    
                    entries.append({
                        'type': 'entry',
                        'direction': 'sell',
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward': risk_reward,
                        'strength': entry_score,
                        'description': f"Bearish entry at {entry_price:.5f} (SL: {stop_loss:.5f}, TP: {take_profit:.5f})",
                        'confirmations': {
                            'market_shift': bool(bearish_shifts),
                            'resistance_zone': in_resistance_zone,
                            'kill_zone': in_kill_zone,
                            'rsi_overbought': rsi_overbought,
                            'macd_bearish': macd_bearish,
                            'bearish_pattern': bearish_pattern
                        }
                    })
            
            return entries
            
        except Exception as e:
            logger.error(f"Error identifying entry opportunities: {e}", exc_info=True)
            return []

    def _generate_trade_signals(self, higher_tf_analysis: Dict, 
                            middle_tf_analysis: Dict, 
                            lower_tf_analysis: Dict,
                            in_kill_zone_time: bool = False) -> List[Dict]:
        """
        Generate trade signals based on multi-timeframe analysis
        
        Args:
            higher_tf_analysis (dict): Higher timeframe analysis
            middle_tf_analysis (dict): Middle timeframe analysis
            lower_tf_analysis (dict): Lower timeframe analysis
            in_kill_zone_time (bool): Whether current time is in a kill zone
            
        Returns:
            list: Trade signals
        """
        signals = []
        
        try:
            # Get higher timeframe bias
            htf_bias = higher_tf_analysis.get('bias', {}).get('direction', 'neutral')
            htf_confidence = higher_tf_analysis.get('bias', {}).get('confidence', 0)
            
            # Get entry opportunities from lower timeframe
            entry_opportunities = lower_tf_analysis.get('entry_opportunities', [])
            
            # Check if we're in a kill zone (price-based)
            in_kill_zone_price = middle_tf_analysis.get('in_kill_zone', False) or lower_tf_analysis.get('in_kill_zone', False)
            
            # Only generate signals if we have a clear bias
            if htf_bias != 'neutral' and htf_confidence >= 60:
                # Prioritize signals if we're in both time and price kill zones
                signal_strength_multiplier = 1.0
                
                if in_kill_zone_time and in_kill_zone_price:
                    signal_strength_multiplier = 1.5  # Boost signal strength if in both kill zones
                    logger.info(f"In both time and price kill zones - boosting signal strength")
                elif in_kill_zone_time:
                    signal_strength_multiplier = 1.2  # Slight boost for time-based kill zone
                    logger.info(f"In time-based kill zone")
                elif in_kill_zone_price:
                    signal_strength_multiplier = 1.1  # Slight boost for price-based kill zone
                    logger.info(f"In price-based kill zone")
                
                for entry in entry_opportunities:
                    entry_direction = entry.get('direction')
                    
                    # Only consider entries that align with higher timeframe bias
                    if (htf_bias == 'bullish' and entry_direction == 'buy') or \
                    (htf_bias == 'bearish' and entry_direction == 'sell'):
                        
                        # Calculate adjusted strength
                        base_strength = min(entry.get('strength', 70), htf_confidence)
                        adjusted_strength = min(100, base_strength * signal_strength_multiplier)
                        
                        # Create a trade signal
                        signal = {
                            'type': 'trade_signal',
                            'direction': entry_direction,
                            'entry_price': entry.get('entry_price'),
                            'stop_loss': entry.get('stop_loss'),
                            'take_profit': entry.get('take_profit'),
                            'risk_reward': entry.get('risk_reward', 2.0),
                            'strength': adjusted_strength,
                            'description': entry.get('description'),
                            'htf_bias': htf_bias,
                            'htf_confidence': htf_confidence,
                            'in_kill_zone_price': in_kill_zone_price,
                            'in_kill_zone_time': in_kill_zone_time,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        signals.append(signal)
            
            # Sort signals by strength (descending)
            signals.sort(key=lambda x: x.get('strength', 0), reverse=True)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating trade signals: {e}", exc_info=True)
            return signals

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range (ATR)
        
        Args:
            df (pd.DataFrame): Price data
            period (int): ATR period
            
        Returns:
            float: ATR value
        """
        try:
            if df.empty or len(df) < period:
                return 0.0
            
            # Calculate True Range
            df = df.copy()
            df['prev_close'] = df['close'].shift(1)
            df['tr1'] = abs(df['high'] - df['low'])
            df['tr2'] = abs(df['high'] - df['prev_close'])
            df['tr3'] = abs(df['low'] - df['prev_close'])
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # Calculate ATR
            atr = df['tr'].rolling(window=period).mean().iloc[-1]
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}", exc_info=True)
            return 0.0


