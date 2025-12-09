from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class DBTrainerSession(Base):
    __tablename__ = "trainer_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Stats (denormalized for easier access)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)

    # Relationships
    trades = relationship("DBManualTrade", back_populates="session", cascade="all, delete-orphan")

class DBManualTrade(Base):
    __tablename__ = "manual_trades"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("trainer_sessions.id"), nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=True) # e.g. "M5", "H1"
    
    # Entry data
    entry_time = Column(DateTime, nullable=False)
    type = Column(String, nullable=False) # LONG or SHORT
    entry_price = Column(Float, nullable=False)
    sl_price = Column(Float, nullable=False)
    tp_price = Column(Float, nullable=False)
    
    # Exit data (user-marked, not backfilled)
    exit_time = Column(DateTime, nullable=True)  # Actual close time
    exit_price = Column(Float, nullable=True)  # Actual close price
    close_time = Column(DateTime, nullable=True)  # Legacy field (kept for compatibility)
    close_price = Column(Float, nullable=True)  # Legacy field (kept for compatibility)
    
    # Outcome (user-marked or auto-calculated)
    pnl = Column(Float, nullable=True)
    outcome = Column(String, nullable=True) # WIN, LOSS, BE
    
    # Visual context and documentation
    screenshot_path = Column(String, nullable=True)  # Path to chart screenshot
    annotations = Column(JSON, nullable=True)  # Drawing data (lines, zones, text)
    notes = Column(Text, nullable=True)  # User notes about trading logic
    
    # Snapshot (legacy)
    market_snapshot = Column(JSON, nullable=True)

    # Relationships
    session = relationship("DBTrainerSession", back_populates="trades")
