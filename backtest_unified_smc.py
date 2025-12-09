#!/usr/bin/env python3
"""
Backtest Unified SMC Strategy V2

Target Metrics:
- Win Rate: >= 60%
- Risk/Reward: >= 2.0
- Max Drawdown: < 4%
"""
import sys
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.data_loader import load_candle_data
from app.strategies.unified_smc_v2 import UnifiedSMCStrategyV2
from app.models.strategy import Signal

# Available pairs from CSV data
PAIRS = ['EURUSD', 'GBPJPY', 'GBPUSD', 'USDCAD']

# Timeframes for strategy
TIMEFRAMES = {
    'H4': 1000,
    'M15': 2000,
    'M5': 5000,
    'M1': 5000
}

class BacktestEngine:
    def __init__(self, initial_balance: float = 50000, risk_per_trade: float = 0.01):
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.balance = initial_balance
        self.equity_curve = []
        self.trades = []
        self.peak_balance = initial_balance
        
    def calculate_position_size(self, entry: float, sl: float) -> float:
        """Calculate position size based on risk percentage"""
        risk_amount = self.balance * self.risk_per_trade
        sl_distance = abs(entry - sl)
        if sl_distance == 0:
            return 0
        # For forex, 1 lot = 100,000 units
        # Position size in lots
        position_size = risk_amount / sl_distance
        return position_size
    
    def execute_trade(self, signal: Signal, df: pd.DataFrame):
        """Simulate trade execution"""
        entry_price = signal.price
        sl_price = signal.sl
        tp_price = signal.tp
        
        # Calculate position size
        position_size = self.calculate_position_size(entry_price, sl_price)
        
        if position_size == 0:
            return
        
        # Find entry candle
        try:
            entry_idx = df.index.get_loc(signal.time)
        except KeyError:
            return
        
        # Simulate forward from entry
        trade_result = None
        exit_time = None
        exit_price = None
        
        for i in range(entry_idx + 1, len(df)):
            candle_high = df['high'].iloc[i]
            candle_low = df['low'].iloc[i]
            candle_time = df.index[i]
            
            if signal.type == 'LONG':
                # Check SL hit
                if candle_low <= sl_price:
                    trade_result = 'LOSS'
                    exit_price = sl_price
                    exit_time = candle_time
                    break
                # Check TP hit
                elif candle_high >= tp_price:
                    trade_result = 'WIN'
                    exit_price = tp_price
                    exit_time = candle_time
                    break
            else:  # SHORT
                # Check SL hit
                if candle_high >= sl_price:
                    trade_result = 'LOSS'
                    exit_price = sl_price
                    exit_time = candle_time
                    break
                # Check TP hit
                elif candle_low <= tp_price:
                    trade_result = 'WIN'
                    exit_price = tp_price
                    exit_time = candle_time
                    break
        
        # If no exit found, skip trade
        if trade_result is None:
            return
        
        # Calculate P&L
        if signal.type == 'LONG':
            pnl = (exit_price - entry_price) * position_size
        else:
            pnl = (entry_price - exit_price) * position_size
        
        # Update balance
        self.balance += pnl
        self.equity_curve.append({
            'time': exit_time,
            'balance': self.balance,
            'pnl': pnl
        })
        
        # Track peak for drawdown
        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        
        # Calculate RR
        risk = abs(entry_price - sl_price) * position_size
        reward = abs(exit_price - entry_price) * position_size
        rr = reward / risk if risk > 0 else 0
        
        # Store trade
        self.trades.append({
            'entry_time': signal.time,
            'exit_time': exit_time,
            'type': signal.type,
            'entry': entry_price,
            'sl': sl_price,
            'tp': tp_price,
            'exit': exit_price,
            'result': trade_result,
            'pnl': pnl,
            'rr': rr,
            'reason': signal.reason
        })
    
    def get_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_rr': 0,
                'max_dd': 0,
                'max_dd_pct': 0,
                'total_pnl': 0,
                'final_balance': self.balance
            }
        
        wins = [t for t in self.trades if t['result'] == 'WIN']
        losses = [t for t in self.trades if t['result'] == 'LOSS']
        
        win_rate = (len(wins) / len(self.trades)) * 100
        
        # Average RR
        avg_rr = sum(t['rr'] for t in self.trades) / len(self.trades)
        
        # Max Drawdown
        max_dd = 0
        for equity_point in self.equity_curve:
            dd = self.peak_balance - equity_point['balance']
            if dd > max_dd:
                max_dd = dd
        
        max_dd_pct = (max_dd / self.initial_balance) * 100
        
        total_pnl = self.balance - self.initial_balance
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': round(win_rate, 2),
            'avg_rr': round(avg_rr, 2),
            'max_dd': round(max_dd, 2),
            'max_dd_pct': round(max_dd_pct, 2),
            'total_pnl': round(total_pnl, 2),
            'final_balance': round(self.balance, 2)
        }


