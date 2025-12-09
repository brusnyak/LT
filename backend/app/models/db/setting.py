"""Setting model for user preferences"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Setting(Base):
    """Stores user settings and preferences per challenge"""
    __tablename__ = "settings"
    __table_args__ = (
        UniqueConstraint('challenge_id', 'key', name='unique_challenge_key'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete='CASCADE'))
    
    key = Column(String, nullable=False, index=True)
    value = Column(Text, nullable=False)
    category = Column(String)  # 'theme', 'layout', 'overlays', 'strategy', 'drawing'
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    challenge = relationship("Challenge", back_populates="settings")
    
    def __repr__(self):
        return f"<Setting(key='{self.key}', category='{self.category}')>"
