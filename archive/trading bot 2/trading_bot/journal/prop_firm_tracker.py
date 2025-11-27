import logging
from datetime import datetime, timedelta
import os
import sqlite3
from typing import Dict, Optional, List
from dataclasses import dataclass

from flask import json

logger = logging.getLogger(__name__)

@dataclass
class PropFirmChallenge:
    """Data class for prop firm challenge parameters"""
    account_size: float
    challenge_type: str  # e.g., "Rapid", "Standard", "Evaluation"
    profit_target: float  # percentage
    max_total_loss: float  # percentage
    daily_loss_limit: float  # percentage
    profit_share: float  # percentage
    drawdown_type: str  # "Trailing" or "Fixed"
    time_limit: int  # days
    leverage: Dict[str, float]  # e.g., {"FX": 30, "Indices": 10}
    min_trading_days: int
    funded_min_trading_days: int
    payout_frequency: int  # days
    allows_copy_trading: bool
    prohibited_strategies: List[str]
    start_date: datetime
    
    @property
    def end_date(self) -> datetime:
        """Calculate the end date based on start date and time limit"""
        return self.start_date + timedelta(days=self.time_limit)
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in the challenge"""
        remaining = (self.end_date - datetime.now()).days
        return max(0, remaining)
    
    @property
    def profit_target_amount(self) -> float:
        """Calculate the profit target in account currency"""
        return self.account_size * (self.profit_target / 100)
    
    @property
    def max_loss_amount(self) -> float:
        """Calculate the maximum loss in account currency"""
        return self.account_size * (self.max_total_loss / 100)
    
    @property
    def daily_loss_amount(self) -> float:
        """Calculate the daily loss limit in account currency"""
        return self.account_size * (self.daily_loss_limit / 100)


class PropFirmTracker:
    """Tracks prop firm challenge progress"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        
    async def create_challenge(self, user_id: int, challenge_data: Dict) -> PropFirmChallenge:
        """Create a new prop firm challenge"""
        try:
            challenge = PropFirmChallenge(
                account_size=float(challenge_data.get('account_size', 10000)),
                challenge_type=challenge_data.get('challenge_type', 'Standard'),
                profit_target=float(challenge_data.get('profit_target', 10)),
                max_total_loss=float(challenge_data.get('max_total_loss', 5)),
                daily_loss_limit=float(challenge_data.get('daily_loss_limit', 4)),
                profit_share=float(challenge_data.get('profit_share', 80)),
                drawdown_type=challenge_data.get('drawdown_type', 'Trailing'),
                time_limit=int(challenge_data.get('time_limit', 30)),
                leverage=challenge_data.get('leverage', {"FX": 30, "Indices": 10, "Crypto": 2}),
                min_trading_days=int(challenge_data.get('min_trading_days', 0)),
                funded_min_trading_days=int(challenge_data.get('funded_min_trading_days', 3)),
                payout_frequency=int(challenge_data.get('payout_frequency', 14)),
                allows_copy_trading=challenge_data.get('allows_copy_trading', True),
                prohibited_strategies=challenge_data.get('prohibited_strategies', []),
                start_date=datetime.now()
            )
            
            # Save to database if available
            if self.db:
                # Implementation for database storage
                pass
                
            return challenge
            
        except Exception as e:
            logger.error(f"Error creating prop firm challenge: {e}")
            raise
    
    async def get_challenge(self, user_id: int, challenge_id: Optional[int] = None) -> PropFirmChallenge:
        """Get a prop firm challenge by ID or the active one"""
        # Implementation for retrieving challenge
        pass

    def get_active_challenge(self, user_id):
        """Get the active challenge for a user"""
        try:
            # Get the active challenge from the database
            query = "SELECT * FROM prop_firm_challenges WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1"
            result = self._execute_query(query, (user_id,))
            
            if not result:
                return None
            
            challenge_data = result[0]
            
            # Safely parse JSON fields
            def safe_json_parse(field_value, default=None):
                if not field_value:
                    return default
                try:
                    return json.loads(field_value)
                except json.JSONDecodeError:
                    # If it's already a string but not valid JSON, try to fix it
                    if isinstance(field_value, str):
                        # If it looks like a Python dict/list, try to convert it
                        if (field_value.startswith('{') and field_value.endswith('}')) or \
                        (field_value.startswith('[') and field_value.endswith(']')):
                            try:
                                # Use ast.literal_eval which is safer than eval
                                import ast
                                return ast.literal_eval(field_value)
                            except:
                                pass
                    return default
            
            # Create challenge object with safe JSON parsing
            challenge = PropFirmChallenge(
                id=challenge_data['id'],
                user_id=challenge_data['user_id'],
                prop_firm=challenge_data['prop_firm'],
                challenge_type=challenge_data['challenge_type'],
                account_size=challenge_data['account_size'],
                starting_balance=challenge_data['starting_balance'],
                current_balance=challenge_data['current_balance'],
                profit_target=challenge_data['profit_target'],
                daily_drawdown=challenge_data['daily_drawdown'],
                max_drawdown=challenge_data['max_drawdown'],
                time_limit=challenge_data['time_limit'],
                min_trading_days=challenge_data['min_trading_days'],
                leverage=safe_json_parse(challenge_data['leverage'], {}),
                allowed_instruments=safe_json_parse(challenge_data['allowed_instruments'], []),
                trading_hours=safe_json_parse(challenge_data['trading_hours'], {}),
                status=challenge_data['status'],
                start_date=challenge_data['start_date'],
                end_date=challenge_data['end_date'],
                created_at=challenge_data['created_at'],
                updated_at=challenge_data['updated_at']
            )
            
            return challenge
        except Exception as e:
            logger.error(f"Error getting active challenge: {e}", exc_info=True)
            return None



    async def update_challenge_progress(self, user_id: int, challenge_id: int, 
                                       current_balance: float, daily_pnl: float) -> Dict:
        """Update challenge progress with current account metrics"""
        try:
            challenge = await self.get_challenge(user_id, challenge_id)
            
            # Calculate metrics
            profit_loss = current_balance - challenge.account_size
            profit_loss_pct = (profit_loss / challenge.account_size) * 100
            
            # Check for violations
            daily_loss_violation = daily_pnl < -challenge.daily_loss_amount
            max_loss_violation = profit_loss < -challenge.max_loss_amount
            
            # Check for success
            challenge_completed = profit_loss >= challenge.profit_target_amount
            
            return {
                "challenge_id": challenge_id,
                "current_balance": current_balance,
                "profit_loss": profit_loss,
                "profit_loss_pct": profit_loss_pct,
                "daily_pnl": daily_pnl,
                "days_remaining": challenge.days_remaining,
                "daily_loss_violation": daily_loss_violation,
                "max_loss_violation": max_loss_violation,
                "challenge_completed": challenge_completed
            }
            
        except Exception as e:
            logger.error(f"Error updating challenge progress: {e}")
            raise