"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import data, analysis, backtest, prediction, challenges, journal, trainer, stats, trades, challenge_progression
from app.database import init_db

# Initialize database
init_db()

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

# Mount uploads directory
from fastapi.staticfiles import StaticFiles
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(prediction.router, prefix="/api/prediction", tags=["prediction"])
app.include_router(challenges.router, prefix="/api", tags=["challenges"])
app.include_router(journal.router, prefix="/api", tags=["journal"])
app.include_router(trainer.router, prefix="/api/trainer", tags=["trainer"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(challenge_progression.router, prefix="/api/progression", tags=["progression"])



@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True)