def backtest_pair(pair: str, strategy: UnifiedSMCStrategyV2) -> Dict:
    """Backtest a single pair"""
    print(f"\n{'='*60}")
    print(f"Backtesting {pair}...")
    print(f"{'='*60}")
    
    # Load data for all timeframes
    df_multi_tf = {}
    for tf, limit in TIMEFRAMES.items():
        try:
            df = load_candle_data(pair, tf, limit=limit, source='csv')
            df_multi_tf[tf] = df
            print(f"  Loaded {len(df)} candles for {tf}")
        except FileNotFoundError:
            print(f"  ⚠️  No data for {tf}, skipping...")
            return None
        except Exception as e:
            print(f"  ❌ Error loading {tf}: {e}")
            return None
    
    # Run strategy
    try:
        result = strategy.analyze(df_multi_tf)
        signals = result['signals']
        print(f"  Generated {len(signals)} signals")
    except Exception as e:
        print(f"  ❌ Strategy error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Backtest signals
    engine = BacktestEngine()
    execution_tf = 'M5'  # Use M5 for execution
    df_exec = df_multi_tf[execution_tf]
    
    for signal in signals:
        engine.execute_trade(signal, df_exec)
    
    # Get metrics
    metrics = engine.get_metrics()
    metrics['pair'] = pair
    
    # Print results
    print(f"\n  Results:")
    print(f"    Total Trades: {metrics['total_trades']}")
    print(f"    Win Rate: {metrics['win_rate']}%")
    print(f"    Avg RR: {metrics['avg_rr']}")
    print(f"    Max DD: {metrics['max_dd_pct']}%")
    print(f"    Total P&L: ${metrics['total_pnl']}")
    print(f"    Final Balance: ${metrics['final_balance']}")
    
    # Check if meets targets
    meets_targets = (
        metrics['win_rate'] >= 60 and
        metrics['avg_rr'] >= 2.0 and
        metrics['max_dd_pct'] < 4.0
    )
    
    if meets_targets:
        print(f"  ✅ MEETS TARGETS!")
    else:
        print(f"  ❌ Does not meet targets")
        if metrics['win_rate'] < 60:
            print(f"     - Win rate too low ({metrics['win_rate']}% < 60%)")
        if metrics['avg_rr'] < 2.0:
            print(f"     - RR too low ({metrics['avg_rr']} < 2.0)")
        if metrics['max_dd_pct'] >= 4.0:
            print(f"     - Max DD too high ({metrics['max_dd_pct']}% >= 4%)")
    
    return metrics


def main():
    """Run backtest on all pairs"""
    print("\n" + "="*60)
    print("UNIFIED SMC STRATEGY V2 BACKTEST")
    print("="*60)
    print(f"Target Metrics:")
    print(f"  - Win Rate: >= 60%")
    print(f"  - Avg RR: >= 2.0")
    print(f"  - Max DD: < 4%")
    
    strategy = UnifiedSMCStrategyV2()
    
    all_results = []
    
    for pair in PAIRS:
        metrics = backtest_pair(pair, strategy)
        if metrics:
            all_results.append(metrics)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if not all_results:
        print("❌ No successful backtests")
        return
    
    # Aggregate metrics
    total_trades = sum(m['total_trades'] for m in all_results)
    total_wins = sum(m['winning_trades'] for m in all_results)
    avg_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    avg_rr = sum(m['avg_rr'] for m in all_results) / len(all_results)
    max_dd = max(m['max_dd_pct'] for m in all_results)
    
    print(f"\nAggregate Metrics:")
    print(f"  Total Trades: {total_trades}")
    print(f"  Overall Win Rate: {avg_win_rate:.2f}%")
    print(f"  Average RR: {avg_rr:.2f}")
    print(f"  Max DD (worst pair): {max_dd:.2f}%")
    
    # Check overall targets
    meets_targets = (
        avg_win_rate >= 60 and
        avg_rr >= 2.0 and
        max_dd < 4.0
    )
    
    print(f"\n{'='*60}")
    if meets_targets:
        print("✅ STRATEGY MEETS ALL TARGETS!")
    else:
        print("❌ STRATEGY DOES NOT MEET TARGETS")
        print("\nIssues:")
        if avg_win_rate < 60:
            print(f"  - Win rate: {avg_win_rate:.2f}% (target: >= 60%)")
        if avg_rr < 2.0:
            print(f"  - Avg RR: {avg_rr:.2f} (target: >= 2.0)")
        if max_dd >= 4.0:
            print(f"  - Max DD: {max_dd:.2f}% (target: < 4%)")
    print(f"{'='*60}\n")
    
    # Save results
    output_file = 'backtest_results_unified_smc.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'pairs': all_results,
            'aggregate': {
                'total_trades': total_trades,
                'win_rate': round(avg_win_rate, 2),
                'avg_rr': round(avg_rr, 2),
                'max_dd': round(max_dd, 2),
                'meets_targets': meets_targets
            }
        }, f, indent=2)
    
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()
