"""
Test optimized strategy with "Quick Wins"
"""
from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals
from app.services.journal import JournalService

def test_optimized(pair: str = "GBPUSD"):
    """Test optimized strategy on GBPUSD"""
    print("="*80)
    print(f"OPTIMIZED STRATEGY TEST - {pair}")
    print("="*80)
    print("\nQuick Win Optimizations:")
    print("  ✅ Trend filter enabled")
    print("  ✅ Swing threshold: 10 pips (was 5)")
    print("  ✅ TP search window: 200 candles (was 100)")
    print("  ✅ Min RR: 1.0R (was 1.5R)")
    print()
    
    # Load data
    df_4h = load_candle_data(pair, "H4", limit=500)
    df_m15 = load_candle_data(pair, "M15", limit=3000)
    
    print(f"Loaded: {len(df_4h)} H4 candles, {len(df_m15)} M15 candles")
    
    # Detect ranges
    ranges = detect_4h_range(df_4h)
    
    # Test different configurations
    configs = [
        {
            'name': 'BASELINE (from Phase 4)',
            'params': {
                'use_dynamic_tp': True,
                'use_swing_filter': True,
                'use_trend_filter': False,
                'min_rr': 1.5
            }
        },
        {
            'name': 'OPTIMIZED (Quick Wins)',
            'params': {
                'use_dynamic_tp': True,
                'use_swing_filter': True,
                'use_trend_filter': True,  # ✅ Enabled
                'min_rr': 1.0  # ✅ Lowered
            }
        }
    ]
    
    results = []
    
    for config in configs:
        print(f"\n{'='*80}")
        print(f"{config['name']}")
        print(f"{'='*80}")
        
        signals = analyze_5m_signals(df_m15, ranges, **config['params'])
        
        if len(signals) == 0:
            print("⚠️  No signals generated")
            continue
        
        journal = JournalService()
        result = journal.process_signals(signals, pair)
        
        print(f"\nResults:")
        print(f"├─ Total Trades: {result.stats.total_trades}")
        print(f"├─ Win Rate: {result.stats.win_rate:.2f}%")
        print(f"├─ Avg RR: {result.stats.avg_rr:.2f}R")
        print(f"├─ Max DD: {result.stats.max_drawdown:.2f}%")
        print(f"├─ Total P&L: ${result.stats.total_pnl:.2f}")
        print(f"├─ Final Balance: ${result.account.balance:.2f}")
        print(f"└─ Best: ${result.stats.best_trade:.2f} | Worst: ${result.stats.worst_trade:.2f}")
        
        results.append({
            'config': config['name'],
            'trades': result.stats.total_trades,
            'wr': result.stats.win_rate,
            'avg_rr': result.stats.avg_rr,
            'max_dd': result.stats.max_drawdown,
            'pnl': result.stats.total_pnl
        })
    
    # Comparison
    if len(results) == 2:
        print(f"\n{'='*80}")
        print("IMPROVEMENT ANALYSIS")
        print(f"{'='*80}")
        
        baseline = results[0]
        optimized = results[1]
        
        wr_delta = optimized['wr'] - baseline['wr']
        rr_delta = optimized['avg_rr'] - baseline['avg_rr']
        pnl_delta = optimized['pnl'] - baseline['pnl']
        
        print(f"\nWin Rate:    {baseline['wr']:.2f}% → {optimized['wr']:.2f}% ({wr_delta:+.2f}%)")
        print(f"Avg RR:      {baseline['avg_rr']:.2f}R → {optimized['avg_rr']:.2f}R ({rr_delta:+.2f}R)")
        print(f"Total P&L:   ${baseline['pnl']:.2f} → ${optimized['pnl']:.2f} (${pnl_delta:+.2f})")
        print(f"Max DD:      {baseline['max_dd']:.2f}% → {optimized['max_dd']:.2f}%")
        
        if wr_delta >= 5 and pnl_delta > 0:
            print(f"\n✅ SIGNIFICANT IMPROVEMENT! Optimizations are working.")
        elif wr_delta >= 0 and pnl_delta > 0:
            print(f"\n✅ Modest improvement. Optimizations help.")
        else:
            print(f"\n⚠️  Mixed results. May need different approach.")

if __name__ == "__main__":
    test_optimized("GBPUSD")
