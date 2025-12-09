"""Trades API endpoints for signal acceptance and journal management"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.db.trade import Trade
from app.models.db.challenge import Challenge
from app.models.db.prediction_history import PredictionHistory

router = APIRouter()


# Pydantic models for request/response
class SignalAcceptRequest(BaseModel):
    pair: str
    type: str  # LONG/SHORT
    entry: float
    sl: float
    tp: float
    rr: float
    signal_time: str  # ISO format
    strategy: str = "human_trained"
    challenge_id: int = 1  # Default challenge


class TradeResponse(BaseModel):
    id: int
    pair: str
    type: str
    entry_price: float
    sl_price: float
    tp_price: float
    signal_time: datetime
    close_time: Optional[datetime]
    outcome: Optional[str]
    pnl: Optional[float]
    rr_achieved: Optional[float]
    balance_before: float
    balance_after: Optional[float]
    screenshot_path: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.post("/accept", response_model=TradeResponse)
async def accept_signal(
    signal: SignalAcceptRequest,
    db: Session = Depends(get_db)
):
    """
    Accept a signal and create a trade entry in the journal
    Enforces all prop firm rules before acceptance
    """
    try:
        # Import rule checker
        from app.core.rule_checker import check_all_rules_on_trade_accept
        
        # Get challenge
        challenge = db.query(Challenge).filter(Challenge.id == signal.challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Check if challenge is active
        if not challenge.is_active:
            raise HTTPException(status_code=400, detail=f"Challenge breached: {challenge.breach_reason}")
        
        # Calculate risk amount (use challenge's risk_per_trade setting)
        risk_amount = challenge.current_balance * (challenge.risk_per_trade / 100)
        
        # Check all rules before accepting trade
        rules_ok, error_msg = check_all_rules_on_trade_accept(
            challenge=challenge,
            entry_price=signal.entry,
            sl_price=signal.sl,
            tp_price=signal.tp,
            trade_type=signal.type,
            risk_amount=risk_amount,
            db=db
        )
        
        if not rules_ok:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Create trade entry
        trade = Trade(
            challenge_id=signal.challenge_id,
            signal_time=datetime.fromisoformat(signal.signal_time.replace('Z', '+00:00')),
            pair=signal.pair,
            type=signal.type,
            strategy=signal.strategy,
            entry_price=signal.entry,
            sl_price=signal.sl,
            tp_price=signal.tp,
            outcome='ACTIVE',
            risk_amount=risk_amount,
            balance_before=challenge.current_balance
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        # Update challenge last trade date
        challenge.last_trade_date = datetime.utcnow()
        db.commit()
        
        return trade
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to accept signal: {str(e)}")


@router.get("/", response_model=List[TradeResponse])
async def list_trades(
    challenge_id: int = Query(1, description="Challenge ID"),
    pair: Optional[str] = Query(None, description="Filter by pair"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE/CLOSED)"),
    limit: int = Query(100, description="Max trades to return"),
    db: Session = Depends(get_db)
):
    """
    List all trades for a challenge
    """
    query = db.query(Trade).filter(Trade.challenge_id == challenge_id)
    
    if pair:
        query = query.filter(Trade.pair == pair)
    
    if status:
        if status == "ACTIVE":
            query = query.filter(Trade.outcome == 'ACTIVE')
        elif status == "CLOSED":
            query = query.filter(Trade.outcome.in_(['TP_HIT', 'SL_HIT', 'MANUAL_CLOSE']))
    
    trades = query.order_by(Trade.signal_time.desc()).limit(limit).all()
    return trades


@router.delete("/clear")
async def clear_trades(
    challenge_id: int = Query(1, description="Challenge ID"),
    pair: Optional[str] = Query(None, description="Clear only specific pair"),
    db: Session = Depends(get_db)
):
    """
    Clear all trades for a challenge (optionally filtered by pair)
    """
    query = db.query(Trade).filter(Trade.challenge_id == challenge_id)
    
    if pair:
        query = query.filter(Trade.pair == pair)
    
    count = query.delete()
    db.commit()
    
    return {"message": f"Cleared {count} trades"}


@router.delete("/{trade_id}")
async def delete_trade(
    trade_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a specific trade
    """
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    db.delete(trade)
    db.commit()
    
    return {"message": f"Trade {trade_id} deleted successfully"}


