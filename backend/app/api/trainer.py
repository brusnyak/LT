from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.trainer import TrainerSession, ManualTrade
from app.models.db.trainer import DBTrainerSession, DBManualTrade
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/sessions", response_model=TrainerSession)
def create_session(session: TrainerSession, db: Session = Depends(get_db)):
    db_session = DBTrainerSession(
        id=session.id,
        name=session.name,
        symbol=session.symbol,
        start_date=session.start_date,
        end_date=session.end_date,
        created_at=datetime.utcnow()
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/sessions", response_model=List[TrainerSession])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(DBTrainerSession).order_by(DBTrainerSession.created_at.desc()).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=TrainerSession)
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(DBTrainerSession).filter(DBTrainerSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(DBTrainerSession).filter(DBTrainerSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}

@router.post("/sessions/{session_id}/trades", response_model=ManualTrade)
def log_trade(session_id: str, trade: ManualTrade, db: Session = Depends(get_db)):
    """Log a manual trade in a training session"""
    # Verify session exists
    session = db.query(DBTrainerSession).filter(DBTrainerSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create trade object (not saved yet)
    db_trade = DBManualTrade(
        id=trade.id,
        session_id=session_id,
        symbol=trade.symbol,
        entry_time=trade.entry_time,
        type=trade.type,
        entry_price=trade.entry_price,
        sl_price=trade.sl_price,
        tp_price=trade.tp_price,
        close_time=trade.exit_time if hasattr(trade, 'exit_time') else None,
        outcome="OPEN" 
    )

    # --- Outcome Calculation ---
    try:
        from app.core.data_loader import load_candle_data
        import pytz
        
        # Load M1 data starting from entry time to find outcome
        # Using M1 for reasonable precision
        # load_candle_data doesn't support start_date directly, so we load a large chunk and filter
        df = load_candle_data(trade.symbol, "M1", limit=10000)
        # Note: load_candle_data logic for 'start_date' arg might be simpler to just load and filter
        
        # Filter for data after entry
        # Handle Timezone: DF is Europe/Bratislava, trade.entry_time is likely UTC (from frontend ISO)
        bratislava_tz = pytz.timezone('Europe/Bratislava')
        
        if trade.entry_time.tzinfo is None:
            # Assume UTC if naive
            entry_utc = pytz.utc.localize(trade.entry_time)
        else:
            entry_utc = trade.entry_time.astimezone(pytz.utc)
            
        # Convert entry time to target timezone for comparison
        entry_dt = entry_utc.astimezone(bratislava_tz)
        
        future_data = df[df.index >= entry_dt].sort_index()

        outcome = "OPEN"
        close_time = None
        close_price = None
        
        # Standard Risk settings
        RISK_AMOUNT = 500.0 # $500 (1% of 50k)
        risk_per_unit = abs(trade.entry_price - trade.sl_price)
        units = (RISK_AMOUNT / risk_per_unit) if risk_per_unit > 0 else 0

        for ts, row in future_data.iterrows():
            # Check price action within the candle (Low/High)
            
            if trade.type == 'LONG':
                # Check SL first? Or check overlap?
                # Conservative: Check SL range
                if row['low'] <= trade.sl_price:
                    outcome = "SL_HIT"
                    close_price = trade.sl_price
                    close_time = ts
                    break
                if row['high'] >= trade.tp_price:
                    outcome = "TP_HIT"
                    close_price = trade.tp_price
                    close_time = ts
                    break
            
            elif trade.type == 'SHORT':
                if row['high'] >= trade.sl_price:
                    outcome = "SL_HIT"
                    close_price = trade.sl_price
                    close_time = ts
                    break
                if row['low'] <= trade.tp_price:
                    outcome = "TP_HIT"
                    close_price = trade.tp_price
                    close_time = ts
                    break
        
        # Apply outcome if found
        if outcome != "OPEN":
            db_trade.outcome = outcome
            db_trade.close_time = close_time
            db_trade.close_price = close_price
            
            # Calculate PnL
            price_diff = (close_price - trade.entry_price) if trade.type == 'LONG' else (trade.entry_price - close_price)
            db_trade.pnl = price_diff * units
            
            # Update session stats
            session.total_pnl += db_trade.pnl
            # Recalculate win rate
            # We need to query all closed trades for this session or update incrementally
            # Incremental update:
            # We increment total_trades later.
            # Win rate = wins / total.
            # But safer to just leave it for now or simple update.
            
    except Exception as e:
        print(f"Error calculating trade outcome: {e}")
        # Proceed with saving as OPEN or PENDING

    db.add(db_trade)
    
    # Update session stats
    session.total_trades += 1
    
    db.commit()
    db.refresh(db_trade)
    
    return ManualTrade(
        id=db_trade.id,
        session_id=db_trade.session_id,
        symbol=db_trade.symbol,
        entry_time=db_trade.entry_time,
        type=db_trade.type,
        entry_price=db_trade.entry_price,
        sl_price=db_trade.sl_price,
        tp_price=db_trade.tp_price,
        outcome=db_trade.outcome,
        pnl=db_trade.pnl,
        close_time=db_trade.close_time,
        close_price=db_trade.close_price
    )

@router.put("/trades/{trade_id}", response_model=ManualTrade)
def update_trade(trade_id: str, trade_update: ManualTrade, db: Session = Depends(get_db)):
    db_trade = db.query(DBManualTrade).filter(DBManualTrade.id == trade_id).first()
    if not db_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
        
    # Update fields
    if trade_update.close_time:
        db_trade.close_time = trade_update.close_time
    if trade_update.close_price:
        db_trade.close_price = trade_update.close_price
    if trade_update.pnl is not None:
        db_trade.pnl = trade_update.pnl
        # Update session total PnL
        db_trade.session.total_pnl += trade_update.pnl
    if trade_update.outcome:
        db_trade.outcome = trade_update.outcome
        
    db.commit()
    db.refresh(db_trade)
    db.refresh(db_trade)
    return db_trade

class ScreenshotUpload(BaseModel):
    trade_id: str
    image: str # Base64 encoded

@router.post("/sessions/{session_id}/trades/{trade_id}/screenshot")
async def upload_screenshot(
    session_id: str,
    trade_id: str,
    upload: ScreenshotUpload,
    db: Session = Depends(get_db)
):
    import base64
    import os
    
    # Verify trade exists
    db_trade = db.query(DBManualTrade).filter(DBManualTrade.id == trade_id, DBManualTrade.session_id == session_id).first()
    if not db_trade:
        raise HTTPException(status_code=404, detail="Trade not found")
        
    try:
        # Decode base64
        # Remove header if present (data:image/png;base64,...)
        if "base64," in upload.image:
            image_data = base64.b64decode(upload.image.split("base64,")[1])
        else:
            image_data = base64.b64decode(upload.image)
            
        # Ensure uploads dir exists
        uploads_dir = "uploads/gym/screenshots"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file
        filename = f"{trade_id}.png"
        file_path = os.path.join(uploads_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(image_data)
            
        # Update db
        db_trade.screenshot_path = file_path
        db.commit()
        
        return {"message": "Screenshot saved", "path": file_path}
        
    except Exception as e:
        print(f"Error saving screenshot: {e}")
        raise HTTPException(status_code=500, detail="Failed to save screenshot")

