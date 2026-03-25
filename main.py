"""
Tennis Scout — FastAPI Backend
================================
Avvio: uvicorn main:app --reload --port 8000
Docs:  http://localhost:8000/docs
"""

import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from database import init_db
from routes import matches, analysis, history, scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializza il database e lo scheduler all'avvio."""
    logger.info("Tennis Scout backend avviato — inizializzazione DB...")
    await init_db()
    logger.info("Database pronto.")
    yield
    logger.info("Shutdown.")


app = FastAPI(
    title="Tennis Scout API",
    description="Backend per la previsione di partite tennis ATP con AI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — permette alla dashboard React di chiamare il backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra i router
app.include_router(matches.router,  prefix="/api/matches",  tags=["Partite"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analisi AI"])
app.include_router(history.router,  prefix="/api/history",  tags=["Storico"])
app.include_router(scheduler.router,prefix="/api/scheduler",tags=["Scheduler"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Tennis Scout API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
