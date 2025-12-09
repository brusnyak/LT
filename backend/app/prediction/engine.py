"""Multi-strategy ensemble prediction engine"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.prediction.pattern_analyzer import PatternAnalyzer


class PredictionEngine:
    """
    Main prediction engine that combines multiple strategies
    to generate market predictions
    """
    
    def __init__(self, strategies: Optional[List] = None):
        self.strategies = strategies or []
        self.pattern_analyzer = PatternAnalyzer()
        self.prediction_history = []
    
    def predict_market(
        self,
        df: pd.DataFrame,
        split_index: int,
        num_candles: int = 20,
        timeframe: str = "M5"
    ) -> Dict[str, Any]:
        """
        Generate market prediction using ensemble of strategies and pattern analysis
        
        Args:
            df: Full historical dataframe
            split_index: Index to split actual vs predicted
            num_candles: Number of candles to predict
            timeframe: Chart timeframe
            
        Returns:
            Complete prediction with targets, direction, confidence
        """
        # Split data
        actual_df = df.iloc[:split_index].copy()
        
        if len(actual_df) < 50:
            raise ValueError("Not enough historical data for prediction (need at least 50 candles)")
        
        # 1. Pattern Analysis
        trend = self.pattern_analyzer.analyze_trend(actual_df)
        levels = self.pattern_analyzer.identify_support_resistance(actual_df)
        targets = self.pattern_analyzer.predict_targets(actual_df, trend['direction'])
        reversal_price, reversal_conf = self.pattern_analyzer.predict_reversal_zone(
            actual_df, trend['direction']
        )
        
        # 2. Strategy Ensemble (if strategies provided)
        strategy_predictions = []
        strategy_weights = {}
        
        for strategy in self.strategies:
            try:
                # Run strategy analysis on actual data
                result = strategy.analyze({'primary': actual_df})
                
                # Extract strategy's view
                strategy_pred = self._extract_strategy_prediction(result, actual_df)
                strategy_predictions.append(strategy_pred)
                
                # Weight based on strategy's historical performance
                strategy_weights[strategy.name] = getattr(strategy, 'accuracy_weight', 1.0)
            except Exception as e:
                print(f"Strategy {getattr(strategy, 'name', 'unknown')} failed: {e}")
                continue
        
        # 3. Combine predictions
        if strategy_predictions:
            ensemble_direction = self._vote_direction(strategy_predictions, strategy_weights)
            ensemble_confidence = self._calculate_consensus(strategy_predictions, strategy_weights)
        else:
            ensemble_direction = trend['direction']
            ensemble_confidence = trend['strength']
        
        # 4. Generate predicted candles
        predicted_candles = self._generate_predicted_candles(
            actual_df,
            num_candles,
            ensemble_direction,
            targets,
            reversal_price,
            timeframe
        )
        
        # 5. Prepare prediction result
        prediction = {
            'split_index': split_index,
            'split_time': actual_df.iloc[-1]['time'].isoformat() if len(actual_df) > 0 else None,
            'direction': ensemble_direction,
            'confidence': ensemble_confidence,
            'target_high': targets['target_high'],
            'target_low': targets['target_low'],
            'reversal_point': reversal_price,
            'reversal_confidence': reversal_conf,
            'predicted_candles': predicted_candles,
            'pattern_analysis': {
                'trend': trend,
                'support_resistance': levels,
            },
            'strategies_used': [s.name for s in self.strategies if hasattr(s, 'name')],
            'ensemble_weights': strategy_weights,
            'timeframe': timeframe,
        }
        
        return prediction
    
    def step_prediction(
        self,
        df: pd.DataFrame,
        current_split: int,
        direction: str = "forward"
    ) -> int:
        """
        Move the split point forward or backward
        
        Returns:
            New split index
        """
        new_split = current_split + (1 if direction == "forward" else -1)
        
        # Keep within bounds (min 50 candles history, leave 20 for future)
        new_split = max(50, min(len(df) - 20, new_split))
        
        return new_split
    
    def calculate_accuracy(
        self,
        prediction: Dict,
        actual_df: pd.DataFrame
    ) -> float:
        """
        Compare prediction vs actual outcome
        
        Returns:
            Accuracy score (0-100)
        """
        predicted_candles = prediction['predicted_candles']
        predicted_direction = prediction['direction']
        
        # Get actual candles for the same time period
        split_time = datetime.fromisoformat(prediction['split_time'])
        actual_future = actual_df[actual_df['time'] > split_time].head(len(predicted_candles))
        
        if len(actual_future) == 0:
            return 0.0
        
        # Direction accuracy
        actual_direction = self._determine_actual_direction(actual_future)
        direction_correct = 100 if actual_direction == predicted_direction else 0
        
        # Target accuracy
        actual_high = actual_future['high'].max()
        actual_low = actual_future['low'].min()
        
        target_high_error = abs(actual_high - prediction['target_high']) / actual_high * 100
        target_low_error = abs(actual_low - prediction['target_low']) / actual_low * 100
        
        target_accuracy = max(0, 100 - (target_high_error + target_low_error) / 2)
        
        # Price prediction accuracy (compare predicted OHLC vs actual)
        price_accuracy = 0
        for i, pred_candle in enumerate(predicted_candles):
            if i >= len(actual_future):
                break
            
            actual_row = actual_future.iloc[i]
            
            # Compare close prices
            close_error = abs(actual_row['close'] - pred_candle['close']) / actual_row['close'] * 100
            price_accuracy += max(0, 100 - close_error)
        
        price_accuracy /= len(predicted_candles) if predicted_candles else 1
        
        # Combined accuracy (weighted)
        total_accuracy = (
            direction_correct * 0.4 +
            target_accuracy * 0.3 +
            price_accuracy * 0.3
        )
        
        return total_accuracy
    
    def _extract_strategy_prediction(self, strategy_result: Dict, df: pd.DataFrame) -> Dict:
        """Extract prediction-relevant info from strategy analysis"""
        signals = strategy_result.get('signals', [])
        
        # Determine strategy's directional bias
        if signals:
            last_signal = signals[-1]
            direction = 'BULLISH' if last_signal.get('type') == 'LONG' else 'BEARISH'
        else:
            # No signals = ranging
            direction = 'RANGING'
        
        return {
            'direction': direction,
            'confidence': 70 if signals else 30,
            'signals': signals
        }
    
    def _vote_direction(self, predictions: List[Dict], weights: Dict) -> str:
        """Weighted voting for direction"""
        votes = {'BULLISH': 0, 'BEARISH': 0, 'RANGING': 0}
        
        for pred in predictions:
            direction = pred.get('direction', 'RANGING')
            weight = weights.get(pred.get('strategy_name', ''), 1.0)
            votes[direction] += weight
        
        return max(votes, key=votes.get)
    
    def _calculate_consensus(self, predictions: List[Dict], weights: Dict) -> float:
        """Calculate confidence based on strategy consensus"""
        if not predictions:
            return 50.0
        
        # Check how many strategies agree
        directions = [p.get('direction') for p in predictions]
        most_common = max(set(directions), key=directions.count)
        agreement_count = directions.count(most_common)
        
        consensus = (agreement_count / len(predictions)) * 100
        return consensus
    
    def _generate_predicted_candles(
        self,
        actual_df: pd.DataFrame,
        num_candles: int,
        direction: str,
        targets: Dict,
        reversal_point: float,
        timeframe: str
    ) -> List[Dict]:
        """Generate predicted OHLC candles based on direction and targets"""
        predicted = []
        
        last_candle = actual_df.iloc[-1]
        current_price = last_candle['close']
        last_time = last_candle['time']
        
        # Determine time delta based on timeframe
        time_delta = self._get_time_delta(timeframe)
        
        # Calculate price movement parameters
        target_high = targets['target_high']
        target_low = targets['target_low']
        
        # Generate candles with realistic price movement
        for i in range(num_candles):
            # Time progression
            candle_time = last_time + time_delta * (i + 1)
            
            # Price progression (gradual movement toward targets)
            progress = (i + 1) / num_candles
            
            if direction == 'BULLISH':
                # Upward trend with pullbacks
                base_close = current_price + (target_high - current_price) * progress
                volatility = (target_high - current_price) * 0.02  # 2% volatility
            elif direction == 'BEARISH':
                # Downward trend with bounces
                base_close = current_price - (current_price - target_low) * progress
                volatility = (current_price - target_low) * 0.02
            else:  # RANGING
                # Oscillate between support/resistance
                base_close = current_price + np.sin(i * 0.5) * (target_high - target_low) * 0.3
                volatility = (target_high - target_low) * 0.01
            
            # Add some randomness
            noise = np.random.randn() * volatility * 0.5
            close = base_close + noise
            
            # Generate OHLC
            high = close + abs(np.random.randn() * volatility)
            low = close - abs(np.random.randn() * volatility)
            open_price = predicted[-1]['close'] if predicted else current_price
            
            predicted.append({
                'time': candle_time.isoformat(),
                'open': round(open_price, 5),
                'high': round(high, 5),
                'low': round(low, 5),
                'close': round(close, 5),
                'volume': int(last_candle.get('volume', 1000) * (1 + np.random.randn() * 0.1))
            })
        
        return predicted
    
    def _get_time_delta(self, timeframe: str) -> timedelta:
        """Convert timeframe string to timedelta"""
        mapping = {
            'M1': timedelta(minutes=1),
            'M5': timedelta(minutes=5),
            'M15': timedelta(minutes=15),
            'M30': timedelta(minutes=30),
            'H1': timedelta(hours=1),
            'H4': timedelta(hours=4),
            'D1': timedelta(days=1),
        }
        return mapping.get(timeframe, timedelta(minutes=5))
    
    def _determine_actual_direction(self, df: pd.DataFrame) -> str:
        """Determine actual direction from real price movement"""
        if len(df) < 2:
            return 'RANGING'
        
        start_price = df.iloc[0]['close']
        end_price = df.iloc[-1]['close']
        change = (end_price - start_price) / start_price * 100
        
        if change > 0.5:
            return 'BULLISH'
        elif change < -0.5:
            return 'BEARISH'
        else:
            return 'RANGING'
