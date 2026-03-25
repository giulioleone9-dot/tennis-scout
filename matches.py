"""
routes/matches.py — Endpoints per le partite
"""

import aiosqlite
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from database import DB_PATH
from schemas import MatchOut, MatchCreate

router = APIRouter()


@router.get("/", response_model=List[MatchOut])
async def get_matches(
    days: int = Query(7, description="Partite degli ultimi/prossimi N giorni"),
    surface: Optional[str] = Query(None, description="clay | hard | grass"),
    min_score: Optional[int] = Query(None, description="Score minimo predizione"),
    tour: Optional[str] = Query("ATP", description="ATP | WTA"),
    limit: int = Query(50, le=200),
):
    """Ritorna le partite con le relative predizioni AI."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        date_to   = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        query = """
            SELECT
                m.*,
                p.score,
                p.analysis_text,
                p.factor_ranking,
                p.factor_surface,
                p.factor_form,
                p.factor_h2h,
                p.model_version,
                p.created_at AS pred_created_at
            FROM matches m
            LEFT JOIN predictions p ON p.match_id = m.id
            WHERE m.match_date BETWEEN ? AND ?
        """
        params: list = [date_from, date_to]

        if surface:
            query += " AND m.surface = ?"
            params.append(surface)
        if tour:
            query += " AND m.tour = ?"
            params.append(tour)
        if min_score is not None:
            query += " AND p.score >= ?"
            params.append(min_score)

        query += " ORDER BY p.score DESC NULLS LAST, m.match_date ASC LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        results = []
        for row in rows:
            m = dict(row)
            pred = None
            if m.get("score") is not None:
                pred = {
                    "score": m["score"],
                    "analysis_text": m["analysis_text"] or "",
                    "factor_ranking": m["factor_ranking"] or 0,
                    "factor_surface": m["factor_surface"] or 0,
                    "factor_form": m["factor_form"] or 0,
                    "factor_h2h": m["factor_h2h"] or 0,
                    "model_version": m["model_version"] or "",
                    "created_at": m["pred_created_at"] or "",
                }
            results.append(MatchOut(
                id=m["id"],
                ext_id=m.get("ext_id"),
                tournament=m["tournament"],
                surface=m["surface"],
                round=m.get("round"),
                match_date=m["match_date"],
                player1=m["player1"],
                player2=m["player2"],
                rank1=m.get("rank1"),
                rank2=m.get("rank2"),
                favorite=m.get("favorite"),
                underdog=m.get("underdog"),
                fav_rank=m.get("fav_rank"),
                und_rank=m.get("und_rank"),
                rank_gap=m.get("rank_gap"),
                tour=m.get("tour", "ATP"),
                prediction=pred,
            ))

        return results


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(match_id: int):
    """Ritorna un singolo match con predizione."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT m.*, p.score, p.analysis_text,
                      p.factor_ranking, p.factor_surface,
                      p.factor_form, p.factor_h2h,
                      p.model_version, p.created_at AS pred_created_at
               FROM matches m
               LEFT JOIN predictions p ON p.match_id = m.id
               WHERE m.id = ?""",
            (match_id,)
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Match non trovato")

    m = dict(row)
    pred = None
    if m.get("score") is not None:
        pred = {
            "score": m["score"],
            "analysis_text": m["analysis_text"] or "",
            "factor_ranking": m["factor_ranking"] or 0,
            "factor_surface": m["factor_surface"] or 0,
            "factor_form": m["factor_form"] or 0,
            "factor_h2h": m["factor_h2h"] or 0,
            "model_version": m["model_version"] or "",
            "created_at": m["pred_created_at"] or "",
        }
    return MatchOut(
        id=m["id"], ext_id=m.get("ext_id"),
        tournament=m["tournament"], surface=m["surface"],
        round=m.get("round"), match_date=m["match_date"],
        player1=m["player1"], player2=m["player2"],
        rank1=m.get("rank1"), rank2=m.get("rank2"),
        favorite=m.get("favorite"), underdog=m.get("underdog"),
        fav_rank=m.get("fav_rank"), und_rank=m.get("und_rank"),
        rank_gap=m.get("rank_gap"), tour=m.get("tour", "ATP"),
        prediction=pred,
    )


@router.delete("/{match_id}", status_code=204)
async def delete_match(match_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM predictions WHERE match_id = ?", (match_id,))
        await db.execute("DELETE FROM results    WHERE match_id = ?", (match_id,))
        await db.execute("DELETE FROM matches    WHERE id = ?",       (match_id,))
        await db.commit()
