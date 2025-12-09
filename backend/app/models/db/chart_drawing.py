"""Chart drawing model for saved chart annotations"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ChartDrawing(Base):
    """Stores chart drawings (lines, rectangles, Fibonacci, etc.)"""
    __tablename__ = "chart_drawings"
    
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False)
    
    # Chart context
    pair = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    
    # Drawing type
    tool_type = Column(String, nullable=False)  # 'line', 'horizontal_line', 'rectangle', 'fib', 'text'
    
    # Drawing configuration (stored as JSON)
    # Includes: coordinates, color, width, starred, label, etc.
    config = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    challenge = relationship("Challenge", back_populates="drawings")
    
    def __repr__(self):
        return f"<ChartDrawing(id={self.id}, type='{self.tool_type}', pair='{self.pair}')>"
