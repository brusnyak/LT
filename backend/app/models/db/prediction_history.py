"""Prediction history model for tracking predictions and accuracy"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PredictionHistory(Base):
    """Stores market predictions and their outcomes for accuracy tracking"""
    __tablename__ = "prediction_history"
    
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete='CASCADE'))
    
    # Market context
    pair = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    prediction_time = Column(DateTime, nullable=False, index=True)
    
    # Prediction data (JSON)
    predicted_candles = Column(JSON, nullable=False)  # Future OHLC predictions
    strategies_used = Column(JSON, nullable=False)  # Which strategies contributed
    ensemble_weights = Column(JSON)  # Weight of each strategy in prediction
    
    # Prediction details
    direction = Column(String)  # 'BULLISH', 'BEARISH', 'RANGING'
    target_high = Column(Float)
    target_low = Column(Float)
    reversal_point = Column(Float)
    confidence = Column(Float)  # 0-100
    
    # Actual outcome (filled after reality unfolds)
    actual_candles = Column(JSON)  # What actually happened
    accuracy_score = Column(Float)  # How accurate was the prediction (0-100)
    outcome_verified = Column(DateTime)  # When we verified the outcome
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    challenge = relationship("Challenge")
    
    def __repr__(self):
        return f"<PredictionHistory(pair='{self.pair}', direction='{self.direction}', confidence={self.confidence})>"
