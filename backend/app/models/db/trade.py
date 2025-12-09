"""Trade model for journal entries"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Literal
from app.database import Base


class Trade(Base):
    """Represents a single trade entry in the journal"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False)
    
    # Trade timing
    signal_time = Column(DateTime, nullable=False)
    close_time = Column(DateTime)
    
    # Trade details
    pair = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'LONG', 'SHORT'
    strategy = Column(String)  # 'range_4h', 'mtf_30_1', etc.
    
    # Prices
    entry_price = Column(Float, nullable=False)
    sl_price = Column(Float, nullable=False)
    tp_price = Column(Float, nullable=False)
    close_price = Column(Float)
    
    # Outcome
    outcome: Optional[Literal['TP_HIT', 'SL_HIT', 'ACTIVE', 'MANUAL_CLOSE', 'OPEN', 'WIN', 'LOSS', 'BE']] = Column(String)
    
    # Risk/Reward
    risk_amount = Column(Float, nullable=False)  # Dollar amount risked
    pnl = Column(Float)  # Realized P&L
    rr_achieved = Column(Float)  # Actual R multiple achieved
    
    # Balance tracking
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float)
    
    # Notes
    notes = Column(Text)
    screenshot_path = Column(String)  # Path to chart screenshot
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    challenge = relationship("Challenge", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(id={self.id}, pair='{self.pair}', type='{self.type}', outcome='{self.outcome}')>"
