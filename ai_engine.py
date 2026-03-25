"""
ai_engine.py — Motore di analisi AI con Claude
"""

import os
import json
import asyncio
import logging
import httpx
from typing import Dict, Optional

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL   = "claude-sonnet-4-20250514"

# Pesi del punteggio composito
WEIGHTS = {
    "ranking_gap": 0.35,
    "surface":     0.25,
    "form":        0.20,
    "h2h_risk":    0.20,
}


def compute_rule_based_score(match: Dict) -> Dict:
    """
    Calcola il punteggio composito con regole fisse (veloce, offline).
    Usato come pre-filtro prima di chiamare Claude.
    """
    rank_gap = match.get("rank_gap", 0)
    surface_wr = match.get("fav_surface_wr", 60)
    form_wins = match.get("fav_form_wins", 5)  # vittorie su 10 partite
    h2h_ratio = match.get("h2h_win_ratio", 0.5)

    # Ranking gap (0-100)
    if rank_gap >= 200: rg = 95
    elif rank_gap >= 120: rg = 88
    elif rank_gap >= 80:  rg = 78
    elif rank_gap >= 50:  rg = 68
    elif rank_gap >= 30:  rg = 58
    else:                 rg = 45

    # Surface win rate (0-100)
    if surface_wr >= 80: sv = 90
    elif surface_wr >= 72: sv = 78
    elif surface_wr >= 63: sv = 65
    elif surface_wr >= 55: sv = 52
    else:                  sv = 38

    # Forma recente su 10 partite
    form_pct = form_wins * 10
    if form_pct >= 80: fm = 88
    elif form_pct >= 70: fm = 75
    elif form_pct >= 60: fm = 62
    else:                fm = 48

    # H2H e rischio
    if h2h_ratio >= 0.75:  hr = 85
    elif h2h_ratio >= 0.5: hr = 70
    elif h2h_ratio > 0:    hr = 52
    else:                  hr = 65  # nessun H2H precedente → neutro

    total = int(
        rg * WEIGHTS["ranking_gap"] +
        sv * WEIGHTS["surface"] +
        fm * WEIGHTS["form"] +
        hr * WEIGHTS["h2h_risk"]
    )

    return {
        "score": min(max(total, 0), 100),
        "factor_ranking": rg,
        "factor_surface": sv,
        "factor_form": fm,
        "factor_h2h": hr,
    }


async def analyze_match_with_claude(match: Dict, rule_score: Dict) -> Dict:
    """
    Chiama Claude per un'analisi qualitativa del match.
    Ritorna il dict con score finale e testo di analisi.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY non trovata — uso solo score rule-based")
        return {
            **rule_score,
            "analysis_text": "Analisi AI non disponibile (API key mancante).",
            "model_version": "rule-based"
        }

    prompt = f"""Sei un analista tennistico ATP di alto livello. Analizza questo match e fornisci una valutazione precisa.

DATI MATCH:
Torneo: {match.get('tournament')} | Superficie: {match.get('surface').upper()} | Turno: {match.get('round','')}
Favorito: {match.get('favorite')} (ATP #{match.get('fav_rank')})
Sfidante: {match.get('underdog')} (ATP #{match.get('und_rank')})
Gap di ranking: {match.get('rank_gap')} posizioni
Win rate favorito su {match.get('surface')}: {match.get('fav_surface_wr', '?')}%
Forma recente favorito: {match.get('fav_form_wins', '?')}/10 vittorie
H2H (vinte/perse favorito): {match.get('h2h', '0-0')}

PRE-SCORE ALGORITMICO: {rule_score['score']}/100

Il tuo compito:
1. Valuta se il pre-score è corretto o va aggiustato (±15 punti max)
2. Scrivi un'analisi in italiano di 2-3 frasi, tecnica e concisa

Rispondi ESCLUSIVAMENTE con JSON valido (nessun testo fuori dal JSON):
{{
  "score": <intero 0-100>,
  "analysis_text": "<2-3 frasi in italiano>"
}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            r.raise_for_status()
            data = r.json()
            text = "".join(b.get("text", "") for b in data.get("content", []))
            clean = text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)

            return {
                **rule_score,
                "score": int(parsed.get("score", rule_score["score"])),
                "analysis_text": parsed.get("analysis_text", "—"),
                "model_version": ANTHROPIC_MODEL,
            }

    except Exception as e:
        logger.error(f"Claude API error ({match.get('favorite')} vs {match.get('underdog')}): {e}")
        return {
            **rule_score,
            "analysis_text": f"Analisi parziale: score calcolato su base algoritmica. ({str(e)[:80]})",
            "model_version": "rule-based-fallback",
        }


async def analyze_match_full(match: Dict) -> Optional[Dict]:
    """
    Pipeline completa: rule-based → Claude.
    Ritorna None se il match non supera il filtro minimo (rank_gap < 20).
    """
    # Filtro preliminare rapido
    if match.get("rank_gap", 0) < 20:
        logger.debug(f"Scartato (gap troppo basso): {match.get('player1')} vs {match.get('player2')}")
        return None

    rule_score = compute_rule_based_score(match)

    # Se lo score è molto basso, non sprechiamo chiamate API
    if rule_score["score"] < 45:
        return {
            **rule_score,
            "analysis_text": "Partita equilibrata — non supera i criteri di selezione.",
            "model_version": "rule-based",
        }

    # Chiamata Claude per i match sopra soglia
    return await analyze_match_with_claude(match, rule_score)
