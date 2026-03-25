# 🎾 Tennis Scout

Sistema AI per la previsione di partite tennis ATP.  
Stack: **FastAPI** (backend) + **React/Vite** (frontend) + **SQLite** (database) + **Claude AI** (analisi)

---

## Struttura del progetto

```
tennis-scout/
├── backend/
│   ├── main.py          ← FastAPI app principale
│   ├── database.py      ← SQLite asincrono
│   ├── schemas.py       ← Modelli Pydantic
│   ├── scraper.py       ← Scraping ATP (Sofascore + UTS)
│   ├── ai_engine.py     ← Motore di analisi Claude AI
│   ├── routes/
│   │   ├── matches.py   ← GET/DELETE partite
│   │   ├── analysis.py  ← POST avvia analisi AI
│   │   ├── history.py   ← Storico e accuratezza
│   │   └── scheduler.py ← Scheduler automatico
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── App.jsx          ← Dashboard React
```

---

## Setup Backend (5 minuti)

### 1. Installa Python 3.11+
Scarica da https://python.org se non ce l'hai.

### 2. Crea ambiente virtuale e installa dipendenze
```bash
cd tennis-scout/backend

# Crea ambiente virtuale
python -m venv venv

# Attivalo (Windows)
venv\Scripts\activate
# Attivalo (Mac/Linux)
source venv/bin/activate

# Installa librerie
pip install -r requirements.txt
```

### 3. Crea il file .env
```bash
# Copia il file di esempio
cp .env.example .env

# Apri .env e inserisci la tua API key di Anthropic
# Ottienila su: https://console.anthropic.com
```

Il file `.env` deve contenere:
```
ANTHROPIC_API_KEY=sk-ant-la-tua-chiave-qui
```

### 4. Avvia il backend
```bash
uvicorn main:app --reload --port 8000
```

Il backend sarà disponibile su http://localhost:8000  
Documentazione API interattiva: http://localhost:8000/docs

---

## Setup Frontend (5 minuti)

### 1. Installa Node.js
Scarica da https://nodejs.org (versione LTS)

### 2. Crea il progetto React
```bash
# Nella cartella tennis-scout
npm create vite@latest frontend-app -- --template react

cd frontend-app
npm install
```

### 3. Sostituisci App.jsx
Copia il contenuto di `frontend/App.jsx` dentro `frontend-app/src/App.jsx`

### 4. Avvia la dashboard
```bash
npm run dev
```

La dashboard sarà su http://localhost:5173

---

## Come usarlo

### Flusso base
1. Apri la dashboard su http://localhost:5173
2. Clicca **"Analizza settimana"**
3. Il sistema:
   - Scarica le partite ATP dei prossimi 7 giorni da Sofascore
   - Recupera i ranking correnti
   - Calcola lo score di confidenza con regole + Claude AI
   - Salva tutto nel database
4. Vedi le partite ordinate per score
5. Usa i filtri per vedere solo le partite "Alta confidenza" (≥72)

### Registrare i risultati reali
Dopo ogni partita, clicca **"[Giocatore] vince"** nella card.  
Il sistema traccia l'accuratezza nel tempo e la mostra nel pannello statistiche.

### Scheduler automatico (facoltativo)
Per analisi automatiche ogni 3 giorni:
```bash
# Via API (il backend deve girare)
curl -X POST "http://localhost:8000/api/scheduler/start?interval_days=3"

# Per fermarlo
curl -X POST "http://localhost:8000/api/scheduler/stop"
```

---

## Endpoints principali

| Metodo | URL | Descrizione |
|--------|-----|-------------|
| GET    | /api/matches/ | Lista partite con predizioni |
| GET    | /api/matches/{id} | Singola partita |
| POST   | /api/analysis/run | Avvia analisi completa |
| GET    | /api/analysis/status | Stato analisi in corso |
| POST   | /api/analysis/single/{id} | Rianalizza un match |
| POST   | /api/history/result | Registra risultato reale |
| GET    | /api/history/accuracy | Statistiche accuratezza |
| POST   | /api/scheduler/start | Avvia scheduler auto |
| GET    | /api/scheduler/status | Stato scheduler |

---

## Prossimi upgrade

- [ ] Integrazione API SportRadar (dati più affidabili)
- [ ] Notifiche email/Telegram con le migliori giocate
- [ ] Analisi forma basata su scraping H2H reale
- [ ] Backtest su dati storici (2020-2024)
- [ ] Deploy su cloud (Railway, Render, ecc.)
