"""Journal/Trades API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.db.trade import Trade
from app.models.db.challenge import Challenge
from pydantic import BaseModel

router = APIRouter()


# Pydantic models
class TradeCreate(BaseModel):
    """Request model for creating a trade"""
    challenge_id: int
    signal_time: datetime
    pair: str
    type: str  # 'LONG', 'SHORT'
    strategy: Optional[str] = None
    entry_price: float
    sl_price: float
    tp_price: float
    risk_amount: float
    balance_before: float
    notes: Optional[str] = None


class TradeClose(BaseModel):
    """Request model for closing a trade"""
    close_price: float
    outcome: str  # 'TP_HIT', 'SL_HIT', 'MANUAL_CLOSE'


class TradeResponse(BaseModel):
    """Response model for trade data"""
    id: int
    challenge_id: int
    signal_time: datetime
    close_time: Optional[datetime]
    pair: str
    type: str
    strategy: Optional[str]
    entry_price: float
    sl_price: float
    tp_price: float
    close_price: Optional[float]
    outcome: Optional[str]
    risk_amount: float
    pnl: Optional[float]
    rr_achieved: Optional[float]
    balance_before: float
    balance_after: Optional[float]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class JournalStats(BaseModel):
    """Statistics for a challenge's trading journal"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    active_trades: int
    win_rate: float
    avg_rr: float
    total_pnl: float
    max_drawdown: float
    best_trade: Optional[float]
    worst_trade: Optional[float]


@router.post("/journal/trades", response_model=TradeResponse, status_code=201)
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    """Create a new trade entry"""
    # Verify challenge exists
    challenge = db.query(Challenge).filter(Challenge.id == trade.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    db_trade = Trade(**trade.dict(), outcome='ACTIVE')
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    
    return db_trade


@router.get("/journal/trades", response_model=List[TradeResponse])
async def list_trades(
    challenge_id: Optional[int] = Query(None, description="Filter by challenge ID"),
    active_only: bool = Query(False, description="Return only active trades"),
    db: Session = Depends(get_db)
):
    """Get list of all trades"""
    query = db.query(Trade)
    
    if challenge_id:
        query = query.filter(Trade.challenge_id == challenge_id)
    
    if active_only:
        query = query.filter(Trade.outcome == 'ACTIVE')
    
    return query.order_by(Trade.signal_time.desc()).all()


@router.get("/journal/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade by ID"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade


@router.put("/journal/trades/{trade_id}/close", response_model=TradeResponse)
async def close_trade(
    trade_id: int,
    close_data: TradeClose,
    db: Session = Depends(get_db)
):
    """Close a trade and calculate P&L"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.outcome != 'ACTIVE':
        raise HTTPException(status_code=400, detail="Trade is already closed")
    
    # Update trade
    trade.close_time = datetime.utcnow()
    trade.close_price = close_data.close_price
    trade.outcome = close_data.outcome
    
    # Calculate P&L
    if trade.type == 'LONG':
        pnl = trade.risk_amount * (close_data.close_price - trade.entry_price) / (trade.entry_price - trade.sl_price)
    else:  # SHORT
        pnl = trade.risk_amount * (trade.entry_price - close_data.close_price) / (trade.sl_price - trade.entry_price)
    
    trade.pnl = pnl
    trade.balance_after = trade.balance_before + pnl
    trade.rr_achieved = pnl / trade.risk_amount if trade.risk_amount > 0 else 0
    
    # Update challenge balance
    challenge = db.query(Challenge).filter(Challenge.id == trade.challenge_id).first()
    if challenge:
        challenge.current_balance = trade.balance_after
    
    db.commit()
    db.refresh(trade)
    
    return trade


@router.get("/journal/stats/{challenge_id}", response_model=JournalStats)
async def get_challenge_stats(challenge_id: int, db: Session = Depends(get_db)):
    """Get trading statistics for a challenge"""
    trades = db.query(Trade).filter(Trade.challenge_id == challenge_id).all()
    
    if not trades:
        return JournalStats(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            active_trades=0,
            win_rate=0.0,
            avg_rr=0.0,
            total_pnl=0.0,
            max_drawdown=0.0,
            best_trade=None,
            worst_trade=None
        )
    
    closed_trades = [t for t in trades if t.outcome in ['TP_HIT', 'SL_HIT', 'MANUAL_CLOSE']]
    active_trades = [t for t in trades if t.outcome == 'ACTIVE']
    winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
    losing_trades = [t for t in closed_trades if t.pnl and t.pnl <= 0]
    
    total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
    avg_rr = sum(t.rr_achieved for t in closed_trades if t.rr_achieved) / len(closed_trades) if closed_trades else 0.0
    win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0.0
    
    # Calculate max drawdown
    balances = [t.balance_after for t in closed_trades if t.balance_after]
    max_drawdown = 0.0
    if balances:
        peak = balances[0]
        for balance in balances:
            if balance > peak:
                peak = balance
            drawdown = peak - balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
    
    pnls = [t.pnl for t in closed_trades if t.pnl]
    best_trade = max(pnls) if pnls else None
    worst_trade = min(pnls) if pnls else None
    
    return JournalStats(
        total_trades=len(trades),
        winning_trades=len(winning_trades),
        losing_trades=len(losing_trades),
        active_trades=len(active_trades),
        win_rate=win_rate,
        avg_rr=avg_rr,
        total_pnl=total_pnl,
        max_drawdown=max_drawdown,
        best_trade=best_trade,
        worst_trade=worst_trade
    )


@router.delete("/journal/trades/{trade_id}")
async def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    """Delete a trade"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    db.delete(trade)
    db.commit()
    
    return {"message": "Trade deleted"}
