"""
Test strategy variations for rapid optimization
Run: python backend/test_strategy_variations.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals
from app.services.journal import JournalService

def test_baseline():
    """Test current strategy (baseline)"""
    print("\n" + "="*80)
    print("BASELINE STRATEGY (Current)")
    print("="*80)
    
    df_4h = load_candle_data("EURUSD", "H4", limit=1000)
    df_5m = load_candle_data("EURUSD", "M5", limit=5000)
    
    ranges = detect_4h_range(df_4h)
    signals = analyze_5m_signals(df_5m, ranges, use_dynamic_tp=False)  # Fixed 2R
    
    journal = JournalService()
    result = journal.process_signals(signals, "EURUSD")
    
    print_results(result, "BASELINE")
    return result

def print_results(result, version_name):
    """Print test results in table format"""
    stats = result.stats
    account = result.account
    
    print(f"\n{version_name} Results:")
    print(f"├─ Total Trades: {stats.total_trades}")
    print(f"├─ Win Rate: {stats.win_rate:.2f}%")
    print(f"├─ Avg RR: {stats.avg_rr:.2f}R")
    print(f"├─ Max DD: {stats.max_drawdown:.2f}%")
    print(f"├─ Total P&L: ${stats.total_pnl:.2f}")
    print(f"├─ Final Balance: ${account.balance:.2f}")
    print(f"└─ Best Trade: ${stats.best_trade:.2f} | Worst: ${stats.worst_trade:.2f}")

def run_all_tests():
    """Run all strategy variations"""
    print("\n" + "🚀 STRATEGY OPTIMIZATION TEST SUITE" + "\n")
    
    results = {}
    
    # Baseline (fixed 2R)
    results['baseline'] = test_baseline()
    
    # V2: Dynamic TP
    results['v2_dynamic_tp'] = test_dynamic_tp()
    
    # V3: Dynamic TP + Swing Filter (OB Proxy)
    results['v3_swing_filter'] = test_swing_filter()
    
    # V4: V3 + Min RR 2.0
    results['v4_min_rr_2'] = test_min_rr_filter()
    
    # V5: V3 + Trend Filter (EMA 200)
    results['v5_trend_filter'] = test_trend_filter()
    
    # V6: V5 + Min RR 2.0
    results['v6_trend_min_rr_2'] = test_trend_min_rr()
    
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Version':<20} {'WR':<10} {'Avg RR':<10} {'Max DD':<10} {'P&L':<12}")
    print("-"*80)
    
    for name, result in results.items():
        print(f"{name:<20} {result.stats.win_rate:>6.2f}%   {result.stats.avg_rr:>6.2f}R   "
              f"{result.stats.max_drawdown:>6.2f}%   ${result.stats.total_pnl:>9.2f}")


def test_dynamic_tp():
    """Test with dynamic TP based on FVG/Liquidity"""
    print("\n" + "="*80)
    print("V2: DYNAMIC TP (FVG + Liquidity)")
    print("="*80)
    
    df_4h = load_candle_data("EURUSD", "H4", limit=1000)
    df_5m = load_candle_data("EURUSD", "M5", limit=5000)
    
    ranges = detect_4h_range(df_4h)
    signals = analyze_5m_signals(df_5m, ranges, use_dynamic_tp=True, use_swing_filter=False, min_rr=0.0)
    
    journal = JournalService()
    result = journal.process_signals(signals, "EURUSD")
    
    print_results(result, "V2_DYNAMIC_TP")
    return result

def test_swing_filter():
    """Test with Dynamic TP + Swing Entry Filter"""
    print("\n" + "="*80)
    print("V3: DYNAMIC TP + SWING FILTER (OB Proxy)")
    print("="*80)
    
    df_4h = load_candle_data("EURUSD", "H4", limit=1000)
    df_5m = load_candle_data("EURUSD", "M5", limit=5000)
    
    ranges = detect_4h_range(df_4h)
    signals = analyze_5m_signals(df_5m, ranges, use_dynamic_tp=True, use_swing_filter=True, min_rr=0.0)
    
    journal = JournalService()
    result = journal.process_signals(signals, "EURUSD")
    
    print_results(result, "V3_SWING_FILTER")
    return result

def test_min_rr_filter():
    """Test with V3 + Min RR 2.0"""
    print("\n" + "="*80)
    print("V4: V3 + MIN RR 2.0")
    print("="*80)
    
    df_4h = load_candle_data("EURUSD", "H4", limit=1000)
    df_5m = load_candle_data("EURUSD", "M5", limit=5000)
    
    ranges = detect_4h_range(df_4h)
    signals = analyze_5m_signals(df_5m, ranges, use_dynamic_tp=True, use_swing_filter=True, min_rr=2.0)
    
    journal = JournalService()
    result = journal.process_signals(signals, "EURUSD")
    
    print_results(result, "V4_MIN_RR_2")
    return result

def test_trend_filter():
    """Test with V3 + Trend Filter (EMA 200)"""
    print("\n" + "="*80)
    print("V5: V3 + TREND FILTER (EMA 200)")
    print("="*80)
    
    df_4h = load_candle_data("EURUSD", "H4", limit=1000)
    df_5m = load_candle_data("EURUSD", "M5", limit=5000)
    
    ranges = detect_4h_range(df_4h)
    signals = analyze_5m_signals(df_5m, ranges, use_dynamic_tp=True, use_swing_filter=True, use_trend_filter=True, min_rr=1.5)
    
    journal = JournalService()
    result = journal.process_signals(signals, "EURUSD")
    
    print_results(result, "V5_TREND_FILTER")
    return result

def test_trend_min_rr():
    """Test with V5 + Min RR 2.0"""
    print("\n" + "="*80)
    print("V6: V5 + MIN RR 2.0")
    print("="*80)
    
    df_4h = load_candle_data("EURUSD", "H4", limit=1000)
    df_5m = load_candle_data("EURUSD", "M5", limit=5000)
    
    ranges = detect_4h_range(df_4h)
    signals = analyze_5m_signals(df_5m, ranges, use_dynamic_tp=True, use_swing_filter=True, use_trend_filter=True, min_rr=2.0)
    
    journal = JournalService()
    result = journal.process_signals(signals, "EURUSD")
    
    print_results(result, "V6_TREND_MIN_RR_2")
    return result

if __name__ == "__main__":
    run_all_tests()
