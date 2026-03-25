"""
routes/scheduler.py — Scheduler automatico ogni N giorni
"""

import asyncio
import aiosqlite
import logging
from fastapi import APIRouter, BackgroundTasks
from datetime import datetime, timedelta

from database import DB_PATH
from schemas import SchedulerStatus

router  = APIRouter()
logger  = logging.getLogger(__name__)

_sched_state = {
    "active": False,
    "interval_days": 3,
    "last_run": None,
    "next_run": None,
    "last_matches_found": 0,
    "last_matches_scored": 0,
    "status": "idle",
}
_sched_task = None


@router.post("/start")
async def start_scheduler(background_tasks: BackgroundTasks, interval_days: int = 3):
    """Avvia lo scheduler automatico ogni N giorni."""
    global _sched_task
    if _sched_state["active"]:
        return {"message": "Scheduler già attivo", "interval_days": _sched_state["interval_days"]}

    _sched_state["interval_days"] = interval_days
    _sched_state["active"] = True
    _sched_state["status"] = "running"
    background_tasks.add_task(_scheduler_loop)
    return {"message": f"Scheduler avviato — analisi ogni {interval_days} giorni"}


@router.post("/stop")
async def stop_scheduler():
    """Ferma lo scheduler automatico."""
    _sched_state["active"] = False
    _sched_state["status"] = "stopped"
    return {"message": "Scheduler fermato"}


@router.get("/status", response_model=SchedulerStatus)
async def scheduler_status():
    return SchedulerStatus(
        last_run=_sched_state["last_run"],
        next_run=_sched_state["next_run"],
        status=_sched_state["status"],
        last_matches_found=_sched_state["last_matches_found"],
        last_matches_scored=_sched_state["last_matches_scored"],
    )


# ── Loop interno ─────────────────────────────────────────────────────────────

async def _scheduler_loop():
    """Esegue il job di analisi ogni N giorni."""
    from routes.analysis import _run_analysis_job

    while _sched_state["active"]:
        now = datetime.now()
        _sched_state["last_run"] = now.isoformat()
        _sched_state["next_run"] = (now + timedelta(days=_sched_state["interval_days"])).isoformat()
        _sched_state["status"] = "analyzing"

        logger.info(f"Scheduler: avvio analisi automatica ({now.strftime('%d/%m/%Y %H:%M')})")

        try:
            await _run_analysis_job(days=7)
            await _log_scheduler_run(status="ok")
            _sched_state["status"] = "waiting"
            logger.info(f"Scheduler: analisi completata. Prossima: {_sched_state['next_run']}")

        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await _log_scheduler_run(status="error", error=str(e))
            _sched_state["status"] = "error"

        # Attendi N giorni (controllando ogni ora se lo scheduler è stato fermato)
        wait_seconds = _sched_state["interval_days"] * 86400
        elapsed = 0
        while elapsed < wait_seconds and _sched_state["active"]:
            await asyncio.sleep(3600)
            elapsed += 3600


async def _log_scheduler_run(status: str, error: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO scheduler_log (status, matches_found, matches_scored, error_msg)
            VALUES (?, ?, ?, ?)
        """, (
            status,
            _sched_state["last_matches_found"],
            _sched_state["last_matches_scored"],
            error
        ))
        await db.commit()
