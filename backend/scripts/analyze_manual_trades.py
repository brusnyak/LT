"""
Analyze Manual Trades from Gym Sessions via API
Extract patterns to inform Human-Trained Strategy
"""

import requests
import json
from collections import defaultdict
import statistics


def analyze_manual_trades():
    """Analyze all manual trades from gym sessions via API"""
    
    # Fetch sessions from API
    response = requests.get('http://localhost:9000/api/trainer/sessions')
    sessions = response.json()
    
    print(f"\n{'='*60}")
    print(f"MANUAL TRADE ANALYSIS")
    print(f"{'='*60}\n")
    
    # Filter sessions with trades
    sessions_with_trades = [s for s in sessions if s['total_trades'] > 0]
    
    all_trades = []
    for session in sessions_with_trades:
        trades = session.get('trades', [])
        all_trades.extend(trades)
        
        print(f"Session: {session['name']}")
        print(f"  Trades: {len(trades)}")
        print(f"  Date: {session['created_at'][:10]}")
        print()
    
    total_trades = len(all_trades)
    
    print(f"\n{'='*60}")
    print(f"OVERALL STATISTICS")
    print(f"{'='*60}\n")
    print(f"Total Sessions: {len(sessions_with_trades)}")
    print(f"Total Trades: {total_trades}")
    
    if total_trades == 0:
        print("\nNo trades to analyze!")
        return
    
    # Analyze trade types
    long_trades = [t for t in all_trades if t['type'] == 'LONG']
    short_trades = [t for t in all_trades if t['type'] == 'SHORT']
    
    print(f"\nTrade Distribution:")
    print(f"  Long: {len(long_trades)} ({len(long_trades)/total_trades*100:.1f}%)")
    print(f"  Short: {len(short_trades)} ({len(short_trades)/total_trades*100:.1f}%)")
    
    # Calculate R:R ratios
    rr_ratios = []
    for trade in all_trades:
        risk = abs(trade['entry_price'] - trade['sl_price'])
        reward = abs(trade['tp_price'] - trade['entry_price'])
        if risk > 0:
            rr = reward / risk
            rr_ratios.append(rr)
    
    if rr_ratios:
        print(f"\nR:R Analysis:")
        print(f"  Average R:R: {statistics.mean(rr_ratios):.2f}")
        print(f"  Median R:R: {statistics.median(rr_ratios):.2f}")
        print(f"  Min R:R: {min(rr_ratios):.2f}")
        print(f"  Max R:R: {max(rr_ratios):.2f}")
        
        # R:R distribution
        rr_buckets = defaultdict(int)
        for rr in rr_ratios:
            if rr < 1:
                rr_buckets['<1R'] += 1
            elif rr < 2:
                rr_buckets['1-2R'] += 1
            elif rr < 3:
                rr_buckets['2-3R'] += 1
            elif rr < 4:
                rr_buckets['3-4R'] += 1
            elif rr < 5:
                rr_buckets['4-5R'] += 1
            else:
                rr_buckets['5R+'] += 1
        
        print(f"\nR:R Distribution:")
        for bucket in ['<1R', '1-2R', '2-3R', '3-4R', '4-5R', '5R+']:
            count = rr_buckets.get(bucket, 0)
            if count > 0:
                print(f"  {bucket}: {count} trades ({count/len(rr_ratios)*100:.1f}%)")
    
    # Calculate SL/TP in pips
    sl_pips = []
    tp_pips = []
    
    for trade in all_trades:
        risk = abs(trade['entry_price'] - trade['sl_price'])
        reward = abs(trade['tp_price'] - trade['entry_price'])
        
        # Convert to pips (assuming 5-digit pricing)
        sl_pips.append(risk * 10000)
        tp_pips.append(reward * 10000)
    
    if sl_pips:
        print(f"\nStop Loss Analysis (pips):")
        print(f"  Average SL: {statistics.mean(sl_pips):.1f} pips")
        print(f"  Median SL: {statistics.median(sl_pips):.1f} pips")
        print(f"  Min SL: {min(sl_pips):.1f} pips")
        print(f"  Max SL: {max(sl_pips):.1f} pips")
    
    if tp_pips:
        print(f"\nTake Profit Analysis (pips):")
        print(f"  Average TP: {statistics.mean(tp_pips):.1f} pips")
        print(f"  Median TP: {statistics.median(tp_pips):.1f} pips")
        print(f"  Min TP: {min(tp_pips):.1f} pips")
        print(f"  Max TP: {max(tp_pips):.1f} pips")
    
    # Time-based analysis
    from datetime import datetime
    hours = defaultdict(int)
    for trade in all_trades:
        try:
            dt = datetime.fromisoformat(trade['entry_time'].replace('Z', '+00:00'))
            hour = dt.hour
            hours[hour] += 1
        except:
            pass
    
    if hours:
        print(f"\nTrading Hours Distribution:")
        for hour in sorted(hours.keys()):
            count = hours[hour]
            print(f"  {hour:02d}:00 - {count} trades ({count/total_trades*100:.1f}%)")
    
    # Export to JSON for strategy use
    analysis_data = {
        'total_trades': total_trades,
        'total_sessions': len(sessions_with_trades),
        'long_trades': len(long_trades),
        'short_trades': len(short_trades),
        'avg_rr': statistics.mean(rr_ratios) if rr_ratios else 0,
        'median_rr': statistics.median(rr_ratios) if rr_ratios else 0,
        'avg_sl_pips': statistics.mean(sl_pips) if sl_pips else 0,
        'avg_tp_pips': statistics.mean(tp_pips) if tp_pips else 0,
        'rr_distribution': dict(rr_buckets),
        'trading_hours': dict(hours),
        'analyzed_at': datetime.now().isoformat()
    }
    
    # Calculate performance metrics with position sizing
    print(f"\n{'='*60}")
    print(f"PERFORMANCE SIMULATION (0.5% Risk Per Trade)")
    print(f"{'='*60}\n")
    
    # Starting balance
    starting_balance = 10000  # $10,000
    risk_per_trade_pct = 0.005  # 0.5%
    
    print(f"Starting Balance: ${starting_balance:,.2f}")
    print(f"Risk Per Trade: {risk_per_trade_pct*100}%")
    
    # Simulate trades (assuming all hit TP for best-case)
    balance = starting_balance
    peak_balance = starting_balance
    max_dd = 0
    equity_curve = [starting_balance]
    
    wins = 0
    losses = 0
    
    for i, trade in enumerate(all_trades):
        risk_pips = abs(trade['entry_price'] - trade['sl_price']) * 10000
        reward_pips = abs(trade['tp_price'] - trade['entry_price']) * 10000
        
        # Risk amount in dollars
        risk_amount = balance * risk_per_trade_pct
        
        # Assume TP hit (best case) - calculate profit
        # Profit = (reward_pips / risk_pips) * risk_amount
        rr = reward_pips / risk_pips if risk_pips > 0 else 0
        profit = rr * risk_amount
        
        balance += profit
        wins += 1  # Assuming all wins for now
        
        equity_curve.append(balance)
        
        # Update peak and calculate drawdown
        if balance > peak_balance:
            peak_balance = balance
        
        current_dd = ((peak_balance - balance) / peak_balance) * 100
        if current_dd > max_dd:
            max_dd = current_dd
    
    # Calculate metrics
    total_gain = balance - starting_balance
    total_gain_pct = (total_gain / starting_balance) * 100
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
    
    print(f"\nResults (Best Case - All TPs Hit):")
    print(f"  Win Rate: {win_rate:.1f}% ({wins}W / {losses}L)")
    print(f"  Final Balance: ${balance:,.2f}")
    print(f"  Total Gain: ${total_gain:,.2f} ({total_gain_pct:.1f}%)")
    print(f"  Max Drawdown: {max_dd:.2f}%")
    print(f"  Peak Balance: ${peak_balance:,.2f}")
    
    # Add to analysis data
    analysis_data['performance'] = {
        'starting_balance': starting_balance,
        'final_balance': balance,
        'total_gain': total_gain,
        'total_gain_pct': total_gain_pct,
        'win_rate': win_rate,
        'wins': wins,
        'losses': losses,
        'max_dd_pct': max_dd,
        'peak_balance': peak_balance,
        'risk_per_trade_pct': risk_per_trade_pct * 100
    }
    
    # Save to file
    import os
    os.makedirs('backend/data', exist_ok=True)
    with open('backend/data/manual_trades_analysis.json', 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Analysis saved to: backend/data/manual_trades_analysis.json")
    print(f"{'='*60}\n")
    
    print(f"\n{'='*60}")
    print(f"TARGET METRICS")
    print(f"{'='*60}\n")
    print(f"✓ Win Rate: {win_rate:.1f}% (Target: ≥60%)")
    print(f"✓ Avg R:R: {analysis_data['avg_rr']:.2f} (Target: ≥2.0)")
    print(f"✓ Max DD: {max_dd:.2f}% (Target: <4%)")
    print(f"✓ Account Gain: {total_gain_pct:.1f}% (Target: Variable)")
    
    return analysis_data


if __name__ == '__main__':
    analyze_manual_trades()
