"""
Challenge Progression API
Handles phase advancement and progression tracking

Endpoints:
- POST /api/progression/{challenge_id}/check - Check if phase completed
- POST /api/progression/{challenge_id}/advance - Advance to next phase
- GET /api/progression/{challenge_id}/status - Get progression status
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.db.challenge import Challenge
import os
import requests

router = APIRouter()

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def send_telegram_message(message: str):
    """Send notification via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram: {e}")


class ProgressionStatus(BaseModel):
    """Progression status response"""
    phase: str
    trading_days: int
    min_trading_days: int
    current_profit_pct: float
    profit_target_pct: float
    is_phase_complete: bool
    can_advance: bool
    message: str


def check_phase_completion(challenge: Challenge) -> tuple[bool, str]:
    """
    Check if current phase requirements are met
    
    Returns: (is_complete, message)
    """
    current_profit_pct = ((challenge.current_balance - challenge.starting_balance) / challenge.starting_balance) * 100
    
    if challenge.phase == 'Phase1':
        # Step 1: 8% profit + 4 trading days
        profit_met = current_profit_pct >= 8.0
        days_met = challenge.trading_days_count >= challenge.min_trading_days
        
        if profit_met and days_met:
            return True, f"🎉 Step 1 Complete! Profit: {current_profit_pct:.2f}%, Trading Days: {challenge.trading_days_count}"
        elif profit_met:
            return False, f"Profit target met ({current_profit_pct:.2f}%), need {challenge.min_trading_days - challenge.trading_days_count} more trading days"
        elif days_met:
            return False, f"Trading days met ({challenge.trading_days_count}), need {8.0 - current_profit_pct:.2f}% more profit"
        else:
            return False, f"Need {8.0 - current_profit_pct:.2f}% profit and {challenge.min_trading_days - challenge.trading_days_count} trading days"
    
    elif challenge.phase == 'Phase2':
        # Step 2: 6% profit + 4 trading days
        profit_met = current_profit_pct >= 6.0
        days_met = challenge.trading_days_count >= challenge.min_trading_days
        
        if profit_met and days_met:
            return True, f"🎉 Step 2 Complete! Profit: {current_profit_pct:.2f}%, Trading Days: {challenge.trading_days_count}"
        elif profit_met:
            return False, f"Profit target met ({current_profit_pct:.2f}%), need {challenge.min_trading_days - challenge.trading_days_count} more trading days"
        elif days_met:
            return False, f"Trading days met ({challenge.trading_days_count}), need {6.0 - current_profit_pct:.2f}% more profit"
        else:
            return False, f"Need {6.0 - current_profit_pct:.2f}% profit and {challenge.min_trading_days - challenge.trading_days_count} trading days"
    
    elif challenge.phase == 'Funded':
        # Funded accounts don't have completion requirements
        return False, "Funded account - no phase completion"
    
    return False, "Unknown phase"


def advance_phase(challenge: Challenge, db: Session):
    """
    Advance challenge to next phase
    
    Phase1 -> Phase2: Reset balance, change profit target to 6%
    Phase2 -> Funded: Keep balance, no profit target
    """
    if challenge.phase == 'Phase1':
        # Mark Phase 1 as completed
        challenge.phase_completed_date = datetime.utcnow()
        
        # Advance to Phase 2
        challenge.phase = 'Phase2'
        challenge.profit_target = 6.0  # 6% for Step 2
        challenge.current_balance = challenge.starting_balance  # Reset balance
        challenge.trading_days_count = 0  # Reset trading days
        challenge.phase_start_date = datetime.utcnow()
        
        db.commit()
        
        # Send Telegram notification
        send_telegram_message(
            f"🎉 *PHASE ADVANCEMENT*\n\n"
            f"Challenge: {challenge.name}\n"
            f"Phase 1 → Phase 2\n\n"
            f"Balance reset to: ${challenge.starting_balance:,.0f}\n"
            f"New target: 6% (${challenge.starting_balance * 0.06:,.0f})\n"
            f"Trading days reset: 0 / {challenge.min_trading_days}"
        )
        
        return "Advanced to Phase 2"
    
    elif challenge.phase == 'Phase2':
        # Mark Phase 2 as completed
        challenge.phase_completed_date = datetime.utcnow()
        
        # Advance to Funded
        challenge.phase = 'Funded'
        challenge.profit_target = 0  # No target for funded
        # Balance stays as-is
        challenge.trading_days_count = 0
        challenge.phase_start_date = datetime.utcnow()
        
        db.commit()
        
        # Send Telegram notification
        send_telegram_message(
            f"🎉 *CONGRATULATIONS!*\n\n"
            f"Challenge: {challenge.name}\n"
            f"Phase 2 → Funded Account\n\n"
            f"Current Balance: ${challenge.current_balance:,.0f}\n"
            f"You are now trading a funded account!"
        )
        
        return "Advanced to Funded"
    
    else:
        raise HTTPException(status_code=400, detail="Cannot advance from Funded phase")


@router.post("/{challenge_id}/check")
async def check_progression(challenge_id: int, db: Session = Depends(get_db)):
    """Check if challenge phase is complete"""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    is_complete, message = check_phase_completion(challenge)
    
    return {
        "is_complete": is_complete,
        "message": message,
        "can_advance": is_complete
    }


@router.post("/{challenge_id}/advance")
async def advance_challenge_phase(challenge_id: int, db: Session = Depends(get_db)):
    """Manually advance challenge to next phase"""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Check if phase is complete
    is_complete, message = check_phase_completion(challenge)
    if not is_complete:
        raise HTTPException(status_code=400, detail=f"Phase not complete: {message}")
    
    # Advance phase
    result = advance_phase(challenge, db)
    
    return {
        "success": True,
        "message": result,
        "new_phase": challenge.phase
    }


@router.get("/{challenge_id}/status", response_model=ProgressionStatus)
async def get_progression_status(challenge_id: int, db: Session = Depends(get_db)):
    """Get detailed progression status"""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    current_profit_pct = ((challenge.current_balance - challenge.starting_balance) / challenge.starting_balance) * 100
    is_complete, message = check_phase_completion(challenge)
    
    return ProgressionStatus(
        phase=challenge.phase,
        trading_days=challenge.trading_days_count,
        min_trading_days=challenge.min_trading_days,
        current_profit_pct=current_profit_pct,
        profit_target_pct=challenge.profit_target,
        is_phase_complete=is_complete,
        can_advance=is_complete,
        message=message
    )
