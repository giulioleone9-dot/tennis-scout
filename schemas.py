"""
schemas.py — Modelli Pydantic per request/response
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class MatchBase(BaseModel):
    tournament: str
    surface: str  # clay | hard | grass
    round: Optional[str] = None
    match_date: str
    player1: str
    player2: str
    rank1: Optional[int] = None
    rank2: Optional[int] = None
    tour: str = "ATP"


class MatchCreate(MatchBase):
    ext_id: Optional[str] = None


class PredictionOut(BaseModel):
    score: int
    analysis_text: str
    factor_ranking: int
    factor_surface: int
    factor_form: int
    factor_h2h: int
    model_version: str
    created_at: str

    class Config:
        from_attributes = True


class MatchOut(BaseModel):
    id: int
    ext_id: Optional[str]
    tournament: str
    surface: str
    round: Optional[str]
    match_date: str
    player1: str
    player2: str
    rank1: Optional[int]
    rank2: Optional[int]
    favorite: Optional[str]
    underdog: Optional[str]
    fav_rank: Optional[int]
    und_rank: Optional[int]
    rank_gap: Optional[int]
    tour: str
    prediction: Optional[PredictionOut] = None

    class Config:
        from_attributes = True


class ResultCreate(BaseModel):
    match_id: int
    winner: str
    score_set: Optional[str] = None


class ResultOut(BaseModel):
    id: int
    match_id: int
    winner: str
    score_set: Optional[str]
    correct: Optional[int]
    recorded_at: str

    class Config:
        from_attributes = True


class AccuracyStats(BaseModel):
    total_predictions: int
    total_results: int
    correct: int
    accuracy_pct: float
    high_confidence_accuracy: float  # score >= 72
    avg_score: float


class AnalysisRequest(BaseModel):
    match_id: int


class BulkAnalysisResponse(BaseModel):
    started: bool
    total_matches: int
    message: str


class SchedulerStatus(BaseModel):
    last_run: Optional[str]
    next_run: Optional[str]
    status: str
    last_matches_found: int
    last_matches_scored: int
