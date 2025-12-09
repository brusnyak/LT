"""
Comprehensive backtest script for Range 4H strategy across all pairs.

This script tests the CURRENT Range 4H implementation to establish baseline performance.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals

# Configuration
DATA_DIR = Path("/Users/yegor/Documents/Agency & Security Stuff/Development/SMC/archive/charts/forex")
PAIRS = ['EURUSD', 'GBPUSD', 'GBPJPY', 'USDCAD']
INITIAL_BALANCE = 50000
RISK_PER_TRADE = 0.005  # 0.5%

# Strategy variations to test
VARIATIONS = {
    'baseline': {
        'use_dynamic_tp': False,
        'use_swing_filter': False,
        'use_trend_filter': False,
        'min_rr': 1.5
    },
    'v3_swing_filter': {
        'use_dynamic_tp': True,
        'use_swing_filter': True,
        'use_trend_filter': False,
        'min_rr': 1.5
    },
    'v5_trend_filter': {
        'use_dynamic_tp': True,
        'use_swing_filter': True,
        'use_trend_filter': True,
        'min_rr': 1.5
    }
}

def load_data(pair: str):
    """Load 4H and 5M data for a pair"""
    # 4H CSV: always headerless, TAB-separated
    # Format: YYYY-MM-DD HH:MM\tOpen\tHigh...
    # We must use sep='\t' to avoid splitting the date string "YYYY-MM-DD HH:MM"
    df_4h = pd.read_csv(
        DATA_DIR / f"{pair}240.csv",
        sep='\t',
        header=None,
        names=['time', 'open', 'high', 'low', 'close', 'volume']
    )
    
    # 5M CSV: Mixed formats
    file_path_5m = DATA_DIR / f"{pair}5.csv"
    
    # Peek at the first line to determine format
    with open(file_path_5m, 'r') as f:
        first_line = f.readline()
        
    if ',' in first_line:
        # Comma separated, likely has header (EURUSD, GBPUSD)
        df_5m = pd.read_csv(file_path_5m)
        df_5m.columns = df_5m.columns.str.lower()
    else:
        # Tab/Space separated, no header (GBPJPY, USDCAD)
        # Assuming tab separated like 4H if no commas
        df_5m = pd.read_csv(
            file_path_5m,
            sep='\t',
            header=None,
            names=['time', 'open', 'high', 'low', 'close', 'volume']
        )
    
    # Convert time to datetime
    # 4H data has "YYYY-MM-DD HH:MM" format
    df_4h['time'] = pd.to_datetime(df_4h['time'])
    df_5m['time'] = pd.to_datetime(df_5m['time'])
    
    # Localize to UTC if needed
    if df_4h['time'].dt.tz is None:
        df_4h['time'] = df_4h['time'].dt.tz_localize('UTC')
    if df_5m['time'].dt.tz is None:
        df_5m['time'] = df_5m['time'].dt.tz_localize('UTC')
    
    return df_4h, df_5m

def calculate_position_size(balance: float, entry: float, sl: float, risk_pct: float = 0.005):
    """Calculate position size based on risk"""
    risk_amount = balance * risk_pct
    sl_distance = abs(entry - sl)
    if sl_distance == 0:
        return 0
    return risk_amount / sl_distance

def calculate_metrics(signals, initial_balance: float):
    """Calculate performance metrics"""
    balance = initial_balance
    equity_curve = [balance]
    peak = balance
    max_dd = 0
    
    winning_trades = 0
    losing_trades = 0
    total_rr = 0
    total_sl_pips = 0
    total_tp_pips = 0
    
    for signal in signals:
        if signal.status != 'CLOSED':
            continue
            
        # Calculate position size
        pos_size = calculate_position_size(balance, signal.price, signal.sl)
        
        # Track SL/TP in pips (1 pip = 0.0001 for most pairs, 0.01 for JPY pairs)
        pip_value = 0.01 if 'JPY' in str(signal.time) else 0.0001  # Rough estimation
        sl_pips = abs(signal.price - signal.sl) / pip_value
        tp_pips = abs(signal.tp - signal.price) / pip_value
        total_sl_pips += sl_pips
        total_tp_pips += tp_pips
        
        # Calculate P&L
        if signal.outcome in ['TP1_HIT', 'TP2_HIT']:
            # Win
            winning_trades += 1
            if signal.outcome == 'TP1_HIT':
                # Partial close at TP1, then BE stop
                reward = abs(signal.tp - signal.price)
                pnl = pos_size * reward * 0.5  # 50% at TP1
            else:
                # Full TP2
                reward1 = abs(signal.tp - signal.price)
                reward2 = abs(signal.tp2 - signal.price)
                pnl = pos_size * (reward1 * 0.5 + reward2 * 0.5)
            
            # Calculate RR
            risk = abs(signal.price - signal.sl)
            avg_reward = (abs(signal.tp - signal.price) + abs(signal.tp2 - signal.price)) / 2
            rr = avg_reward / risk if risk > 0 else 0
            total_rr += rr
        else:
            # Loss
            losing_trades += 1
            risk = abs(signal.price - signal.sl)
            pnl = -pos_size * risk
            total_rr += 0  # 0R on loss
        
        balance += pnl
        equity_curve.append(balance)
        
        # Track drawdown
        if balance > peak:
            peak = balance
        dd = ((peak - balance) / peak) * 100
        max_dd = max(max_dd, dd)
    
    total_trades = winning_trades + losing_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    avg_rr = (total_rr / total_trades) if total_trades > 0 else 0
    avg_sl_pips = (total_sl_pips / total_trades) if total_trades > 0 else 0
    avg_tp_pips = (total_tp_pips / total_trades) if total_trades > 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': round(win_rate, 2),
        'avg_rr': round(avg_rr, 2),
        'avg_sl_pips': round(avg_sl_pips, 1),
        'avg_tp_pips': round(avg_tp_pips, 1),
        'max_dd': round(max_dd, 2),
        'total_pnl': round(balance - initial_balance, 2),
        'final_balance': round(balance, 2),
        'equity_curve': equity_curve
    }

def backtest_pair(pair: str, variation_name: str, variation_config: dict):
    """Backtest a single pair with given configuration"""
    print(f"\n{'='*60}")
    print(f"Testing {pair} - {variation_name}")
    print(f"{'='*60}")
    
    # Load data
    df_4h, df_5m = load_data(pair)
    
    # Detect ranges
    ranges = detect_4h_range(df_4h)
    print(f"Detected {len(ranges)} 4H ranges")
    
    # Generate signals
    signals = analyze_5m_signals(df_5m, ranges, **variation_config)
    print(f"Generated {len(signals)} signals")
    
    # Calculate metrics
    metrics = calculate_metrics(signals, INITIAL_BALANCE)
    
    # Print results
    print(f"\nResults:")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"  Win Rate: {metrics['win_rate']}% (Target: ≥70%)")
    print(f"  Avg RR: {metrics['avg_rr']} (Target: ≥2.0)")
    print(f"  Avg SL: {metrics['avg_sl_pips']} pips")
    print(f"  Avg TP: {metrics['avg_tp_pips']} pips")
    print(f"  Max DD: {metrics['max_dd']}% (Target: <4%)")
    print(f"  Total P&L: ${metrics['total_pnl']}")
    print(f"  Final Balance: ${metrics['final_balance']}")
    
    # Check if meets targets
    meets_targets = (
        metrics['win_rate'] >= 70 and
        metrics['avg_rr'] >= 2.0 and
        metrics['max_dd'] < 4.0
    )
    print(f"\n  {'✅ MEETS TARGETS' if meets_targets else '❌ DOES NOT MEET TARGETS'}")
    
    return {
        'pair': pair,
        'variation': variation_name,
        'metrics': metrics,
        'meets_targets': meets_targets
    }

def main():
    """Run comprehensive backtest"""
    print("="*60)
    print("RANGE 4H STRATEGY - COMPREHENSIVE BACKTEST")
    print("="*60)
    print(f"Testing {len(PAIRS)} pairs × {len(VARIATIONS)} variations")
    print(f"Pairs: {', '.join(PAIRS)}")
    print(f"Variations: {', '.join(VARIATIONS.keys())}")
    
    all_results = []
    
    for variation_name, variation_config in VARIATIONS.items():
        print(f"\n\n{'#'*60}")
        print(f"VARIATION: {variation_name.upper()}")
        print(f"Config: {variation_config}")
        print(f"{'#'*60}")
        
        variation_results = []
        
        for pair in PAIRS:
            try:
                result = backtest_pair(pair, variation_name, variation_config)
                variation_results.append(result)
                all_results.append(result)
            except Exception as e:
                print(f"\n❌ Error testing {pair}: {e}")
                import traceback
                traceback.print_exc()
        
        # Summary for this variation
        print(f"\n{'='*60}")
        print(f"SUMMARY: {variation_name}")
        print(f"{'='*60}")
        
        total_trades = sum(r['metrics']['total_trades'] for r in variation_results)
        avg_win_rate = sum(r['metrics']['win_rate'] for r in variation_results) / len(variation_results) if variation_results else 0
        avg_rr = sum(r['metrics']['avg_rr'] for r in variation_results) / len(variation_results) if variation_results else 0
        avg_dd = sum(r['metrics']['max_dd'] for r in variation_results) / len(variation_results) if variation_results else 0
        pairs_meeting_targets = sum(1 for r in variation_results if r['meets_targets'])
        
        print(f"Total Trades (all pairs): {total_trades}")
        print(f"Avg Win Rate: {avg_win_rate:.2f}%")
        print(f"Avg RR: {avg_rr:.2f}")
        print(f"Avg Max DD: {avg_dd:.2f}%")
        print(f"Pairs Meeting Targets: {pairs_meeting_targets}/{len(PAIRS)}")
    
    # Save results
    output_file = f"backtest_results_range4h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'pairs': PAIRS,
            'variations': list(VARIATIONS.keys()),
            'results': all_results
        }, f, indent=2, default=str)
    
    print(f"\n\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
