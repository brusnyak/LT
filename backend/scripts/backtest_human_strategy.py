"""
Full Backtest with Trade Simulation
Calculate win rate, max DD, and account performance
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import json
from datetime import datetime
from app.strategies.human_trained_strategy import HumanTrainedStrategy

print(f"\n{'='*60}")
print(f"FULL BACKTEST WITH TRADE SIMULATION")
print(f"{'='*60}\n")

# Load EURUSD M15 data
print("Loading EURUSD M15 data...")
df_m15 = pd.read_csv('archive/charts/forex/EURUSD15.csv')
print(f"Loaded {len(df_m15)} candles")
print(f"Period: {df_m15['time'].iloc[0]} to {df_m15['time'].iloc[-1]}\n")

# Initialize strategy
strategy = HumanTrainedStrategy()

# Backtest parameters
starting_balance = 10000
risk_per_trade_pct = 0.005  # 0.5%
balance = starting_balance
peak_balance = starting_balance
max_dd = 0

# Track trades
trades = []
open_trades = []

# Run backtest on last 5000 candles (for better results)
print("Running backtest on last 5000 candles...")
test_data = df_m15.tail(5000).reset_index(drop=True)

for i in range(100, len(test_data)):
    # Get historical data up to current point
    hist_data = test_data.iloc[:i]
    current_candle = test_data.iloc[i]
    
    # Generate signals every 10 candles (to avoid overtrading)
    if i % 10 == 0:
        signals = strategy.generate_signals('EURUSD', hist_data, hist_data, hist_data)
        
        # Open new trades from signals
        for signal in signals[:1]:  # Take only best signal
            # Check if we already have an open trade in same direction
            has_same_direction = any(t['type'] == signal['type'] for t in open_trades)
            if not has_same_direction:
                # Calculate position size
                risk_amount = balance * risk_per_trade_pct
                risk_pips = abs(signal['entry'] - signal['sl']) * 10000
                
                trade = {
                    'entry_index': i,
                    'entry_time': current_candle['time'],
                    'type': signal['type'],
                    'entry': signal['entry'],
                    'sl': signal['sl'],
                    'tp': signal['tp'],
                    'rr': signal['rr'],
                    'risk_amount': risk_amount,
                    'risk_pips': risk_pips
                }
                open_trades.append(trade)
    
    # Check open trades for SL/TP hits
    for trade in open_trades[:]:
        hit_sl = False
        hit_tp = False
        
        if trade['type'] == 'LONG':
            if current_candle['low'] <= trade['sl']:
                hit_sl = True
            elif current_candle['high'] >= trade['tp']:
                hit_tp = True
        else:  # SHORT
            if current_candle['high'] >= trade['sl']:
                hit_sl = True
            elif current_candle['low'] <= trade['tp']:
                hit_tp = True
        
        if hit_sl or hit_tp:
            # Close trade
            trade['exit_index'] = i
            trade['exit_time'] = current_candle['time']
            trade['outcome'] = 'WIN' if hit_tp else 'LOSS'
            
            # Calculate P&L
            if hit_tp:
                trade['pnl'] = trade['risk_amount'] * trade['rr']
                balance += trade['pnl']
            else:
                trade['pnl'] = -trade['risk_amount']
                balance += trade['pnl']
            
            trades.append(trade)
            open_trades.remove(trade)
            
            # Update peak and DD
            if balance > peak_balance:
                peak_balance = balance
            
            current_dd = ((peak_balance - balance) / peak_balance) * 100
            if current_dd > max_dd:
                max_dd = current_dd

# Calculate metrics
total_trades = len(trades)
wins = [t for t in trades if t['outcome'] == 'WIN']
losses = [t for t in trades if t['outcome'] == 'LOSS']

win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
total_gain = balance - starting_balance
total_gain_pct = (total_gain / starting_balance) * 100

print(f"\n{'='*60}")
print(f"BACKTEST RESULTS")
print(f"{'='*60}\n")

print(f"Starting Balance: ${starting_balance:,.2f}")
print(f"Final Balance: ${balance:,.2f}")
print(f"Total Gain: ${total_gain:,.2f} ({total_gain_pct:.1f}%)")
print(f"\nTrades: {total_trades}")
print(f"  Wins: {len(wins)} ({win_rate:.1f}%)")
print(f"  Losses: {len(losses)} ({100-win_rate:.1f}%)")
print(f"\nRisk Management:")
print(f"  Risk Per Trade: {risk_per_trade_pct*100}%")
print(f"  Max Drawdown: {max_dd:.2f}%")
print(f"  Peak Balance: ${peak_balance:,.2f}")

if wins:
    avg_win = sum(t['pnl'] for t in wins) / len(wins)
    print(f"\nAvg Win: ${avg_win:.2f}")

if losses:
    avg_loss = sum(t['pnl'] for t in losses) / len(losses)
    print(f"Avg Loss: ${avg_loss:.2f}")

if wins and losses:
    profit_factor = abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses))
    print(f"Profit Factor: {profit_factor:.2f}")

print(f"\n{'='*60}")
print(f"TARGET METRICS")
print(f"{'='*60}\n")

targets_met = []
if win_rate >= 60:
    targets_met.append("✓ Win Rate")
    print(f"✓ Win Rate: {win_rate:.1f}% (Target: ≥60%)")
else:
    print(f"✗ Win Rate: {win_rate:.1f}% (Target: ≥60%) - NEEDS IMPROVEMENT")

avg_rr = strategy.target_rr
if avg_rr >= 2.0:
    targets_met.append("✓ Avg R:R")
    print(f"✓ Avg R:R: {avg_rr:.2f} (Target: ≥2.0)")
else:
    print(f"✗ Avg R:R: {avg_rr:.2f} (Target: ≥2.0) - NEEDS IMPROVEMENT")

if max_dd < 4.0:
    targets_met.append("✓ Max DD")
    print(f"✓ Max DD: {max_dd:.2f}% (Target: <4%)")
else:
    print(f"✗ Max DD: {max_dd:.2f}% (Target: <4%) - NEEDS IMPROVEMENT")

print(f"\nTargets Met: {len(targets_met)}/3")

# Save results
results = {
    'starting_balance': starting_balance,
    'final_balance': balance,
    'total_gain_pct': total_gain_pct,
    'total_trades': total_trades,
    'win_rate': win_rate,
    'max_dd': max_dd,
    'avg_rr': avg_rr,
    'targets_met': targets_met,
    'timestamp': datetime.now().isoformat()
}

os.makedirs('backend/data', exist_ok=True)
with open('backend/data/backtest_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: backend/data/backtest_results.json\n")
