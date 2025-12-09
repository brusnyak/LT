"""
Backtest Human-Trained Strategy on ALL Available CSV Data
Handles different CSV formats (headers/no-headers, comma/tab)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
import json
from datetime import datetime
from app.strategies.human_trained_strategy import HumanTrainedStrategy

# Configuration
FILES_TO_TEST = [
    {'name': 'EURUSD', 'path': 'archive/charts/forex/EURUSD15.csv', 'has_header': True, 'sep': ','},
    {'name': 'GBPUSD', 'path': 'archive/charts/forex/GBPUSD15.csv', 'has_header': False, 'sep': '\t'},
    {'name': 'XAUUSD', 'path': 'archive/charts/metals/XAUUSD15.csv', 'has_header': False, 'sep': '\t'},
    {'name': 'USDCAD', 'path': 'archive/charts/forex/USDCAD15.csv', 'has_header': False, 'sep': '\t'},
]

def load_data(file_config):
    """Load and normalize data from CSV"""
    path = file_config['path']
    if not os.path.exists(path):
        print(f"⚠ File not found: {path}")
        return None
        
    try:
        if file_config['has_header']:
            df = pd.read_csv(path, sep=file_config['sep'])
        else:
            # Manually assign headers for files without them
            # Format appears to be: Time, Open, High, Low, Close, Volume
            df = pd.read_csv(path, sep=file_config['sep'], header=None, 
                           names=['time', 'open', 'high', 'low', 'close', 'volume'])
            
        # Ensure column names are lowercase
        df.columns = df.columns.str.lower()
        
        # Parse time column
        # Try different formats
        try:
            df['time'] = pd.to_datetime(df['time'])
        except:
            # Sometimes time might need specific format parsing
            pass
            
        return df
    except Exception as e:
        print(f"⚠ Error loading {path}: {e}")
        return None

def run_backtest(strategy, df, symbol):
    """Run backtest on a single dataframe"""
    
    # Backtest parameters
    starting_balance = 10000
    risk_per_trade_pct = 0.005  # 0.5%
    balance = starting_balance
    peak_balance = starting_balance
    max_dd = 0
    
    trades = []
    open_trades = []
    
    # Run on last 10000 candles or full length if shorter
    limit = min(10000, len(df))
    test_data = df.tail(limit).reset_index(drop=True)
    
    print(f"  Running on {limit} candles ({test_data['time'].iloc[0]} to {test_data['time'].iloc[-1]})...")
    
    for i in range(100, len(test_data)):
        # Get historical data up to current point
        hist_data = test_data.iloc[:i]
        current_candle = test_data.iloc[i]
        
        # Generate signals every 5 candles (more frequent checks)
        if i % 5 == 0:
            # We pass the same data for H4/M15/M5 for now as a simplification
            # In a real scenario, we would resample
            signals = strategy.generate_signals(symbol, hist_data, hist_data, hist_data)
            
            # Open new trades from signals
            for signal in signals[:1]:  # Take only best signal
                # Check if we already have an open trade in same direction
                has_same_direction = any(t['type'] == signal['type'] for t in open_trades)
                if not has_same_direction:
                    # Calculate position size
                    risk_amount = balance * risk_per_trade_pct
                    risk_pips = abs(signal['entry'] - signal['sl']) * 10000
                    
                    if risk_pips == 0: continue
                    
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
                    
    return {
        'symbol': symbol,
        'trades': trades,
        'final_balance': balance,
        'max_dd': max_dd,
        'total_gain_pct': (balance - starting_balance) / starting_balance * 100
    }

def main():
    print(f"\n{'='*60}")
    print(f"MULTI-PAIR BACKTEST: HUMAN-TRAINED STRATEGY")
    print(f"{'='*60}\n")
    
    strategy = HumanTrainedStrategy()
    results = []
    
    for config in FILES_TO_TEST:
        print(f"Testing {config['name']}...")
        df = load_data(config)
        if df is not None:
            res = run_backtest(strategy, df, config['name'])
            results.append(res)
            
            # Print individual result
            wins = len([t for t in res['trades'] if t['outcome'] == 'WIN'])
            losses = len([t for t in res['trades'] if t['outcome'] == 'LOSS'])
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0
            
            print(f"  Trades: {total} ({wins}W / {losses}L)")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  Gain: {res['total_gain_pct']:.2f}%")
            print(f"  Max DD: {res['max_dd']:.2f}%")
            print("")
            
    # Global Summary
    print(f"{'='*60}")
    print(f"GLOBAL SUMMARY")
    print(f"{'='*60}\n")
    
    total_trades = sum(len(r['trades']) for r in results)
    total_wins = sum(len([t for t in r['trades'] if t['outcome'] == 'WIN']) for r in results)
    global_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    print(f"Total Trades: {total_trades}")
    print(f"Global Win Rate: {global_win_rate:.1f}%")
    
    print("\nPerformance by Pair:")
    for r in results:
        wins = len([t for t in r['trades'] if t['outcome'] == 'WIN'])
        total = len(r['trades'])
        wr = (wins / total * 100) if total > 0 else 0
        print(f"  {r['symbol']}: {wr:.1f}% WR | {r['total_gain_pct']:.2f}% Gain | {r['max_dd']:.2f}% DD")

if __name__ == "__main__":
    main()
