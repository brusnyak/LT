"""Journal service for trade tracking and account management"""
import pandas as pd
from datetime import datetime
from app.models.journal import TradeRecord, AccountState, JournalStats, JournalResponse
from app.models.strategy import Signal

STARTING_BALANCE = 50000.0
RISK_PERCENT = 0.005  # 0.5%

class JournalService:
    """Manages trade journaling and account tracking"""
    
    def __init__(self):
        self.balance = STARTING_BALANCE
        self.starting_balance = STARTING_BALANCE
        self.trades = []
        self.trade_id_counter = 1
        
    def process_signals(self, signals: list[Signal], pair: str) -> JournalResponse:
        """
        Convert signals to trade records with P&L calculation
        """
        self.trades = []
        self.balance = STARTING_BALANCE
        self.trade_id_counter = 1
        
        for signal in signals:
            trade = self._signal_to_trade(signal, pair)
            self.trades.append(trade)
            
        # Calculate stats
        stats = self._calculate_stats()
        account = self._get_account_state()
        
        return JournalResponse(
            account=account,
            trades=self.trades,
            stats=stats
        )
    
    def _signal_to_trade(self, signal: Signal, pair: str) -> TradeRecord:
        """Convert a signal to a trade record with P&L"""
        # Calculate position size based on risk
        risk_amount = self.balance * RISK_PERCENT
        
        # Calculate pip/point value (simplified - assumes forex 5-decimal)
        sl_distance = abs(signal.price - signal.sl)
        
        # Position size = Risk / SL distance
        # For forex: lot size, but we'll work in $ for simplicity
        
        # Calculate P&L if trade is closed
        pnl = None
        rr_achieved = None
        balance_after = self.balance
        
        if signal.outcome:
            if signal.outcome == 'TP_HIT':
                # Won 2R
                pnl = risk_amount * 2.0
                rr_achieved = 2.0
            elif signal.outcome == 'SL_HIT':
                # Lost 1R
                pnl = -risk_amount
                rr_achieved = -1.0
            
            # Update balance
            balance_after = self.balance + pnl if pnl else self.balance
            self.balance = balance_after
        
        trade = TradeRecord(
            id=self.trade_id_counter,
            signal_time=signal.time,
            close_time=signal.close_time,
            pair=pair,
            type=signal.type,
            entry_price=signal.price,
            sl_price=signal.sl,
            tp_price=signal.tp,
            close_price=signal.close_price,
            outcome=signal.outcome if signal.outcome else 'ACTIVE',
            risk_amount=risk_amount,
            pnl=pnl,
            rr_achieved=rr_achieved,
            balance_before=self.balance - (pnl if pnl else 0),
            balance_after=balance_after
        )
        
        self.trade_id_counter += 1
        return trade
    
    def _calculate_stats(self) -> JournalStats:
        """Calculate trading statistics"""
        closed_trades = [t for t in self.trades if t.outcome != 'ACTIVE']
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]
        
        total = len(closed_trades)
        wins = len(winning_trades)
        losses = len(losing_trades)
        
        win_rate = (wins / total * 100) if total > 0 else 0.0
        
        # Average RR
        rr_values = [t.rr_achieved for t in closed_trades if t.rr_achieved]
        avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0
        
        # Total P&L
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl) if closed_trades else 0.0
        
        # Max drawdown (peak to trough)
        balances = [STARTING_BALANCE] + [t.balance_after for t in closed_trades if t.balance_after]
        max_balance = STARTING_BALANCE
        max_dd = 0.0
        
        for balance in balances:
            if balance > max_balance:
                max_balance = balance
            dd = (max_balance - balance) / max_balance * 100
            if dd > max_dd:
                max_dd = dd
        
        # Consecutive wins/losses
        max_cons_wins = 0
        max_cons_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in closed_trades:
            if trade.pnl and trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_cons_wins = max(max_cons_wins, current_wins)
            elif trade.pnl and trade.pnl < 0:
                current_losses += 1
                current_wins = 0
                max_cons_losses = max(max_cons_losses, current_losses)
        
        # Best/worst trades
        pnls = [t.pnl for t in closed_trades if t.pnl]
        best_trade = max(pnls) if pnls else None
        worst_trade = min(pnls) if pnls else None
        
        return JournalStats(
            total_trades=total,
            winning_trades=wins,
            losing_trades=losses,
            win_rate=win_rate,
            avg_rr=avg_rr,
            total_pnl=total_pnl,
            max_drawdown=max_dd,
            max_consecutive_wins=max_cons_wins,
            max_consecutive_losses=max_cons_losses,
            best_trade=best_trade,
            worst_trade=worst_trade
        )
    
    def _get_account_state(self) -> AccountState:
        """Get current account state"""
        closed_trades = [t for t in self.trades if t.outcome != 'ACTIVE']
        active_trades = [t for t in self.trades if t.outcome == 'ACTIVE']
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]
        
        total_risk = sum(t.risk_amount for t in active_trades)
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl) if closed_trades else 0.0
        
        stats = self._calculate_stats()
        
        # Daily P&L (simplified - just use total for now)
        daily_pnl = total_pnl
        
        return AccountState(
            balance=self.balance,
            starting_balance=self.starting_balance,
            equity=self.balance,  # Simplified - doesn't account for floating P&L
            total_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            active_trades=len(active_trades),
            total_pnl=total_pnl,
            total_risk=total_risk,
            win_rate=stats.win_rate,
            avg_rr=stats.avg_rr,
            max_drawdown=stats.max_drawdown,
            daily_pnl=daily_pnl
        )

# Global instance
journal_service = JournalService()
