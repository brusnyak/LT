#!/usr/bin/env python3
"""
Optimized Multi-Pair Backtest for MVP Strategy
Tests on: EURUSD, GBPJPY, USDCAD, XAUUSD (Gold)
Uses smaller data windows for faster iteration
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from app.strategies.unified_mvp import UnifiedMVPStrategy
from app.core.data_loader import load_candle_data
from app.services.journal import JournalService

def backtest_pair(pair, strategy, initial_balance=10000, risk_pct=0.005):
    """
    Backtest MVP strategy on a single pair
    
    Returns:
        dict with performance metrics
    """
    print(f"\n{'='*70}")
    print(f"Backtesting {pair}")
    print(f"{'='*70}")
    
    try:
        # Load data with smaller windows for speed
        # Last ~2 months of data
        df_h4 = load_candle_data(pair, 'H4', limit=200)   # ~33 days
        df_m15 = load_candle_data(pair, 'M15', limit=1000) # ~10 days
        df_m5 = load_candle_data(pair, 'M5', limit=2000)   # ~7 days
        
        print(f"✅ Loaded data:")
        print(f"   H4: {len(df_h4)} candles ({df_h4.index[0]} to {df_h4.index[-1]})")
        print(f"   M15: {len(df_m15)} candles")
        print(f"   M5: {len(df_m5)} candles")
        
        # Run strategy analysis to get trend and setup info
        print(f"\n📊 Running strategy analysis...")
        result = strategy.analyze({
            'H4': df_h4,
            'M15': df_m15,
            'M5': df_m5
        })
        
        metadata = result.get('metadata', {})
        print(f"   H4 Trend: {metadata.get('h4_trend', 'N/A').upper()}")
        print(f"   M15 Quality OBs: {metadata.get('m15_quality_obs', 0)}")
        print(f"   Liquidity Zones: {metadata.get('m15_liquidity_zones', 0)}")
        
        # For backtesting, we need to simulate going through candles
        # This is simplified - just get signals from current state
        signals = result.get('signals', [])
        
        if not signals:
            print(f"\n⚠️  No signals generated")
            print(f"   Market: {metadata.get('h4_trend')} - Strategy waiting for quality setup")
            return {
                'pair': pair,
                'signals': 0,
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'avg_rr': 0,
                'max_dd': 0,
                'final_balance': initial_balance,
                'pnl': 0,
                'pnl_pct': 0,
                'h4_trend': metadata.get('h4_trend', 'N/A')
            }
        
        print(f"\n✅ Generated {len(signals)} signal(s)")
        
        # Process signals with journal
        journal = JournalService()
        journal.balance = initial_balance
        journal.starting_balance = initial_balance
        
        perf = journal.process_signals(signals, pair)
        
        # Calculate metrics
        total_trades = len(perf.closed_trades)
        wins = sum(1 for t in perf.closed_trades if t.pnl > 0)
        losses = sum(1 for t in perf.closed_trades if t.pnl < 0)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate avg RR
        winning_trades = [t for t in perf.closed_trades if t.pnl > 0]
        avg_rr = sum(t.risk_reward for t in winning_trades) / len(winning_trades) if winning_trades else 0
        
        final_balance = perf.account.balance
        pnl = final_balance - initial_balance
        pnl_pct = (pnl / initial_balance) * 100
        
        print(f"\n📈 Results:")
        print(f"   Signals: {len(signals)}")
        print(f"   Trades: {total_trades}")
        print(f"   Wins: {wins} | Losses: {losses}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Avg RR: {avg_rr:.2f}")
        print(f"   Max DD: {perf.stats.max_drawdown_pct:.2f}%")
        print(f"   Final Balance: ${final_balance:.2f}")
        print(f"   P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        
        return {
            'pair': pair,
            'signals': len(signals),
            'trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_rr': avg_rr,
            'max_dd': perf.stats.max_drawdown_pct,
            'final_balance': final_balance,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'h4_trend': metadata.get('h4_trend', 'N/A')
        }
        
    except Exception as e:
        print(f"❌ Error backtesting {pair}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'pair': pair,
            'error': str(e),
            'signals': 0,
            'trades': 0
        }

def main():
    print("="*70)
    print("MVP UNIFIED STRATEGY - MULTI-PAIR BACKTEST")
    print("="*70)
    
    # Initialize strategy
    strategy = UnifiedMVPStrategy()
    
    # Test pairs
    pairs = ['EURUSD', 'GBPJPY', 'USDCAD', 'XAUUSD']
    
    results = []
    for pair in pairs:
        result = backtest_pair(pair, strategy)
        results.append(result)
    
    # Summary table
    print(f"\n{'='*70}")
    print("SUMMARY - ALL PAIRS")
    print(f"{'='*70}\n")
    
    print(f"{'Pair':<10} {'Trend':<10} {'Signals':<8} {'Trades':<7} {'Win%':<7} {'RR':<6} {'DD%':<7} {'P&L%':<8}")
    print("-"*70)
    
    for r in results:
        if 'error' in r:
            print(f"{r['pair']:<10} ERROR: {r['error'][:40]}")
        else:
            print(f"{r['pair']:<10} {r['h4_trend']:<10} {r['signals']:<8} {r['trades']:<7} "
                  f"{r['win_rate']:<7.1f} {r['avg_rr']:<6.2f} {r['max_dd']:<7.2f} {r['pnl_pct']:<+8.2f}")
    
    # Overall stats
    total_trades = sum(r.get('trades', 0) for r in results)
    total_wins = sum(r.get('wins', 0) for r in results)
    
    print("-"*70)
    if total_trades > 0:
        overall_wr = (total_wins / total_trades) * 100
        print(f"{'OVERALL':<10} {'':<10} {'':<8} {total_trades:<7} {overall_wr:<7.1f}")
        
        # Check if meets targets
        print(f"\n🎯 Target Metrics:")
        print(f"   Win Rate Target: >60% | Actual: {overall_wr:.1f}% {'✅' if overall_wr >= 60 else '❌'}")
        
        # Find best pair
        best_pair = max([r for r in results if 'error' not in r], 
                       key=lambda x: x.get('win_rate', 0), 
                       default=None)
        if best_pair:
            print(f"\n🏆 Best Performer: {best_pair['pair']} ({best_pair['win_rate']:.1f}% WR, {best_pair['avg_rr']:.2f}R)")
    else:
        print("\n⚠️  No trades across all pairs - Strategy is very selective")
        print("   This suggests:")
        print("   • Market conditions don't meet criteria (ranging markets)")
        print("   • OB quality filters are too strict")
        print("   • Consider relaxing some filters or testing on different data period")
    
    print(f"\n{'='*70}")

if __name__ == "__main__":
    main()
