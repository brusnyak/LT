"""Stats API endpoints for dashboard and home page"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.db.trade import Trade

router = APIRouter()


@router.get("/summary")
async def get_stats_summary(
    challenge_id: int = Query(1, description="Challenge ID"),
    pair: Optional[str] = Query(None, description="Filter by pair"),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics from journal trades for dashboard/home page
    Returns: win_rate, avg_rr, total_trades, etc.
    """
    try:
        # Query closed trades from database
        query = db.query(Trade).filter(
            Trade.challenge_id == challenge_id,
            Trade.outcome.in_(['TP_HIT', 'SL_HIT', 'MANUAL_CLOSE'])
        )
        
        if pair:
            query = query.filter(Trade.pair == pair)
        
        trades = query.all()
        
        if not trades:
            return {
                'win_rate': 0,
                'avg_rr': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'challenge_id': challenge_id
            }
        
        # Calculate stats from actual trades
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.outcome == 'TP_HIT'])
        losing_trades = len([t for t in trades if t.outcome == 'SL_HIT'])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate average RR from achieved RR (not planned)
        rr_values = [t.rr_achieved for t in trades if t.rr_achieved is not None]
        avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0
        
        return {
            'win_rate': round(win_rate, 1),
            'avg_rr': round(avg_rr, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'challenge_id': challenge_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats calculation failed: {str(e)}")
