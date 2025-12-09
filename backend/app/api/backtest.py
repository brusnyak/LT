from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.core.data_loader import load_candle_data
from app.strategies.range_4h import detect_4h_range, analyze_5m_signals
from app.services.journal import JournalService

router = APIRouter()

@router.get("/run")
async def run_backtest_endpoint():
    """
    Run the backtest suite and return results for the comparison table.
    """
    try:
        results = []
        
        # Load Data once
        # Using smaller limit for quick API response
        df_4h = load_candle_data("EURUSD", "H4", limit=500)
        df_5m = load_candle_data("EURUSD", "M5", limit=3000)
        
        if df_4h.empty or df_5m.empty:
            return []
            
        ranges = detect_4h_range(df_4h)
        journal = JournalService()
        
        # Define variations to test
        variations = [
            {
                "id": "v1_baseline",
                "name": "V1: Baseline (Fixed 2R)",
                "params": {"use_dynamic_tp": False, "use_swing_filter": False, "use_trend_filter": False, "min_rr": 0.0}
            },
            {
                "id": "v3_swing",
                "name": "V3: Swing Filter",
                "params": {"use_dynamic_tp": True, "use_swing_filter": True, "use_trend_filter": False, "min_rr": 0.0}
            },
            {
                "id": "v5_trend",
                "name": "V5: Trend Filter (Best)",
                "params": {"use_dynamic_tp": True, "use_swing_filter": True, "use_trend_filter": True, "min_rr": 1.5}
            },
            {
                "id": "v_mvp",
                "name": "MVP Unified (H4+M15+M5)",
                "params": {"strategy_class": "UnifiedMVP"}
            },
            {
                "id": "v_unified",
                "name": "Unified Strategy (SMC + Tech)",
                "params": {"strategy_class": "UnifiedSMCStrategy"}
            }
        ]
        
        # Import strategies
        from app.strategies.unified_smc_strategy import UnifiedSMCStrategy
        from app.strategies.unified_mvp import UnifiedMVPStrategy
        
        unified_strategy = UnifiedSMCStrategy()
        mvp_strategy = UnifiedMVPStrategy()

        for v in variations:
            strategy_class = v.get('params', {}).get('strategy_class')
            
            if strategy_class == "UnifiedMVP":
                # Run MVP Unified Strategy (H4+M15+M5)
                df_m15 = load_candle_data("EURUSD", "M15", limit=1500)
                df_multi_tf = {'H4': df_4h, 'M15': df_m15, 'M5': df_5m}
                analysis_result = mvp_strategy.analyze(df_multi_tf)
                signals = analysis_result.get('signals', [])
                if not signals:
                    print(f"MVP Strategy returned no signals. Metadata: {analysis_result.get('metadata', {})}")
            elif strategy_class == "UnifiedSMCStrategy":
                # Run Unified Strategy
                df_multi_tf = {'H4': df_4h, 'M5': df_5m}
                analysis_result = unified_strategy.analyze(df_multi_tf)
                signals = analysis_result.get('signals', [])
                if not signals:
                    print(f"Unified Strategy returned no signals. Result: {analysis_result.keys()}")
                    if 'error' in analysis_result:
                        print(f"Error: {analysis_result['error']}")
            else:
                # Run Legacy Range Strategy
                signals = analyze_5m_signals(df_5m, ranges, **v['params'])
            
            # Reset journal for each run (in memory)
            journal.trades = []
            journal.balance = 50000
            journal.starting_balance = 50000
            
            if not signals:
                continue
                
            res = journal.process_signals(signals, "EURUSD")
            
            results.append({
                "id": v['id'],
                "name": v['name'],
                "win_rate": res.stats.win_rate,
                "avg_rr": res.stats.avg_rr,
                "max_dd": res.stats.max_drawdown,
                "total_pnl": res.stats.total_pnl,
                "total_trades": res.stats.total_trades,
                "final_balance": res.account.balance
            })
            
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
