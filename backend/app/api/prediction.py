"""Prediction API endpoints for V3 Live Prediction Mode"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.db.prediction_history import PredictionHistory
from app.models.db.challenge import Challenge
from app.core.data_loader import load_candle_data
from app.prediction.engine import PredictionEngine
from pydantic import BaseModel

router = APIRouter()


# Pydantic models
class PredictionRequest(BaseModel):
    """Request model for starting prediction"""
    challenge_id: int
    pair: str
    timeframe: str
    split_index: int
    num_candles: int = 20
    strategies: Optional[List[str]] = None  # Strategy names to use


class PredictionResponse(BaseModel):
    """Response model for prediction data"""
    id: int
    split_index: int  
    split_time: str
    direction: str
    confidence: float
    target_high: float
    target_low: float
    reversal_point: float
    reversal_confidence: float
    predicted_candles: List[dict]
    pattern_analysis: dict
    strategies_used: List[str]
    ensemble_weights: dict


class PredictionStepRequest(BaseModel):
    """Request for stepping prediction"""
    direction: str = "forward"  # or "backward"


class AccuracyRequest(BaseModel):
    """Request to calculate prediction accuracy"""
    prediction_id: int


@router.post("/start", response_model=PredictionResponse)
async def start_prediction(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new market prediction
    
    Analyzes historical data up to split_index, generates prediction
    for next N candles using ensemble of strategies
    """
    # Verify challenge exists
    challenge = db.query(Challenge).filter(Challenge.id == request.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Load market data
    try:
        # Load all available data to allow deep backtesting/simulation
        df = load_candle_data(request.pair, request.timeframe, limit=0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")
    
    if len(df) < request.split_index + request.num_candles:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough data. Need at least {request.split_index + request.num_candles} candles"
        )
    
    # Load strategies (for now, use empty list - will integrate later)
    # TODO: Load actual strategy instances based on request.strategies
    strategies = []
    
    # Create prediction engine
    engine = PredictionEngine(strategies=strategies)
    
    # Generate prediction
    try:
        prediction = engine.predict_market(
            df=df,
            split_index=request.split_index,
            num_candles=request.num_candles,
            timeframe=request.timeframe
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    
    # Save to database
    db_prediction = PredictionHistory(
        challenge_id=request.challenge_id,
        pair=request.pair,
        timeframe=request.timeframe,
        prediction_time=datetime.utcnow(),
        predicted_candles=prediction['predicted_candles'],
        strategies_used=prediction['strategies_used'],
        ensemble_weights=prediction['ensemble_weights'],
        direction=prediction['direction'],
        target_high=prediction['target_high'],
        target_low=prediction['target_low'],
        reversal_point=prediction['reversal_point'],
        confidence=prediction['confidence']
    )
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    return PredictionResponse(
        id=db_prediction.id,
        split_index=prediction['split_index'],
        split_time=prediction['split_time'],
        direction=prediction['direction'],
        confidence=prediction['confidence'],
        target_high=prediction['target_high'],
        target_low=prediction['target_low'],
        reversal_point=prediction['reversal_point'],
        reversal_confidence=prediction['reversal_confidence'],
        predicted_candles=prediction['predicted_candles'],
        pattern_analysis=prediction['pattern_analysis'],
        strategies_used=prediction['strategies_used'],
        ensemble_weights=prediction['ensemble_weights']
    )


@router.post("/step")
async def step_prediction(
    pair: str,
    timeframe: str,
    challenge_id: int,
    current_split: int,
    step_request: PredictionStepRequest,
    db: Session = Depends(get_db)
):
    """Step forward or backward in prediction"""
    # Load data
    df = load_candle_data(pair, timeframe, limit=0)
    
    engine = PredictionEngine(strategies=[])
    new_split = engine.step_prediction(df, current_split, step_request.direction)
    
    # Generate new prediction at new split point
    prediction = engine.predict_market(df, new_split, num_candles=20, timeframe=timeframe)
    
    # Save to database
    db_prediction = PredictionHistory(
        challenge_id=challenge_id,
        pair=pair,
        timeframe=timeframe,
        prediction_time=datetime.utcnow(),
        predicted_candles=prediction['predicted_candles'],
        strategies_used=prediction['strategies_used'],
        ensemble_weights=prediction['ensemble_weights'],
        direction=prediction['direction'],
        target_high=prediction['target_high'],
        target_low=prediction['target_low'],
        reversal_point=prediction['reversal_point'],
        confidence=prediction['confidence']
    )
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    return {
        "new_split_index": new_split,
        "prediction": PredictionResponse(
            id=db_prediction.id,
            split_index=prediction['split_index'],
            split_time=prediction['split_time'],
            direction=prediction['direction'],
            confidence=prediction['confidence'],
            target_high=prediction['target_high'],
            target_low=prediction['target_low'],
            reversal_point=prediction['reversal_point'],
            reversal_confidence=prediction['reversal_confidence'],
            predicted_candles=prediction['predicted_candles'],
            pattern_analysis=prediction['pattern_analysis'],
            strategies_used=prediction['strategies_used'],
            ensemble_weights=prediction['ensemble_weights']
        )
    }


@router.get("/history")
async def get_prediction_history(
    challenge_id: Optional[int] = Query(None),
    pair: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Get prediction history with optional filters"""
    query = db.query(PredictionHistory)
    
    if challenge_id:
        query = query.filter(PredictionHistory.challenge_id == challenge_id)
    
    if pair:
        query = query.filter(PredictionHistory.pair == pair)
    
    predictions = query.order_by(PredictionHistory.prediction_time.desc()).limit(limit).all()
    
    return {"predictions": predictions}


@router.get("/{prediction_id}")
async def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get a specific prediction by ID"""
    prediction = db.query(PredictionHistory).filter(PredictionHistory.id == prediction_id).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    return prediction


@router.post("/{prediction_id}/verify")
async def verify_prediction(
    prediction_id: int,
    db: Session = Depends(get_db)
):
    """
    Verify a prediction by comparing with actual market data
    Calculates accuracy score
    """
    prediction = db.query(PredictionHistory).filter(PredictionHistory.id == prediction_id).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Load actual market data
    df = load_candle_data(prediction.pair, prediction.timeframe, limit=0)
    
    # Create engine and calculate accuracy
    engine = PredictionEngine(strategies=[])
    
    prediction_dict = {
        'split_time': prediction.prediction_time.isoformat(),
        'predicted_candles': prediction.predicted_candles,
        'direction': prediction.direction,
        'target_high': prediction.target_high,
        'target_low': prediction.target_low,
    }
    
    try:
        accuracy = engine.calculate_accuracy(prediction_dict, df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Accuracy calculation failed: {str(e)}")
    
    # Update database
    prediction.accuracy_score = accuracy
    prediction.outcome_verified = datetime.utcnow()
    
    # Store actual candles for comparison
    split_time = prediction.prediction_time
    actual_future = df[df['time'] > split_time].head(len(prediction.predicted_candles))
    prediction.actual_candles = actual_future.to_dict('records')
    
    db.commit()
    
    return {
        "prediction_id": prediction_id,
        "accuracy_score": accuracy,
        "verified_at": prediction.outcome_verified
    }


@router.get("/stats/{challenge_id}")
async def get_prediction_stats(challenge_id: int, db: Session = Depends(get_db)):
    """Get prediction statistics for a challenge"""
    predictions = db.query(PredictionHistory).filter(
        PredictionHistory.challenge_id == challenge_id
    ).all()
    
    if not predictions:
        return {
            "total_predictions": 0,
            "avg_accuracy": 0,
            "avg_confidence": 0,
            "direction_breakdown": {}
        }
    
    verified = [p for p in predictions if p.accuracy_score is not None]
    
    avg_accuracy = sum(p.accuracy_score for p in verified) / len(verified) if verified else 0
    avg_confidence = sum(p.confidence for p in predictions) / len(predictions)
    
    direction_breakdown = {
        'BULLISH': len([p for p in predictions if p.direction == 'BULLISH']),
        'BEARISH': len([p for p in predictions if p.direction == 'BEARISH']),
        'RANGING': len([p for p in predictions if p.direction == 'RANGING']),
    }
    
    return {
        "total_predictions": len(predictions),
        "verified_predictions": len(verified),
        "avg_accuracy": avg_accuracy,
        "avg_confidence": avg_confidence,
        "direction_breakdown": direction_breakdown
    }


@router.get("/stats")
async def get_stats():
    """
    Get current session statistics
    """
    return {
        "balance": prediction_engine.balance,
        "positions": len(prediction_engine.positions),
        "predictions_made": len(prediction_engine.predictions)
    }
