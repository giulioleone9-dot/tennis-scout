"""
scraper.py — Scraping dati ATP da Sofascore e UltimateTennisStatistics
"""

import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
}


async def fetch_atp_rankings(top_n: int = 300) -> Dict[str, int]:
    """
    Scarica il ranking ATP corrente da UltimateTennisStatistics.
    Ritorna { "Nome Giocatore": posizione_ranking }
    """
    url = "https://www.ultimatetennisstatistics.com/rankingsTable"
    params = {"rankType": "POINTS", "season": 0, "level": "ALL", "surface": "ALL", "rows": top_n}

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=20.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            rankings = {}
            for item in data.get("rows", [])[:top_n]:
                name = item.get("name", "").strip()
                rank = int(item.get("rank", 999))
                if name:
                    rankings[name] = rank
            logger.info(f"Rankings ATP: {len(rankings)} giocatori")
            return rankings
    except Exception as e:
        logger.error(f"Errore fetch rankings: {e}")
        return {}


async def fetch_upcoming_matches(days_ahead: int = 7) -> List[Dict]:
    """
    Recupera le partite ATP dei prossimi N giorni da Sofascore.
    """
    matches = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        for i in range(days_ahead):
            date_str = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"https://api.sofascore.com/api/v1/sport/tennis/scheduled-events/{date_str}"

            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()

                for event in data.get("events", []):
                    tournament = event.get("tournament", {})
                    category_name = tournament.get("category", {}).get("name", "")

                    # Solo ATP e WTA — niente Challenger/ITF
                    if "ATP" not in category_name and "WTA" not in category_name:
                        continue

                    home = event.get("homeTeam", {}).get("name", "").strip()
                    away = event.get("awayTeam", {}).get("name", "").strip()
                    if not home or not away:
                        continue

                    surface_raw = tournament.get("groundType", "hard").lower()
                    surface = {"clay": "clay", "hard": "hard", "grass": "grass"}.get(
                        surface_raw, "hard"
                    )

                    matches.append({
                        "ext_id": str(event.get("id", "")),
                        "tournament": tournament.get("name", "Unknown"),
                        "surface": surface,
                        "round": event.get("roundInfo", {}).get("name", ""),
                        "match_date": date_str,
                        "player1": home,
                        "player2": away,
                        "tour": "ATP" if "ATP" in category_name else "WTA",
                    })

                await asyncio.sleep(0.4)  # pausa cortesia

            except Exception as e:
                logger.warning(f"Sofascore {date_str}: {e}")

    logger.info(f"Partite trovate: {len(matches)}")
    return matches


async def fetch_player_surface_stats(player_name: str, surface: str) -> Dict:
    """
    Recupera le statistiche win/loss di un giocatore su una superficie
    (ultimi 3 anni) da UltimateTennisStatistics.
    """
    surface_map = {"clay": "CLAY", "hard": "HARD", "grass": "GRASS"}
    surf = surface_map.get(surface, "HARD")

    # Build URL del profilo
    parts = player_name.strip().split()
    if len(parts) >= 2:
        name_param = f"{parts[-1]} {parts[0]}"
    else:
        name_param = player_name

    url = "https://www.ultimatetennisstatistics.com/playerProfile"
    params = {"name": name_param, "tab": "statistics", "surface": surf, "season": 0}

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
            r = await client.get(url, params=params)
            # Parsing HTML base — cerca la riga W/L per superficie
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")

            for row in soup.select("table.table tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).upper()
                    if surf in label or surface.upper() in label:
                        wl = cells[1].get_text(strip=True)
                        if "/" in wl:
                            w, l = wl.split("/", 1)
                            w, l = int(w.strip()), int(l.strip())
                            total = w + l
                            if total >= 5:
                                return {
                                    "win_rate": round(w / total * 100, 1),
                                    "wins": w, "losses": l, "matches": total
                                }
    except Exception as e:
        logger.debug(f"Stats {player_name}: {e}")

    # Fallback neutro
    return {"win_rate": 60.0, "wins": 0, "losses": 0, "matches": 0}


async def enrich_matches_with_rankings(
    matches: List[Dict], rankings: Dict[str, int]
) -> List[Dict]:
    """
    Aggiunge rank1, rank2, favorite, underdog, rank_gap a ogni match.
    """
    enriched = []
    for m in matches:
        r1 = rankings.get(m["player1"], 500)
        r2 = rankings.get(m["player2"], 500)

        if r1 <= r2:
            fav, und, fr, ur = m["player1"], m["player2"], r1, r2
        else:
            fav, und, fr, ur = m["player2"], m["player1"], r2, r1

        enriched.append({
            **m,
            "rank1": r1,
            "rank2": r2,
            "favorite": fav,
            "underdog": und,
            "fav_rank": fr,
            "und_rank": ur,
            "rank_gap": ur - fr,
        })

    return enriched
