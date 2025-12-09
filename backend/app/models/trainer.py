from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import uuid

class ManualTrade(BaseModel):
    """
    Represents a single manual trade taken by the user in the Trainer UI.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime] = None # Optional exit time
    type: Literal['LONG', 'SHORT']
    entry_price: float
    sl_price: float
    tp_price: float
    
    # Outcome (calculated later or updated when closed)
    close_time: Optional[datetime] = None
    close_price: Optional[float] = None
    pnl: Optional[float] = None
    outcome: Optional[Literal['WIN', 'LOSS', 'BE', 'OPEN']] = None
    screenshot_path: Optional[str] = None
    
    # Snapshot of market state at entry (for calibration)
    # We can store this as a JSON string or a dict
    market_snapshot: Optional[dict] = None

class TrainerSession(BaseModel):
    """
    Represents a training session (e.g., "EURUSD 2024 Practice").
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    trades: List[ManualTrade] = []
    
    # Stats
    total_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
