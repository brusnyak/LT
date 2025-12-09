import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.core.data_loader import load_candle_data

class PredictionEngine:
    """
    Engine for handling Prediction Mode (Replay) sessions.
    Allows stepping through historical data and generating strategy predictions.
    """
    
    def __init__(self):
        self.session_id: str = "default"
        self.pair: str = ""
        self.timeframe: str = ""
        self.full_data: Optional[pd.DataFrame] = None
        self.current_index: int = 0
        self.start_index: int = 0
        self.predictions: List[Dict] = []
        self.balance: float = 10000.0
        self.positions: List[Dict] = []
        
    def start_session(self, pair: str, timeframe: str, limit: int = 1000, start_offset: int = 200):
        """
        Initialize a new prediction session.
        
        Args:
            pair: Currency pair (e.g., "EURUSD")
            timeframe: Timeframe (e.g., "5M")
            limit: Total candles to load
            start_offset: How many candles from the end to start at (replay buffer)
        """
        self.pair = pair
        self.timeframe = timeframe
        
        # Load data
        self.full_data = load_candle_data(pair, timeframe, limit=limit)
        
        if self.full_data.empty:
            raise ValueError(f"No data found for {pair} {timeframe}")
            
        # Set cursor
        # We need enough history for indicators (e.g., 200 candles)
        min_history = 200
        total_len = len(self.full_data)
        
        if total_len < min_history + start_offset:
            # If not enough data, just start at min_history
            self.start_index = min_history
        else:
            self.start_index = total_len - start_offset
            
        self.current_index = self.start_index
        self.predictions = []
        self.positions = []
        
        return self._get_session_state()
        
    def next_step(self) -> Dict:
        """
        Advance the cursor by one candle.
        """
        if self.full_data is None or self.current_index >= len(self.full_data) - 1:
            return {"status": "finished", "message": "End of data reached"}
            
        self.current_index += 1
        
        # Here we would run the strategy to generate a prediction
        # For V1, we'll generate a dummy prediction or simple trend-based one
        prediction = self._generate_prediction()
        
        return self._get_session_state(prediction)
        
    def _generate_prediction(self) -> Optional[Dict]:
        """
        Run strategy on current slice of data to predict next move.
        """
        # Get current data slice
        current_df = self.full_data.iloc[:self.current_index+1]
        
        # TODO: Integrate actual strategy here
        # For now, return a simple mock prediction based on last candle
        last_candle = current_df.iloc[-1]
        prev_candle = current_df.iloc[-2]
        
        direction = "NEUTRAL"
        if last_candle['close'] > last_candle['open']:
            direction = "BULLISH"
        elif last_candle['close'] < last_candle['open']:
            direction = "BEARISH"
            
        return {
            "timestamp": str(last_candle.name),
            "direction": direction,
            "confidence": 0.75,
            "target_price": last_candle['close'] * (1.001 if direction == "BULLISH" else 0.999)
        }
        
    def _get_session_state(self, prediction: Optional[Dict] = None) -> Dict:
        """
        Return the current state of the session (visible data, stats).
        """
        if self.full_data is None:
            return {}
            
        # Get visible data (up to current index)
        visible_data = self.full_data.iloc[:self.current_index+1]
        
        # Convert to list of dicts for JSON response
        candles = []
        for index, row in visible_data.iterrows():
            candles.append({
                "time": str(index),
                "open": row['open'],
                "high": row['high'],
                "low": row['low'],
                "close": row['close'],
                "volume": row['volume']
            })
            
        return {
            "pair": self.pair,
            "timeframe": self.timeframe,
            "current_index": self.current_index,
            "total_candles": len(self.full_data),
            "progress": (self.current_index / len(self.full_data)) * 100,
            "candles": candles, # In production, might want to send only delta
            "last_prediction": prediction
        }

# Global instance for V1 (single user)
prediction_engine = PredictionEngine()
