"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import data, analysis

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Professional SMC backtesting platform with institutional-grade order block detection",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data.router, prefix=settings.API_PREFIX)
app.include_router(analysis.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/api/backtest/run")
async def run_backtest_endpoint():
    """
    Run the backtest suite and return results for the comparison table.
    In a real app, this would be async and maybe use a task queue.
    For now, we'll run a simplified version of the test script logic.
    """
    try:
        # We'll import the test logic here to avoid circular imports or setup issues
        # Ideally, this logic should be in a service, but for V2 prototype this is fine.
        from app.core.data import load_candle_data
        from app.strategies.range_4h import detect_4h_range, analyze_5m_signals
        from app.journal.service import JournalService
        
        results = []
        
        # Load Data once
        df_4h = load_candle_data("EURUSD", "H4", limit=1000)
        df_5m = load_candle_data("EURUSD", "M5", limit=5000)
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
            }
        ]
        
        for v in variations:
            signals = analyze_5m_signals(df_5m, ranges, **v['params'])
            # Reset journal for each run (in memory)
            journal.trades = []
            journal.account = {"balance": 50000, "equity": 50000, "risk_per_trade": 0.005}
            
            res = journal.process_signals(signals, "EURUSD")
            
            results.append({
                "id": v['id'],
                "name": v['name'],
                "win_rate": res.stats.win_rate,
                "avg_rr": res.stats.avg_rr,
                "max_dd": res.stats.max_drawdown,
                "total_pnl": res.stats.total_pnl,
                "total_trades": res.stats.total_trades,
                "final_balance": res.stats.final_balance
            })
            
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True)
