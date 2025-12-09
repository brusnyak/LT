"""Journal models for trade tracking and account management"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal

class TradeRecord(BaseModel):
    """Individual trade record"""
    id: int
    signal_time: datetime
    close_time: datetime | None
    pair: str
    type: Literal['LONG', 'SHORT']
    entry_price: float
    sl_price: float
    tp_price: float
    close_price: float | None = None
    outcome: Literal['TP_HIT', 'SL_HIT', 'ACTIVE', 'TP1_HIT', 'TP2_HIT'] = 'ACTIVE'
    risk_amount: float  # $ risked on this trade
    pnl: float | None  # Realized P&L
    rr_achieved: float | None  # Actual R multiple achieved
    balance_before: float
    balance_after: float | None
    
class AccountState(BaseModel):
    """Current account state"""
    balance: float
    starting_balance: float
    equity: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    active_trades: int
    total_pnl: float
    total_risk: float  # Total $ at risk in active trades
    win_rate: float
    avg_rr: float
    max_drawdown: float
    daily_pnl: float

class JournalStats(BaseModel):
    """Trading statistics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_rr: float  # Average R multiple
    total_pnl: float
    max_drawdown: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    best_trade: float | None
    worst_trade: float | None

class JournalResponse(BaseModel):
    """Complete journal data"""
    account: AccountState
    trades: List[TradeRecord]
    stats: JournalStats
