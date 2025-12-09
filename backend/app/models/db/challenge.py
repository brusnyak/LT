"""Challenge model for prop firm challenges"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Challenge(Base):
    """Represents a prop firm challenge (Phase 1, Phase 2, Funded)"""
    __tablename__ = "challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'FTMO', 'MFF', 'FundedTrader', 'Custom'
    phase = Column(String, nullable=False, default='Phase1')  # 'Phase1', 'Phase2', 'Funded'
    
    # Account parameters
    starting_balance = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    profit_target = Column(Float, nullable=False)  # Stored as percentage (8, 6, etc.)
    daily_loss_limit = Column(Float, nullable=False)  # Percentage (7)
    max_drawdown = Column(Float, nullable=False)  # Percentage (12)
    
    # Risk management
    risk_per_trade = Column(Float, default=0.5)  # Percentage
    max_positions = Column(Integer, default=2)
    
    # Progression tracking
    trading_days_count = Column(Integer, default=0)  # Number of days with closed trades
    min_trading_days = Column(Integer, default=4)  # Required trading days for phase
    phase_start_date = Column(DateTime, default=datetime.utcnow)  # When current phase started
    phase_completed_date = Column(DateTime, nullable=True)  # When phase was completed
    
    # Status
    is_active = Column(Boolean, default=True)
    breach_reason = Column(String, nullable=True)  # Reason for account breach
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_trade_date = Column(DateTime, nullable=True)  # Track last trade for inactivity monitoring
    
    # Relationships
    trades = relationship("Trade", back_populates="challenge", cascade="all, delete-orphan")
    settings = relationship("Setting", back_populates="challenge", cascade="all, delete-orphan")
    drawings = relationship("ChartDrawing", back_populates="challenge", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Challenge(id={self.id}, name='{self.name}', type='{self.type}', phase='{self.phase}')>"
