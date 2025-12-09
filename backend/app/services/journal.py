
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
    
    def calculate_pnl(self, signal: Signal) -> float:
        """Calculate PnL for a closed signal"""
        if signal.outcome not in ['TP1_HIT', 'TP2_HIT', 'SL_HIT', 'TP_HIT']: # Assuming these are the "closed" outcomes
            return 0.0
            
        if not signal.close_price:
            return 0.0
            
        # Calculate PnL based on outcome
        if signal.outcome == 'TP1_HIT':
            # Partial Close: 50% at TP1, 50% at Close Price (which might be SL/BE or TP2)
            # My logic in range_4h.py sets outcome to 'TP1_HIT' if it hit TP1 then SL (BE).
            # If it hit TP2, outcome is 'TP2_HIT'.
            
            # Logic for TP1_HIT (Hit TP1, then stopped out at BE)
            # 50% @ TP1, 50% @ Entry (0 PnL)
            
            pnl_tp1 = self._calc_trade_pnl(signal.type, signal.price, signal.tp, 0.5, signal.sl)
            pnl_rest = self._calc_trade_pnl(signal.type, signal.price, signal.close_price, 0.5, signal.sl)
            return pnl_tp1 + pnl_rest

        elif signal.outcome == 'TP2_HIT':
            # Hit TP1 then TP2
            # 50% @ TP1, 50% @ TP2
            pnl_tp1 = self._calc_trade_pnl(signal.type, signal.price, signal.tp, 0.5, signal.sl)
            pnl_tp2 = self._calc_trade_pnl(signal.type, signal.price, signal.tp2, 0.5, signal.sl)
            return pnl_tp1 + pnl_tp2
            
        else:
            # Standard Close (SL hit immediately or TP hit immediately if single TP)
            return self._calc_trade_pnl(signal.type, signal.price, signal.close_price, 1.0, signal.sl)

    def _calc_trade_pnl(self, type: str, entry: float, exit: float, position_size_ratio: float, sl: float) -> float:
        # We need to know the risk distance to calculate position size
        # Position Size = Risk Amount / Stop Loss Distance
        # PnL = Position Size * (Exit - Entry)
        
        risk_amount = self.balance * RISK_PERCENT
        sl_distance = abs(entry - sl)
        
        if sl_distance == 0: # Avoid division by zero if SL is at entry
            return 0.0
            
        # Assuming 1 unit of position size is 1$ PnL per 1 unit of price movement
        # This is a simplification. In reality, it depends on instrument and lot size.
        # For now, let's define position size such that 1R is risk_amount.
        
        # If 1R is risk_amount, and 1R is sl_distance * position_size,
        # then position_size = risk_amount / sl_distance
        
        position_size = risk_amount / sl_distance
        
        pnl_per_unit = (exit - entry) * position_size
        
        if type == 'SHORT':
            pnl_per_unit = -pnl_per_unit # Invert PnL for sell trades
            
        return pnl_per_unit * position_size_ratio
    
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
            pnl = self.calculate_pnl(signal)
            
            # Calculate RR achieved
            # RR = PnL / Risk Amount
            if risk_amount > 0:
                rr_achieved = pnl / risk_amount
            
            # Update balance
            balance_after = self.balance + pnl
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
        
        # Average RR (Avg Win / Avg Loss)
        winning_r = [t.rr_achieved for t in winning_trades if t.rr_achieved]
        losing_r = [t.rr_achieved for t in losing_trades if t.rr_achieved]
        
        avg_win = sum(winning_r) / len(winning_r) if winning_r else 0.0
        avg_loss = abs(sum(losing_r) / len(losing_r)) if losing_r else 1.0 # Default to 1 if no losses
        
        if avg_loss == 0:
            avg_rr = 0.0
        else:
            avg_rr = avg_win / avg_loss
        
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
