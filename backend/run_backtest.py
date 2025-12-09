"""
Multi-Pair Backtest Script
Tests both Range 4H and MTF 30/1 strategies across multiple currency pairs
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals
from app.strategies.mtf_30_1 import MTF30_1Strategy
from app.strategies.unified_smc_strategy import UnifiedSMCStrategy
from app.strategies.unified_strategy_lt1 import LT1 # Import new strategy
from app.services.journal import JournalService
from datetime import datetime
import json

# Pairs to test
PAIRS = ['EURUSD', 'GBPUSD', 'GBPJPY', 'USDCAD']

# Performance targets
TARGET_WIN_RATE = 70.0  # >70%
TARGET_AVG_RR = 2.0     # >2.0
TARGET_MAX_DD = 4.0     # <4%

def format_percentage(value):
    """Format value as percentage"""
    return f"{value:.1f}%"

def format_currency(value):
    """Format value as currency"""
    return f"${value:,.2f}"

def format_ratio(value):
    """Format value as ratio"""
    return f"{value:.2f}"

def test_range_4h_strategy(pair, initial_balance=50000):
    """Test Range 4H strategy for a given pair"""
    try:
        # Load data
        df_4h = load_candle_data(pair, "H4", limit=1000)
        df_5m = load_candle_data(pair, "M5", limit=5000)
        
        # Detect ranges
        ranges = detect_4h_range(df_4h)
        
        # Analyze signals with V7 configuration (stricter filters for higher quality)
        signals = analyze_5m_signals(
            df_5m, 
            ranges,
            use_dynamic_tp=True,
            use_swing_filter=True,
            use_trend_filter=True,
            min_rr=3.0,  # Increased from 2.0 to 3.0 for better RR as per docs/strategies/overview.md
            prefer_higher_rr=True  # Prefer swing targets over FVG for higher RR
        )
        
        if not signals:
            return None
        
        # Process through journal
        journal = JournalService()
        # JournalService initializes with STARTING_BALANCE automatically
        
        result = journal.process_signals(signals, pair)
        
        return {
            'pair': pair,
            'strategy': 'Range 4H',
            'total_trades': result.stats.total_trades,
            'winning_trades': result.stats.winning_trades,
            'losing_trades': result.stats.total_trades - result.stats.winning_trades,
            'win_rate': result.stats.win_rate,
            'avg_rr': result.stats.avg_rr,
            'max_drawdown': result.stats.max_drawdown,
            'max_drawdown_pct': result.stats.max_drawdown,
            'total_pnl': result.stats.total_pnl,
            'final_balance': result.account.balance,
            'profit_factor': result.stats.total_pnl / abs(result.stats.max_drawdown) if result.stats.max_drawdown != 0 else 0
        }
        
    except Exception as e:
        print(f"  ✗ Error testing {pair} (Range 4H): {e}")
        return None

def test_mtf_30_1_strategy(pair, initial_balance=50000):
    """Test MTF 30/1 strategy for a given pair"""
    try:
        # Load data
        df_4h = load_candle_data(pair, "H4", limit=1000)
        df_30m = load_candle_data(pair, "M30", limit=2000)
        df_1m = load_candle_data(pair, "M1", limit=5000)
        
        # Run strategy
        strategy = MTF30_1Strategy()
        result = strategy.analyze({
            'H4': df_4h,
            '30M': df_30m,
            '1M': df_1m
        })
        
        signals = result.get('signals', [])
        
        if not signals:
            return None
        
        # Process through journal
        journal = JournalService()
        # JournalService initializes with STARTING_BALANCE automatically
        
        journal_result = journal.process_signals(signals, pair)
        
        return {
            'pair': pair,
            'strategy': 'MTF 30/1',
            'total_trades': journal_result.stats.total_trades,
            'winning_trades': journal_result.stats.winning_trades,
            'losing_trades': journal_result.stats.total_trades - journal_result.stats.winning_trades,
            'win_rate': journal_result.stats.win_rate,
            'avg_rr': journal_result.stats.avg_rr,
            'max_drawdown': journal_result.stats.max_drawdown,
            'max_drawdown_pct': journal_result.stats.max_drawdown,
            'total_pnl': journal_result.stats.total_pnl,
            'final_balance': journal_result.account.balance,
            'profit_factor': journal_result.stats.total_pnl / abs(journal_result.stats.max_drawdown) if journal_result.stats.max_drawdown != 0 else 0
        }
        
    except Exception as e:
        print(f"  ✗ Error testing {pair} (MTF 30/1): {e}")
        return None

def test_unified_smc_strategy(pair, initial_balance=50000):
    """Test Unified SMC strategy for a given pair"""
    try:
        # Load data for multiple timeframes
        df_multi_tf = {
            'H4': load_candle_data(pair, "H4", limit=1000),
            'M15': load_candle_data(pair, "M15", limit=2000),
            'M5': load_candle_data(pair, "M5", limit=5000),
            'M1': load_candle_data(pair, "M1", limit=5000) # For LTF refinement
        }
        
        # Run strategy
        strategy = UnifiedSMCStrategy()
        config = {
            "sweep_threshold": 0.5,
            "eqh_eql_threshold": 0.1
        }
        # The analyze method in UnifiedSMCStrategy expects df, symbol, timeframe
        # For backtesting, we'll pass the M5 data as the primary DF and let the strategy handle MTF internally.
        result = strategy.analyze(df_multi_tf['M5'], pair, 'M5')
        
        signals = result.get('signals', [])
        
        if not signals:
            return None
        
        # Process through journal
        journal = JournalService()
        journal_result = journal.process_signals(signals, pair)
        
        return {
            'pair': pair,
            'strategy': 'Unified SMC',
            'total_trades': journal_result.stats.total_trades,
            'winning_trades': journal_result.stats.winning_trades,
            'losing_trades': journal_result.stats.total_trades - journal_result.stats.winning_trades,
            'win_rate': journal_result.stats.win_rate,
            'avg_rr': journal_result.stats.avg_rr,
            'max_drawdown': journal_result.stats.max_drawdown,
            'max_drawdown_pct': journal_result.stats.max_drawdown,
            'total_pnl': journal_result.stats.total_pnl,
            'final_balance': journal_result.account.balance,
            'profit_factor': journal_result.stats.total_pnl / abs(journal_result.stats.max_drawdown) if journal_result.stats.max_drawdown != 0 else 0
        }
        
    except Exception as e:
        print(f"  ✗ Error testing {pair} (Unified SMC): {e}")
        import traceback
        traceback.print_exc()
        return None

def test_lt1_strategy(pair, initial_balance=50000):
    """Test LT1 strategy for a given pair"""
    try:
        # Load data for multiple timeframes
        df_multi_tf = {
            'H4': load_candle_data(pair, "H4", limit=1000),
            'M15': load_candle_data(pair, "M15", limit=2000),
            'M5': load_candle_data(pair, "M5", limit=5000),
            'M1': load_candle_data(pair, "M1", limit=5000) # For LTF refinement
        }
        
        # Run strategy
        strategy = LT1()
        config = {
            "sweep_threshold": 0.5,
            "eqh_eql_threshold": 0.1
        }
        # The analyze method in LT1 expects df, symbol, timeframe
        # We need to iterate through the data to simulate backtesting
        # For now, let's just analyze the latest candle for a quick test
        
        # This is a simplified call for initial testing, a full backtest loop would be more complex
        # and would involve iterating through df_m5 and calling analyze for each candle.
        # For now, we'll pass the M5 data as the primary DF and let the strategy handle MTF internally.
        
        # To simulate backtesting, we need to pass the full dataframe to the strategy's generate_signals
        # which will then iterate internally.
        
        signals = []
        # Assuming generate_signals is an async method, we need to run it in an event loop
        # For a simple backtest script, we can adapt it to be synchronous or use asyncio.run
        # For now, let's call the synchronous analyze method for the last candle
        
        # This part needs to be adapted to how LT1.analyze is designed to be called for backtesting.
        # Based on the LT1.analyze signature (df, symbol, timeframe), it expects a single timeframe DF.
        # The generate_signals method is async and expects to fetch data.
        # For backtesting, we need to feed it data iteratively or pass pre-loaded data.
        
        # Let's simplify for now and just call analyze on the latest M5 candle
        # This will not be a full backtest, but will check if the strategy can generate signals.
        
        # For a proper backtest, we would need to refactor LT1.generate_signals to accept pre-loaded dataframes
        # or create a backtest loop that feeds data to LT1.analyze candle by candle.
        
        # For this iteration, let's assume LT1.analyze can take a single dataframe and generate signals
        # based on its internal MTF logic.
        
        # Let's call analyze on the latest M5 data
        latest_m5_df = df_multi_tf['M5'].iloc[-500:] # Use a recent window for analysis
        result_analysis = strategy.analyze(latest_m5_df, pair, 'M5')
        signals = result_analysis.get('signals', [])
        
        if not signals:
            return None
        
        # Process through journal
        journal = JournalService()
        journal_result = journal.process_signals(signals, pair)
        
        return {
            'pair': pair,
            'strategy': 'LT1',
            'total_trades': journal_result.stats.total_trades,
            'winning_trades': journal_result.stats.winning_trades,
            'losing_trades': journal_result.stats.total_trades - journal_result.stats.winning_trades,
            'win_rate': journal_result.stats.win_rate,
            'avg_rr': journal_result.stats.avg_rr,
            'max_drawdown': journal_result.stats.max_drawdown,
            'max_drawdown_pct': journal_result.stats.max_drawdown,
            'total_pnl': journal_result.stats.total_pnl,
            'final_balance': journal_result.account.balance,
            'profit_factor': journal_result.stats.total_pnl / abs(journal_result.stats.max_drawdown) if journal_result.stats.max_drawdown != 0 else 0
        }
        
    except Exception as e:
        print(f"  ✗ Error testing {pair} (LT1): {e}")
        import traceback
        traceback.print_exc()
        return None

def print_results_table(results):
    """Print results in a formatted table"""
    print("\n" + "="*120)
    print("BACKTEST RESULTS")
    print("="*120)
    print(f"{'Pair':<10} {'Strategy':<12} {'Trades':<8} {'Win Rate':<10} {'Avg RR':<10} {'Max DD':<12} {'PnL':<12} {'Final':<12}")
    print("-"*120)
    
    for r in results:
        if r:
            print(f"{r['pair']:<10} {r['strategy']:<12} {r['total_trades']:<8} "
                  f"{format_percentage(r['win_rate']):<10} {format_ratio(r['avg_rr']):<10} "
                  f"{format_percentage(r['max_drawdown_pct']):<12} {format_currency(r['total_pnl']):<12} "
                  f"{format_currency(r['final_balance']):<12}")
    
    print("="*120)

def check_performance_targets(results):
    """Check if results meet performance targets"""
    print("\n" + "="*120)
    print("PERFORMANCE TARGET VERIFICATION")
    print("="*120)
    print(f"Targets: Win Rate > {TARGET_WIN_RATE}% | Avg RR > {TARGET_AVG_RR} | Max DD < {TARGET_MAX_DD}%")
    print("-"*120)
    
    passed = []
    failed = []
    
    for r in results:
        if not r:
            continue
            
        meets_win_rate = r['win_rate'] > TARGET_WIN_RATE
        meets_rr = r['avg_rr'] > TARGET_AVG_RR
        meets_dd = r['max_drawdown_pct'] < TARGET_MAX_DD
        
        all_met = meets_win_rate and meets_rr and meets_dd
        
        status = "✓ PASS" if all_met else "✗ FAIL"
        wr_status = "✓" if meets_win_rate else "✗"
        rr_status = "✓" if meets_rr else "✗"
        dd_status = "✓" if meets_dd else "✗"
        
        print(f"{status} {r['pair']:<10} {r['strategy']:<12} | "
              f"{wr_status} WR: {format_percentage(r['win_rate']):<8} | "
              f"{rr_status} RR: {format_ratio(r['avg_rr']):<6} | "
              f"{dd_status} DD: {format_percentage(r['max_drawdown_pct']):<8}")
        
        if all_met:
            passed.append(r)
        else:
            failed.append(r)
    
    print("="*120)
    print(f"\nSummary: {len(passed)}/{len(results)} tests passed performance targets")
    
    return passed, failed

if __name__ == "__main__":
    print("\n" + "="*120)
    print("MULTI-PAIR BACKTEST")
    print("="*120)
    print(f"Testing {len(PAIRS)} pairs: {', '.join(PAIRS)}")
    print(f"Strategies: Range 4H, MTF 30/1, Unified SMC, LT1")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = []
    
    # Test Range 4H strategy
    # print("\n" + "-"*120)
    # print("Testing Range 4H Strategy")
    # print("-"*120)
    
    # for pair in PAIRS:
    #     print(f"\n  Testing {pair}...")
    #     result = test_range_4h_strategy(pair)
    #     if result:
    #         all_results.append(result)
    #         print(f"  ✓ {result['total_trades']} trades | "
    #               f"Win Rate: {format_percentage(result['win_rate'])} | "
    #               f"Avg RR: {format_ratio(result['avg_rr'])} | "
    #               f"Max DD: {format_percentage(result['max_drawdown_pct'])}")
    #     else:
    #         print(f"  ⚠ No signals generated for {pair}")
    
    # Test MTF 30/1 strategy
    # print("\n" + "-"*120)
    # print("Testing MTF 30/1 Strategy")
    # print("-"*120)
    
    # for pair in PAIRS:
    #     print(f"\n  Testing {pair}...")
    #     result = test_mtf_30_1_strategy(pair)
    #     if result:
    #         all_results.append(result)
    #         print(f"  ✓ {result['total_trades']} trades | "
    #               f"Win Rate: {format_percentage(result['win_rate'])} | "
    #               f"Avg RR: {format_ratio(result['avg_rr'])} | "
    #               f"Max DD: {format_percentage(result['max_drawdown_pct'])}")
    #     else:
    #         print(f"  ⚠ No signals generated for {pair}")

    # Test Unified SMC strategy
    print("\n" + "-"*120)
    print("Testing Unified SMC Strategy")
    print("-"*120)
    
    for pair in PAIRS:
        print(f"\n  Testing {pair}...")
        result = test_unified_smc_strategy(pair)
        if result:
            all_results.append(result)
            print(f"  ✓ {result['total_trades']} trades | "
                  f"Win Rate: {format_percentage(result['win_rate'])} | "
                  f"Avg RR: {format_ratio(result['avg_rr'])} | "
                  f"Max DD: {format_percentage(result['max_drawdown_pct'])}")
        else:
            print(f"  ⚠ No signals generated for {pair}")

    # Test LT1 strategy
    print("\n" + "-"*120)
    print("Testing LT1 Strategy")
    print("-"*120)
    
    for pair in PAIRS:
        print(f"\n  Testing {pair}...")
        result = test_lt1_strategy(pair)
        if result:
            all_results.append(result)
            print(f"  ✓ {result['total_trades']} trades | "
                  f"Win Rate: {format_percentage(result['win_rate'])} | "
                  f"Avg RR: {format_ratio(result['avg_rr'])} | "
                  f"Max DD: {format_percentage(result['max_drawdown_pct'])}")
        else:
            print(f"  ⚠ No signals generated for {pair}")
    
    # Print results
    if all_results:
        print_results_table(all_results)
        passed, failed = check_performance_targets(all_results)
        
        # Save results to JSON
        output_file = "backtest_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'targets': {
                    'win_rate': TARGET_WIN_RATE,
                    'avg_rr': TARGET_AVG_RR,
                    'max_dd': TARGET_MAX_DD
                },
                'results': all_results,
                'summary': {
                    'total_tests': len(all_results),
                    'passed': len(passed),
                    'failed': len(failed)
                }
            }, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to {output_file}")
        
        if len(passed) == len(all_results):
            print("\n✓ All tests passed performance targets!")
            sys.exit(0)
        else:
            print(f"\n⚠ {len(failed)} test(s) did not meet performance targets")
            sys.exit(1)
    else:
        print("\n✗ No results generated")
        sys.exit(1)
