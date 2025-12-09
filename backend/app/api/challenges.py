"""Challenge API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.db.challenge import Challenge
from app.templates.challenges import get_template, list_templates
from pydantic import BaseModel

router = APIRouter()


# Pydantic models for requests/responses
class ChallengeCreate(BaseModel):
    """Request model for creating a challenge"""
    name: str
    type: str
    phase: str = "Phase1"
    starting_balance: float
    profit_target: float
    daily_loss_limit: float
    max_drawdown: float
    risk_per_trade: float = 0.5
    max_positions: int = 2


class ChallengeUpdate(BaseModel):
    """Request model for updating a challenge"""
    name: Optional[str] = None
    phase: Optional[str] = None
    current_balance: Optional[float] = None
    starting_balance: Optional[float] = None
    profit_target: Optional[float] = None
    daily_loss_limit: Optional[float] = None
    max_drawdown: Optional[float] = None
    risk_per_trade: Optional[float] = None
    max_positions: Optional[int] = None
    is_active: Optional[bool] = None


class ChallengeResponse(BaseModel):
    """Response model for challenge data"""
    id: int
    name: str
    type: str
    phase: str
    starting_balance: float
    current_balance: float
    profit_target: float
    daily_loss_limit: float
    max_drawdown: float
    risk_per_trade: float
    max_positions: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/templates")
async def get_challenge_templates():
    """Get all available challenge templates"""
    return {"templates": list_templates()}


@router.post("/challenges", response_model=ChallengeResponse, status_code=201)
async def create_challenge(
    challenge: ChallengeCreate,
    template_id: Optional[str] = Query(None, description="Template ID to use"),
    db: Session = Depends(get_db)
):
    """
    Create a new challenge from scratch or from a template.
    If template_id is provided, template values will be used as defaults.
    """
    challenge_data = challenge.dict()
    
    # If template provided, merge with template defaults
    if template_id:
        template = get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
        
        # Template values as base, override with provided values
        for key, value in template.items():
            if key not in challenge_data or challenge_data[key] is None:
                challenge_data[key] = value
    
    # Set current balance to starting balance
    challenge_data['current_balance'] = challenge_data['starting_balance']
    
    db_challenge = Challenge(**challenge_data)
    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    
    return db_challenge


@router.get("/challenges", response_model=List[ChallengeResponse])
async def list_challenges(
    active_only: bool = Query(False, description="Return only active challenges"),
    db: Session = Depends(get_db)
):
    """Get list of all challenges"""
    query = db.query(Challenge)
    
    if active_only:
        query = query.filter(Challenge.is_active == True)
    
    return query.order_by(Challenge.created_at.desc()).all()


@router.get("/challenges/active", response_model=ChallengeResponse)
async def get_active_challenge(db: Session = Depends(get_db)):
    """Get the currently active challenge"""
    challenge = db.query(Challenge).filter(Challenge.is_active == True).first()
    
    if not challenge:
        raise HTTPException(status_code=404, detail="No active challenge found")
    
    return challenge


@router.get("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(challenge_id: int, db: Session = Depends(get_db)):
    """Get a specific challenge by ID"""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    return challenge


@router.put("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def update_challenge(
    challenge_id: int,
    challenge_update: ChallengeUpdate,
    db: Session = Depends(get_db)
):
    """Update a challenge"""
    db_challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Update only provided fields
    update_data = challenge_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_challenge, key, value)
    
    db_challenge.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_challenge)
    
    return db_challenge


@router.post("/challenges/{challenge_id}/activate")
async def activate_challenge(challenge_id: int, db: Session = Depends(get_db)):
    """Set a challenge as active (deactivates all others)"""
    # Deactivate all challenges
    db.query(Challenge).update({Challenge.is_active: False})
    
    # Activate the specified challenge
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge.is_active = True
    db.commit()
    
    return {"message": f"Challenge '{challenge.name}' activated", "challenge_id": challenge_id}


@router.delete("/challenges/{challenge_id}")
async def delete_challenge(challenge_id: int, db: Session = Depends(get_db)):
    """Delete a challenge (and all associated trades, settings, drawings)"""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    db.delete(challenge)
    db.commit()
    
    return {"message": f"Challenge '{challenge.name}' deleted"}
