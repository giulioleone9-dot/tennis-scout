"""
routes/history.py — Storico predizioni e calcolo accuratezza
"""

import aiosqlite
from fastapi import APIRouter, HTTPException
from typing import List

from database import DB_PATH
from schemas import ResultCreate, ResultOut, AccuracyStats

router = APIRouter()


@router.post("/result", response_model=ResultOut, status_code=201)
async def record_result(payload: ResultCreate):
    """
    Registra il risultato reale di un match e calcola se la predizione era corretta.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Recupera il match e la predizione
        async with db.execute(
            "SELECT favorite FROM matches WHERE id = ?", (payload.match_id,)
        ) as cur:
            match_row = await cur.fetchone()

        if not match_row:
            raise HTTPException(status_code=404, detail="Match non trovato")

        async with db.execute(
            "SELECT score FROM predictions WHERE match_id = ?", (payload.match_id,)
        ) as cur:
            pred_row = await cur.fetchone()

        favorite = match_row["favorite"]
        correct = None
        if pred_row and pred_row["score"] is not None:
            correct = 1 if payload.winner == favorite else 0

        await db.execute("""
            INSERT INTO results (match_id, winner, score_set, correct)
            VALUES (?, ?, ?, ?)
        """, (payload.match_id, payload.winner, payload.score_set, correct))
        await db.commit()

        async with db.execute(
            "SELECT * FROM results WHERE match_id = ? ORDER BY id DESC LIMIT 1",
            (payload.match_id,)
        ) as cur:
            row = await cur.fetchone()

        return ResultOut(**dict(row))


@router.get("/accuracy", response_model=AccuracyStats)
async def get_accuracy():
    """
    Calcola le statistiche di accuratezza sulle predizioni con risultato registrato.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT COUNT(*) AS n FROM predictions") as cur:
            total_pred = (await cur.fetchone())["n"]

        async with db.execute("""
            SELECT
                COUNT(*)         AS total,
                SUM(r.correct)   AS correct_sum,
                AVG(p.score)     AS avg_score
            FROM results r
            JOIN predictions p ON p.match_id = r.match_id
            WHERE r.correct IS NOT NULL
        """) as cur:
            row = dict(await cur.fetchone())

        total_res = row["total"] or 0
        correct   = int(row["correct_sum"] or 0)
        avg_score = round(float(row["avg_score"] or 0), 1)
        acc_pct   = round(correct / total_res * 100, 1) if total_res > 0 else 0.0

        # Accuratezza solo su alta confidenza (score >= 72)
        async with db.execute("""
            SELECT COUNT(*) AS total, SUM(r.correct) AS correct_sum
            FROM results r
            JOIN predictions p ON p.match_id = r.match_id
            WHERE p.score >= 72 AND r.correct IS NOT NULL
        """) as cur:
            hc = dict(await cur.fetchone())

        hc_total   = hc["total"] or 0
        hc_correct = int(hc["correct_sum"] or 0)
        hc_acc     = round(hc_correct / hc_total * 100, 1) if hc_total > 0 else 0.0

    return AccuracyStats(
        total_predictions=total_pred,
        total_results=total_res,
        correct=correct,
        accuracy_pct=acc_pct,
        high_confidence_accuracy=hc_acc,
        avg_score=avg_score,
    )


@router.get("/results", response_model=List[ResultOut])
async def list_results(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM results ORDER BY recorded_at DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
    return [ResultOut(**dict(r)) for r in rows]
