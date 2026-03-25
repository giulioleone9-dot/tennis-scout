"""
database.py — Gestione database SQLite asincrono
"""

import aiosqlite
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "tennis_scout.db")


async def init_db():
    """Crea le tabelle se non esistono."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS matches (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ext_id      TEXT UNIQUE,
                tournament  TEXT NOT NULL,
                surface     TEXT NOT NULL,
                round       TEXT,
                match_date  TEXT NOT NULL,
                player1     TEXT NOT NULL,
                player2     TEXT NOT NULL,
                rank1       INTEGER,
                rank2       INTEGER,
                favorite    TEXT,
                underdog    TEXT,
                fav_rank    INTEGER,
                und_rank    INTEGER,
                rank_gap    INTEGER,
                tour        TEXT DEFAULT 'ATP',
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS predictions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id        INTEGER NOT NULL REFERENCES matches(id),
                score           INTEGER NOT NULL,
                analysis_text   TEXT,
                factor_ranking  INTEGER,
                factor_surface  INTEGER,
                factor_form     INTEGER,
                factor_h2h      INTEGER,
                model_version   TEXT DEFAULT 'claude-sonnet-4',
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id    INTEGER NOT NULL REFERENCES matches(id),
                winner      TEXT,
                score_set   TEXT,
                correct     INTEGER,   -- 1 se la predizione era giusta, 0 altrimenti
                recorded_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS scheduler_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at     TEXT DEFAULT (datetime('now')),
                status     TEXT,
                matches_found   INTEGER DEFAULT 0,
                matches_scored  INTEGER DEFAULT 0,
                error_msg  TEXT
            );
        """)
        await db.commit()


async def get_db():
    """Context manager per una connessione al DB."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