@router.patch("/{trade_id}/close")
async def close_trade(
    trade_id: int,
    close_price: float,
    outcome: str = Query(..., description="TP_HIT, SL_HIT, or MANUAL_CLOSE"),
    db: Session = Depends(get_db)
):
    """
    Close a trade and update challenge state
    - Tracks trading days
    - Updates challenge balance
    - Checks for rule violations
    - Triggers phase progression if requirements met
    """
    from app.core.rule_checker import check_all_rules_on_trade_close
    from app.api.challenge_progression import check_phase_completion, advance_phase
    
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Get challenge
    challenge = db.query(Challenge).filter(Challenge.id == trade.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Calculate P&L
    if trade.type == "LONG":
        pnl = (close_price - trade.entry_price) / (trade.entry_price - trade.sl_price) * trade.risk_amount
    else:  # SHORT
        pnl = (trade.entry_price - close_price) / (trade.sl_price - trade.entry_price) * trade.risk_amount
    
    # Calculate RR achieved
    if trade.type == "LONG":
        rr_achieved = (close_price - trade.entry_price) / (trade.entry_price - trade.sl_price)
    else:
        rr_achieved = (trade.entry_price - close_price) / (trade.sl_price - trade.entry_price)
    
    # Update trade
    trade.close_time = datetime.utcnow()
    trade.close_price = close_price
    trade.outcome = outcome
    trade.pnl = pnl
    trade.rr_achieved = rr_achieved
    trade.balance_after = trade.balance_before + pnl
    
    # Update challenge balance
    challenge.current_balance = trade.balance_after
    
    # Track trading days (count unique days with closed trades)
    today = datetime.utcnow().date()
    last_trade_date = challenge.last_trade_date.date() if challenge.last_trade_date else None
    
    if last_trade_date != today:
        challenge.trading_days_count += 1
        print(f"📅 Trading day {challenge.trading_days_count} recorded for challenge {challenge.id}")
    
    challenge.last_trade_date = datetime.utcnow()
    
    db.commit()
    
    # Check for rule violations
    rules_ok, breach_reason = check_all_rules_on_trade_close(challenge, trade, db)
    
    if not rules_ok:
        # Breach the account
        challenge.is_active = False
        challenge.breach_reason = breach_reason
        db.commit()
        
        # Send Telegram notification
        from app.api.challenge_progression import send_telegram_message
        send_telegram_message(
            f"🚨 *ACCOUNT BREACHED*\n\n"
            f"Challenge: {challenge.name}\n"
            f"Reason: {breach_reason}\n\n"
            f"Account has been deactivated."
        )
        
        raise HTTPException(status_code=400, detail=f"Account breached: {breach_reason}")
    
    # Check for phase progression
    is_complete, message = check_phase_completion(challenge)
    
    if is_complete:
        print(f"🎉 Phase complete for challenge {challenge.id}: {message}")
        # Advance phase automatically
        advance_phase(challenge, db)
    
    db.refresh(trade)
    return trade
    
    
class ScreenshotDirectUpload(BaseModel):
    trade_id: int
    image: str # Base64 encoded

@router.post("/screenshot")
async def upload_screenshot_direct(
    upload: ScreenshotDirectUpload,
    db: Session = Depends(get_db)
):
    """
    Upload a screenshot for a specific trade (Direct endpoint)
    """
    import base64
    import os
    
    trade = db.query(Trade).filter(Trade.id == upload.trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
        
    try:
        # Decode base64
        if "base64," in upload.image:
            image_data = base64.b64decode(upload.image.split("base64,")[1])
        else:
            image_data = base64.b64decode(upload.image)
            
        # Ensure uploads dir exists (Journal screenshots)
        uploads_dir = "uploads/journal/screenshots"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file
        filename = f"{upload.trade_id}.png"
        file_path = os.path.join(uploads_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(image_data)
            
        # Update db
        trade.screenshot_path = file_path
        db.commit()
        
        return {"message": "Screenshot saved", "path": file_path}
        
    except Exception as e:
        print(f"Error saving screenshot: {e}")
        raise HTTPException(status_code=500, detail="Failed to save screenshot")


@router.post("/import-from-gym")
async def import_from_gym(
    challenge_id: int = Query(1, description="Challenge ID to import trades into"),
    db: Session = Depends(get_db)
):
    """
    Import verified gym predictions as closed trades in the journal.
    Only imports predictions that have been verified (have accuracy_score).
    """
    # Get challenge
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Get all verified predictions for this challenge
    predictions = db.query(PredictionHistory).filter(
        PredictionHistory.challenge_id == challenge_id,
        PredictionHistory.accuracy_score.isnot(None)
    ).all()
    
    if not predictions:
        return {"message": "No verified predictions found to import", "imported": 0}
    
    imported_count = 0
    current_balance = challenge.starting_balance
    
    for pred in predictions:
        # Determine trade type from prediction direction
        if pred.direction == 'BULLISH':
            trade_type = 'LONG'
        elif pred.direction == 'BEARISH':
            trade_type = 'SHORT'
        else:
            continue  # Skip RANGING predictions
        
        # Use predicted candles to determine entry/exit
        if not pred.predicted_candles or len(pred.predicted_candles) == 0:
            continue
        
        # Entry is the first predicted candle's open
        entry_price = pred.predicted_candles[0].get('open', pred.target_low if trade_type == 'LONG' else pred.target_high)
        
        # SL and TP based on targets
        if trade_type == 'LONG':
            sl_price = pred.target_low
            tp_price = pred.target_high
        else:
            sl_price = pred.target_high
            tp_price = pred.target_low
        
        # Determine outcome based on accuracy
        # High accuracy (>70%) = TP_HIT, Low accuracy (<30%) = SL_HIT, Medium = partial
        if pred.accuracy_score >= 70:
            outcome = 'TP_HIT'
            close_price = tp_price
        elif pred.accuracy_score < 30:
            outcome = 'SL_HIT'
            close_price = sl_price
        else:
            # Partial win/loss based on accuracy
            outcome = 'MANUAL_CLOSE'
            # Interpolate close price based on accuracy
            if trade_type == 'LONG':
                close_price = entry_price + (tp_price - entry_price) * (pred.accuracy_score / 100)
            else:
                close_price = entry_price - (entry_price - tp_price) * (pred.accuracy_score / 100)
        
        # Calculate risk amount (0.5% of current balance)
        risk_amount = current_balance * 0.005
        
        # Calculate P&L
        if trade_type == "LONG":
            pnl = (close_price - entry_price) / (entry_price - sl_price) * risk_amount
            rr_achieved = (close_price - entry_price) / (entry_price - sl_price)
        else:
            pnl = (entry_price - close_price) / (sl_price - entry_price) * risk_amount
            rr_achieved = (entry_price - close_price) / (sl_price - entry_price)
        
        # Create trade
        trade = Trade(
            challenge_id=challenge_id,
            signal_time=pred.prediction_time,
            close_time=pred.outcome_verified,
            pair=pred.pair,
            type=trade_type,
            strategy="gym_import",
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            close_price=close_price,
            outcome=outcome,
            risk_amount=risk_amount,
            balance_before=current_balance,
            balance_after=current_balance + pnl,
            pnl=pnl,
            rr_achieved=rr_achieved
        )
        
        db.add(trade)
        current_balance += pnl
        imported_count += 1
    
    # Update challenge current balance
    challenge.current_balance = current_balance
    
    db.commit()
    
    return {
        "message": f"Successfully imported {imported_count} trades from gym",
        "imported": imported_count,
        "new_balance": current_balance
    }
