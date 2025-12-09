"""
Rule Checker Module
Centralized rule enforcement for prop firm challenges

Rules enforced:
- Daily Loss Limit: 7% of starting balance
- Total Drawdown: 12% of starting balance
- Minimum R:R: 2:1 per trade
- Max Positions: 2 concurrent trades
- Risk per Trade: 0.5% of balance
"""
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.db.challenge import Challenge
from app.models.db.trade import Trade


def check_minimum_rr(entry_price: float, sl_price: float, tp_price: float, trade_type: str, min_rr: float = 2.0) -> tuple[bool, str]:
    """
    Check if trade meets minimum R:R requirement
    
    Returns: (is_valid, error_message)
    """
    try:
        if trade_type == "LONG":
            risk = abs(entry_price - sl_price)
            reward = abs(tp_price - entry_price)
        else:  # SHORT
            risk = abs(sl_price - entry_price)
            reward = abs(entry_price - tp_price)
        
        if risk == 0:
            return False, "Invalid trade: SL cannot equal entry price"
        
        rr = reward / risk
        
        # Use < instead of <= to make minimum inclusive (2.0 is acceptable)
        if rr < min_rr - 0.01:  # Small tolerance for floating point comparison
            return False, f"Trade R:R {rr:.2f} below minimum {min_rr:.1f}"
        
        return True, ""
    
    except Exception as e:
        return False, f"Error calculating R:R: {str(e)}"


def check_max_positions(challenge: Challenge, db: Session) -> tuple[bool, str]:
    """
    Check if challenge has reached max concurrent positions
    
    Returns: (can_add_trade, error_message)
    """
    active_trades = db.query(Trade).filter(
        Trade.challenge_id == challenge.id,
        Trade.outcome == 'ACTIVE'
    ).count()
    
    if active_trades >= challenge.max_positions:
        return False, f"Max concurrent positions ({challenge.max_positions}) reached"
    
    return True, ""


def check_risk_per_trade(challenge: Challenge, risk_amount: float) -> tuple[bool, str]:
    """
    Check if trade risk is within allowed percentage
    
    Returns: (is_valid, error_message)
    """
    max_risk = challenge.starting_balance * (challenge.risk_per_trade / 100)
    
    if risk_amount > max_risk:
        return False, f"Risk ${risk_amount:.2f} exceeds max ${max_risk:.2f} ({challenge.risk_per_trade}%)"
    
    return True, ""


def check_daily_loss_limit(challenge: Challenge, db: Session) -> tuple[bool, str, float]:
    """
    Check if daily loss limit has been exceeded
    
    Returns: (is_within_limit, breach_message, daily_pnl)
    """
    today = datetime.utcnow().date()
    
    # Get all trades closed today
    today_trades = db.query(Trade).filter(
        Trade.challenge_id == challenge.id,
        func.date(Trade.close_time) == today,
        Trade.pnl.isnot(None)
    ).all()
    
    daily_pnl = sum(t.pnl for t in today_trades)
    max_daily_loss = challenge.starting_balance * (challenge.daily_loss_limit / 100)
    
    if daily_pnl <= -max_daily_loss:
        return False, f"Daily loss limit exceeded: ${abs(daily_pnl):.2f} >= ${max_daily_loss:.2f} ({challenge.daily_loss_limit}%)", daily_pnl
    
    return True, "", daily_pnl


def check_total_drawdown(challenge: Challenge) -> tuple[bool, str, float]:
    """
    Check if total drawdown limit has been exceeded
    
    Returns: (is_within_limit, breach_message, current_drawdown)
    """
    max_drawdown_amount = challenge.starting_balance * (challenge.max_drawdown / 100)
    current_drawdown = max(0, challenge.starting_balance - challenge.current_balance)
    
    if current_drawdown >= max_drawdown_amount:
        return False, f"Total drawdown limit exceeded: ${current_drawdown:.2f} >= ${max_drawdown_amount:.2f} ({challenge.max_drawdown}%)", current_drawdown
    
    return True, "", current_drawdown


def check_all_rules_on_trade_close(challenge: Challenge, trade: Trade, db: Session) -> tuple[bool, str]:
    """
    Check all rules when closing a trade
    
    Returns: (is_valid, breach_reason)
    """
    # Check daily loss limit
    daily_ok, daily_msg, _ = check_daily_loss_limit(challenge, db)
    if not daily_ok:
        return False, daily_msg
    
    # Check total drawdown
    drawdown_ok, drawdown_msg, _ = check_total_drawdown(challenge)
    if not drawdown_ok:
        return False, drawdown_msg
    
    return True, ""


def check_all_rules_on_trade_accept(
    challenge: Challenge,
    entry_price: float,
    sl_price: float,
    tp_price: float,
    trade_type: str,
    risk_amount: float,
    db: Session
) -> tuple[bool, str]:
    """
    Check all rules when accepting a new trade
    
    Returns: (is_valid, error_message)
    """
    # Check minimum R:R
    rr_ok, rr_msg = check_minimum_rr(entry_price, sl_price, tp_price, trade_type)
    if not rr_ok:
        return False, rr_msg
    
    # Check max positions
    positions_ok, positions_msg = check_max_positions(challenge, db)
    if not positions_ok:
        return False, positions_msg
    
    # Check risk per trade
    risk_ok, risk_msg = check_risk_per_trade(challenge, risk_amount)
    if not risk_ok:
        return False, risk_msg
    
    return True, ""
