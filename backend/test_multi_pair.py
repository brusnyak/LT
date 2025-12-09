"""
Test range_4h strategy on multiple pairs to validate robustness
"""
from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals
from app.services.journal import JournalService

def test_pair(pair: str, timeframe: str = "M15"):
    """Test range_4h strategy on a specific pair"""
    print(f"\n{'='*80}")
    print(f"Testing {pair} - 4H Range Strategy (using {timeframe} data)")
    print(f"{'='*80}")
    
    try:
        df_4h = load_candle_data(pair, "H4", limit=500)
        df_exec = load_candle_data(pair, timeframe, limit=3000)
        
        print(f"Loaded: {len(df_4h)} H4 candles, {len(df_exec)} {timeframe} candles")
        
        ranges = detect_4h_range(df_4h)
        signals = analyze_5m_signals(
            df_exec, 
            ranges, 
            use_dynamic_tp=True, 
            use_swing_filter=True, 
            use_trend_filter=False, 
            min_rr=1.5
        )
        
        print(f"Found: {len(ranges)} ranges, {len(signals)} signals")
        
        if len(signals) == 0:
            print(f"⚠️  No signals generated for {pair}")
            return None
        
        journal = JournalService()
        result = journal.process_signals(signals, pair)
        
        print(f"\n{pair} Results:")
        print(f"├─ Total Trades: {result.stats.total_trades}")
        print(f"├─ Win Rate: {result.stats.win_rate:.2f}%")
        print(f"├─ Avg RR: {result.stats.avg_rr:.2f}R")
        print(f"├─ Max DD: {result.stats.max_drawdown:.2f}%")
        print(f"├─ Total P&L: ${result.stats.total_pnl:.2f}")
        print(f"├─ Final Balance: ${result.account.balance:.2f}")
        print(f"└─ Best Trade: ${result.stats.best_trade:.2f} | Worst: ${result.stats.worst_trade:.2f}")
        
        return {
            'pair': pair,
            'trades': result.stats.total_trades,
            'wr': result.stats.win_rate,
            'avg_rr': result.stats.avg_rr,
            'max_dd': result.stats.max_drawdown,
            'pnl': result.stats.total_pnl,
            'final_balance': result.account.balance
        }
    except Exception as e:
        print(f"❌ Error testing {pair}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Test 4H Range strategy on all available pairs"""
    print("\n" + "="*80)
    print("PHASE 4: MULTI-PAIR BACKTEST - 4H Range Strategy")
    print("="*80)
    print("Testing strategy robustness across multiple currency pairs")
    print("Using M15 data for execution (M5 data is sparse)")
    
    # Test these pairs
    pairs = ["EURUSD", "GBPUSD", "USDCAD", "GBPJPY"]
    results = []
    
    for pair in pairs:
        result = test_pair(pair, timeframe="M15")
        if result:
            results.append(result)
    
    # Summary table
    print("\n" + "="*80)
    print("MULTI-PAIR COMPARISON")
    print("="*80)
    print(f"{'Pair':<10} {'Trades':<10} {'WR %':<10} {'Avg RR':<10} {'Max DD %':<12} {'P&L $':<12}")
    print("-"*80)
    
    for r in results:
        print(f"{r['pair']:<10} {r['trades']:<10} {r['wr']:>6.2f}    {r['avg_rr']:>6.2f}    "
              f"{r['max_dd']:>8.2f}      ${r['pnl']:>9.2f}")
    
    # Overall statistics
    if results:
        avg_wr = sum(r['wr'] for r in results) / len(results)
        avg_rr = sum(r['avg_rr'] for r in results) / len(results)
        avg_dd = sum(r['max_dd'] for r in results) / len(results)
        total_pnl = sum(r['pnl'] for r in results)
        total_trades = sum(r['trades'] for r in results)
        
        print("-"*80)
        print(f"{'AVERAGE':<10} {total_trades:<10} {avg_wr:>6.2f}    {avg_rr:>6.2f}    "
              f"{avg_dd:>8.2f}      ${total_pnl:>9.2f}")
        
        # Analysis
        print("\n" + "="*80)
        print("PERFORMANCE ANALYSIS")
        print("="*80)
        print(f"Average Win Rate:    {avg_wr:.2f}% (Target: 80%+)")
        print(f"Average RR Ratio:    {avg_rr:.2f}R (Target: 2R+)")
        print(f"Average Max DD:      {avg_dd:.2f}% (Target: <3%)")
        print(f"Total P&L (4 pairs): ${total_pnl:.2f}")
        print(f"Total Trades:        {total_trades}")
        
        # Identify best performing pair
        if results:
            best_wr = max(results, key=lambda x: x['wr'])
            best_pnl = max(results, key=lambda x: x['pnl'])
            lowest_dd = min(results, key=lambda x: x['max_dd'])
            
            print(f"\n📊 Best Performance:")
            print(f"   Highest WR:      {best_wr['pair']} ({best_wr['wr']:.2f}%)")
            print(f"   Highest P&L:     {best_pnl['pair']} (${best_pnl['pnl']:.2f})")
            print(f"   Lowest Drawdown: {lowest_dd['pair']} ({lowest_dd['max_dd']:.2f}%)")
        
        # Verdict
        print(f"\n{'='*80}")
        if avg_wr >= 65 and avg_rr >= 1.5 and avg_dd < 5:
            print("✅ STRATEGY VALIDATED: Good performance across multiple pairs!")
            print("   Strategy shows robustness and consistency")
        elif avg_wr >= 55 and avg_rr >= 1.2:
            print("⚠️  STRATEGY ACCEPTABLE: Moderate performance")
            print("   Consider optimizations for better results")
        else:
            print("❌ STRATEGY NEEDS WORK: Performance below targets")
            print("   Significant refinement required")
        
        print(f"{'='*80}\n")
    else:
        print("\n❌ No valid results - check data availability")

if __name__ == "__main__":
    main()
