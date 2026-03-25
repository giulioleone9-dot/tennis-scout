"""
routes/analysis.py — Endpoint per avviare l'analisi AI
"""

import asyncio
import aiosqlite
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime, timedelta

from database import DB_PATH
from scraper import (
    fetch_atp_rankings,
    fetch_upcoming_matches,
    enrich_matches_with_rankings,
)
from ai_engine import analyze_match_full
from schemas import BulkAnalysisResponse, AnalysisRequest

router = APIRouter()
logger = logging.getLogger(__name__)

# Stato globale semplice per tracciare il job in corso
_job_state = {"running": False, "progress": 0, "total": 0, "done": False}


@router.post("/run", response_model=BulkAnalysisResponse)
async def run_full_analysis(background_tasks: BackgroundTasks, days: int = 7):
    """
    Avvia in background:
    1. Scraping partite ATP prossimi N giorni
    2. Arricchimento con ranking
    3. Analisi AI match per match
    4. Salvataggio nel DB
    """
    if _job_state["running"]:
        return BulkAnalysisResponse(
            started=False,
            total_matches=0,
            message="Analisi già in corso. Attendi che termini."
        )

    background_tasks.add_task(_run_analysis_job, days)
    return BulkAnalysisResponse(
        started=True,
        total_matches=0,
        message=f"Analisi avviata per i prossimi {days} giorni. Usa /api/analysis/status per seguire il progresso."
    )


@router.post("/single/{match_id}")
async def analyze_single_match(match_id: int):
    """(Re)analizza un singolo match già nel DB."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM matches WHERE id = ?", (match_id,)) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Match non trovato")

    match = dict(row)
    result = await analyze_match_full(match)

    if result is None:
        raise HTTPException(status_code=422, detail="Match non supera i criteri minimi")

    await _save_prediction(match_id, result)
    return {"match_id": match_id, "score": result["score"], "analysis": result["analysis_text"]}


@router.get("/status")
async def get_analysis_status():
    """Ritorna lo stato del job di analisi in corso."""
    return {
        "running": _job_state["running"],
        "progress": _job_state["progress"],
        "total": _job_state["total"],
        "done": _job_state["done"],
        "pct": (
            round(_job_state["progress"] / _job_state["total"] * 100)
            if _job_state["total"] > 0 else 0
        )
    }


# ── Job interno ─────────────────────────────────────────────────────────────

async def _run_analysis_job(days: int):
    _job_state.update({"running": True, "progress": 0, "total": 0, "done": False})

    try:
        logger.info("Job analisi: recupero ranking...")
        rankings = await fetch_atp_rankings()

        logger.info("Job analisi: recupero partite...")
        raw_matches = await fetch_upcoming_matches(days_ahead=days)

        logger.info("Job analisi: arricchimento con ranking...")
        matches = await enrich_matches_with_rankings(raw_matches, rankings)

        _job_state["total"] = len(matches)
        logger.info(f"Job analisi: {len(matches)} partite da analizzare")

        for i, match in enumerate(matches):
            try:
                # Salva/aggiorna il match nel DB
                match_id = await _upsert_match(match)

                # Analisi AI
                result = await analyze_match_full(match)
                if result:
                    await _save_prediction(match_id, result)

                _job_state["progress"] = i + 1
                await asyncio.sleep(0.3)  # gentilezza verso l'API

            except Exception as e:
                logger.error(f"Errore match {match.get('player1')} vs {match.get('player2')}: {e}")

        logger.info("Job analisi completato.")

    except Exception as e:
        logger.error(f"Job analisi fallito: {e}")
    finally:
        _job_state.update({"running": False, "done": True})


async def _upsert_match(match: dict) -> int:
    """Inserisce o aggiorna un match nel DB. Ritorna l'id."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Prova insert, se esiste per ext_id aggiorna
        await db.execute("""
            INSERT INTO matches
                (ext_id, tournament, surface, round, match_date,
                 player1, player2, rank1, rank2,
                 favorite, underdog, fav_rank, und_rank, rank_gap, tour)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(ext_id) DO UPDATE SET
                rank1 = excluded.rank1,
                rank2 = excluded.rank2,
                favorite = excluded.favorite,
                underdog = excluded.underdog,
                fav_rank = excluded.fav_rank,
                und_rank = excluded.und_rank,
                rank_gap = excluded.rank_gap
        """, (
            match.get("ext_id"), match["tournament"], match["surface"],
            match.get("round"), match["match_date"],
            match["player1"], match["player2"],
            match.get("rank1"), match.get("rank2"),
            match.get("favorite"), match.get("underdog"),
            match.get("fav_rank"), match.get("und_rank"),
            match.get("rank_gap"), match.get("tour", "ATP"),
        ))
        await db.commit()

        async with db.execute(
            "SELECT id FROM matches WHERE ext_id = ? OR "
            "(player1 = ? AND player2 = ? AND match_date = ?)",
            (match.get("ext_id"), match["player1"], match["player2"], match["match_date"])
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else -1


async def _save_prediction(match_id: int, result: dict):
    """Salva (o aggiorna) la predizione per un match."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Elimina predizione esistente se presente
        await db.execute("DELETE FROM predictions WHERE match_id = ?", (match_id,))
        await db.execute("""
            INSERT INTO predictions
                (match_id, score, analysis_text,
                 factor_ranking, factor_surface, factor_form, factor_h2h,
                 model_version)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            match_id,
            result["score"],
            result.get("analysis_text", ""),
            result.get("factor_ranking", 0),
            result.get("factor_surface", 0),
            result.get("factor_form", 0),
            result.get("factor_h2h", 0),
            result.get("model_version", "unknown"),
        ))
        await db.commit()
