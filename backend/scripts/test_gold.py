"""
Quick test on XAUUSD only to verify Gold pip sizing
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from app.strategies.human_trained_strategy import HumanTrainedStrategy

print("\n" + "="*60)
print("XAUUSD GOLD TEST - Verifying Pip Size")
print("="*60 + "\n")

# Load XAUUSD data
df = pd.read_csv('archive/charts/metals/XAUUSD15.csv', sep='\t', header=None,
                 names=['time', 'open', 'high', 'low', 'close', 'volume'])

print(f"Loaded {len(df)} candles")
print(f"Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
print(f"Avg candle range: ${(df['high'] - df['low']).mean():.2f}\n")

strategy = HumanTrainedStrategy()
pip_size = strategy._get_pip_size('XAUUSD')

print(f"Strategy Parameters for XAUUSD:")
print(f"  Pip Size: ${pip_size}")
print(f"  SL: {strategy.avg_sl_pips} pips × ${pip_size} = ${strategy.avg_sl_pips * pip_size:.2f}")
print(f"  TP: {strategy.avg_tp_pips} pips × ${pip_size} = ${strategy.avg_tp_pips * pip_size:.2f}")
print(f"  Target R:R: {strategy.target_rr}\n")

# Quick backtest on last 1000 candles
test_data = df.tail(1000).reset_index(drop=True)
starting_balance = 10000
balance = starting_balance
risk_pct = 0.005

trades = []
open_trades = []

for i in range(100, len(test_data)):
    if i % 5 == 0:
        hist = test_data.iloc[:i]
        signals = strategy.generate_signals('XAUUSD', hist, hist, hist)
        
        for sig in signals[:1]:
            if not any(t['type'] == sig['type'] for t in open_trades):
                risk_amt = balance * risk_pct
                trade = {
                    'entry_idx': i,
                    'type': sig['type'],
                    'entry': sig['entry'],
                    'sl': sig['sl'],
                    'tp': sig['tp'],
                    'rr': sig['rr'],
                    'risk_amt': risk_amt
                }
                open_trades.append(trade)
    
    candle = test_data.iloc[i]
    for trade in open_trades[:]:
        hit_sl = hit_tp = False
        
        if trade['type'] == 'LONG':
            if candle['low'] <= trade['sl']:
                hit_sl = True
            elif candle['high'] >= trade['tp']:
                hit_tp = True
        else:
            if candle['high'] >= trade['sl']:
                hit_sl = True
            elif candle['low'] <= trade['tp']:
                hit_tp = True
        
        if hit_sl or hit_tp:
            trade['outcome'] = 'WIN' if hit_tp else 'LOSS'
            trade['pnl'] = trade['risk_amt'] * trade['rr'] if hit_tp else -trade['risk_amt']
            balance += trade['pnl']
            trades.append(trade)
            open_trades.remove(trade)

wins = len([t for t in trades if t['outcome'] == 'WIN'])
total = len(trades)
wr = (wins / total * 100) if total > 0 else 0
gain_pct = (balance - starting_balance) / starting_balance * 100

print(f"Quick Backtest Results (1000 candles):")
print(f"  Trades: {total} ({wins}W / {total-wins}L)")
print(f"  Win Rate: {wr:.1f}%")
print(f"  Account: ${starting_balance:,.0f} → ${balance:,.0f}")
print(f"  Gain: {gain_pct:.1f}%\n")

if total > 0:
    print("Sample Trades:")
    for t in trades[:3]:
        sl_size = abs(t['entry'] - t['sl'])
        tp_size = abs(t['tp'] - t['entry'])
        print(f"  {t['type']}: Entry=${t['entry']:.2f}, SL=${t['sl']:.2f} (${sl_size:.2f}), TP=${t['tp']:.2f} (${tp_size:.2f}), R:R={t['rr']:.1f} → {t['outcome']}")
