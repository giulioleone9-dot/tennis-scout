import { useState, useEffect, useCallback, useRef } from "react";

const API_BASE = "https://3b4773b6-6b24-47ab-aaf0-5f00d0db71e3-00-14zqmfmdg191f.worf.replit.dev";

const FONTS = `@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');`;

const CSS = `
  * { box-sizing: border-box; margin: 0; padding: 0; }

  .app {
    min-height: 100vh;
    background: #0a0e14;
    color: #c8d0db;
    font-family: 'DM Sans', sans-serif;
    padding: 0 0 60px;
  }

  .header {
    border-bottom: 1px solid #1e2730;
    padding: 18px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    background: rgba(10,14,20,0.97);
    backdrop-filter: blur(8px);
    z-index: 100;
  }
  .logo {
    display: flex; align-items: center; gap: 10px;
    font-family: 'Space Mono', monospace;
    font-size: 15px; font-weight: 700;
    color: #e8f0fb; letter-spacing: -0.5px;
  }
  .logo-dot {
    width: 8px; height: 8px;
    background: #3de89b; border-radius: 50%;
    box-shadow: 0 0 10px #3de89b88;
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

  .header-right {
    display: flex; align-items: center; gap: 16px;
    font-size: 12px; color: #4a5568;
    font-family: 'Space Mono', monospace;
  }
  .live-badge {
    background: #3de89b18; border: 1px solid #3de89b44;
    color: #3de89b; padding: 3px 8px; border-radius: 4px;
    font-size: 10px; letter-spacing: 1px; font-weight: 700;
  }
  .status-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #3de89b; display: inline-block; margin-right: 6px;
  }
  .status-dot.offline { background: #e85555; }

  .main { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }

  /* Stats row */
  .stats-row {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 12px; margin-bottom: 32px;
  }
  .stat-card {
    background: #111820; border: 1px solid #1e2730;
    border-radius: 10px; padding: 18px 20px; transition: border-color 0.2s;
  }
  .stat-card:hover { border-color: #2a3a4a; }
  .stat-label {
    font-size: 10px; font-family: 'Space Mono', monospace;
    color: #4a5568; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 6px;
  }
  .stat-value { font-size: 26px; font-weight: 600; color: #e8f0fb; line-height: 1; }
  .stat-sub { font-size: 11px; color: #4a5568; margin-top: 4px; }
  .stat-card.accent .stat-value { color: #3de89b; }
  .stat-card.warn .stat-value { color: #f5c842; }

  /* Section */
  .section-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;
  }
  .section-title {
    font-family: 'Space Mono', monospace; font-size: 11px;
    letter-spacing: 1.5px; text-transform: uppercase; color: #4a5568;
  }

  .btn-row { display: flex; gap: 10px; align-items: center; }

  .btn-primary {
    background: #3de89b; color: #030f09; border: none;
    border-radius: 8px; padding: 10px 20px;
    font-family: 'Space Mono', monospace; font-size: 12px;
    font-weight: 700; cursor: pointer; display: flex;
    align-items: center; gap: 8px; transition: all 0.2s; letter-spacing: 0.5px;
  }
  .btn-primary:hover { background: #50f0a8; transform: translateY(-1px); }
  .btn-primary:disabled { background: #1e2730; color: #4a5568; cursor: not-allowed; transform: none; }

  .btn-secondary {
    background: transparent; color: #6a8099;
    border: 1px solid #1e2730; border-radius: 8px; padding: 9px 16px;
    font-family: 'Space Mono', monospace; font-size: 11px;
    cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s;
  }
  .btn-secondary:hover { border-color: #2a3a4a; color: #8a9bb0; }

  /* Progress bar */
  .progress-bar-wrap {
    background: #111820; border: 1px solid #1e2730; border-radius: 8px;
    padding: 14px 20px; margin-bottom: 20px;
  }
  .progress-bar-label {
    display: flex; justify-content: space-between; margin-bottom: 8px;
    font-size: 12px; font-family: 'Space Mono', monospace; color: #6a8099;
  }
  .progress-bar-bg { background: #1a2535; border-radius: 3px; height: 4px; }
  .progress-bar-fill {
    background: #3de89b; height: 100%; border-radius: 3px;
    transition: width 0.4s ease; box-shadow: 0 0 8px #3de89b66;
  }

  /* Spinner */
  .spinner {
    width: 14px; height: 14px; border: 2px solid rgba(3,15,9,0.4);
    border-top-color: #030f09; border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Match cards */
  .matches-grid { display: grid; gap: 12px; }

  .match-card {
    background: #111820; border: 1px solid #1e2730;
    border-radius: 12px; padding: 20px 24px;
    transition: all 0.2s; position: relative; overflow: hidden;
  }
  .match-card::before {
    content: ''; position: absolute;
    left: 0; top: 0; bottom: 0; width: 3px;
    border-radius: 12px 0 0 12px; background: #1e2730; transition: background 0.3s;
  }
  .match-card.high::before { background: #3de89b; box-shadow: 0 0 12px #3de89b66; }
  .match-card.medium::before { background: #f5c842; }
  .match-card.low::before { background: #e85555; }
  .match-card.none::before { background: #2a3a4a; }
  .match-card:hover { border-color: #2a3a4a; background: #131c26; }

  .match-top {
    display: flex; align-items: flex-start;
    justify-content: space-between; margin-bottom: 14px;
  }
  .match-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }

  .badge {
    font-size: 10px; font-family: 'Space Mono', monospace;
    padding: 2px 7px; border-radius: 4px; letter-spacing: 0.5px;
  }
  .badge-neutral { background: #1a2535; border: 1px solid #243040; color: #6a8099; }
  .badge-clay    { background: #2a1a10; border: 1px solid #5a2e15; color: #c2724a; }
  .badge-hard    { background: #101a2a; border: 1px solid #153060; color: #4a8acc; }
  .badge-grass   { background: #0e2015; border: 1px solid #1e4525; color: #4ab870; }

  .players { display: flex; align-items: center; gap: 12px; }
  .player { display: flex; flex-direction: column; gap: 2px; }
  .player-name { font-size: 16px; font-weight: 600; color: #c8d0db; letter-spacing: -0.3px; }
  .player-name.favorite { color: #ffffff; }
  .player-rank { font-size: 11px; font-family: 'Space Mono', monospace; color: #4a5568; }
  .vs-sep { font-size: 11px; font-family: 'Space Mono', monospace; color: #2a3a4a; padding: 0 4px; }

  .tags { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
  .tag {
    font-size: 10px; font-family: 'Space Mono', monospace;
    background: #1a2535; border: 1px solid #243040;
    color: #6a8099; padding: 2px 7px; border-radius: 4px;
  }

  /* Score circle */
  .score-block { display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 72px; }
  .score-circle {
    width: 60px; height: 60px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Mono', monospace; font-size: 18px; font-weight: 700;
  }
  .score-circle.high { background: #0d2a1a; border: 2px solid #3de89b; color: #3de89b; box-shadow: 0 0 20px #3de89b33; }
  .score-circle.medium { background: #2a2210; border: 2px solid #f5c842; color: #f5c842; box-shadow: 0 0 20px #f5c84233; }
  .score-circle.low { background: #2a1010; border: 2px solid #e85555; color: #e85555; box-shadow: 0 0 20px #e8555533; }
  .score-circle.none { background: #1a2535; border: 2px solid #2a3a4a; color: #4a5568; }

  .score-label { font-size: 9px; font-family: 'Space Mono', monospace; letter-spacing: 1px; text-transform: uppercase; }
  .score-label.high { color: #3de89b; }
  .score-label.medium { color: #f5c842; }
  .score-label.low { color: #e85555; }
  .score-label.none { color: #4a5568; }

  /* Factors */
  .rating-bars { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 20px; margin-top: 10px; }
  .rating-item { display: flex; flex-direction: column; gap: 4px; }
  .rating-label { font-size: 10px; font-family: 'Space Mono', monospace; color: #4a5568; letter-spacing: 0.5px; }
  .rating-bar-bg { background: #1a2535; border-radius: 2px; height: 3px; }
  .rating-bar-fill { height: 100%; border-radius: 2px; transition: width 0.8s cubic-bezier(0.4,0,0.2,1); }
  .bar-green { background: #3de89b; }
  .bar-blue { background: #4a8acc; }
  .bar-yellow { background: #f5c842; }
  .bar-purple { background: #9b6fe8; }

  /* Analysis box */
  .analysis-box {
    background: #0d1520; border: 1px solid #1a2535;
    border-radius: 8px; padding: 12px 14px; margin-top: 12px;
  }
  .analysis-title {
    font-size: 10px; font-family: 'Space Mono', monospace;
    color: #4a5568; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px;
  }
  .analysis-text { font-size: 13px; color: #8a9bb0; line-height: 1.6; }

  /* Result recorder */
  .record-result {
    display: flex; align-items: center; gap: 8px; margin-top: 12px;
    padding-top: 12px; border-top: 1px solid #1a2535;
  }
  .record-label { font-size: 11px; font-family: 'Space Mono', monospace; color: #4a5568; }
  .btn-winner {
    font-size: 11px; font-family: 'Space Mono', monospace;
    padding: 4px 10px; border-radius: 5px; cursor: pointer; border: 1px solid #1e2730;
    background: #111820; color: #6a8099; transition: all 0.15s;
  }
  .btn-winner:hover { border-color: #3de89b44; color: #3de89b; background: #0d2a1a; }

  /* Filters */
  .filters { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
  .filter-btn {
    background: #111820; border: 1px solid #1e2730; color: #6a8099;
    padding: 6px 14px; border-radius: 6px; font-size: 12px;
    font-family: 'Space Mono', monospace; cursor: pointer;
    transition: all 0.15s; letter-spacing: 0.3px;
  }
  .filter-btn:hover { border-color: #2a3a4a; color: #8a9bb0; }
  .filter-btn.active { background: #3de89b18; border-color: #3de89b44; color: #3de89b; }

  /* Empty & error */
  .empty-state {
    text-align: center; padding: 60px 20px;
    border: 1px dashed #1e2730; border-radius: 12px; color: #2a3a4a;
  }
  .empty-icon { font-size: 32px; margin-bottom: 12px; }
  .empty-title { font-family: 'Space Mono', monospace; font-size: 13px; margin-bottom: 6px; color: #3a4a5a; }
  .empty-sub { font-size: 13px; line-height: 1.6; }

  /* Skeleton */
  .skeleton-card {
    background: #111820; border: 1px solid #1e2730;
    border-radius: 12px; padding: 20px 24px;
    animation: shimmer 1.5s ease-in-out infinite;
  }
  @keyframes shimmer { 0%,100%{border-color:#1e2730} 50%{border-color:#2a3a4a} }
  .skel-line {
    background: #1a2535; border-radius: 4px; margin-bottom: 10px;
    animation: skfade 1.5s ease-in-out infinite;
  }
  @keyframes skfade { 0%,100%{opacity:0.4} 50%{opacity:0.8} }

  /* Accuracy panel */
  .accuracy-panel {
    background: #111820; border: 1px solid #1e2730;
    border-radius: 10px; padding: 20px 24px; margin-bottom: 24px;
  }
  .acc-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 14px; }
  .acc-item { text-align: center; }
  .acc-value { font-size: 22px; font-weight: 600; color: #e8f0fb; font-family: 'Space Mono', monospace; }
  .acc-label { font-size: 10px; color: #4a5568; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 3px; }

  @media (max-width: 600px) {
    .stats-row { grid-template-columns: repeat(2, 1fr); }
    .match-top { flex-direction: column; gap: 12px; }
    .score-block { flex-direction: row; min-width: auto; }
    .main { padding: 20px 16px; }
    .header { padding: 14px 16px; }
    .acc-grid { grid-template-columns: repeat(2, 1fr); }
  }
`;

const API = {
  async getMatches(minScore = 0) {
    const url = `${API_BASE}/api/matches/?days=7&min_score=${minScore || 0}&limit=50`;
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  async runAnalysis() {
    const r = await fetch(`${API_BASE}/api/analysis/run?days=7`, { method: "POST" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  async getAnalysisStatus() {
    const r = await fetch(`${API_BASE}/api/analysis/status`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  async getAccuracy() {
    const r = await fetch(`${API_BASE}/api/history/accuracy`);
    if (!r.ok) return null;
    return r.json();
  },
  async recordResult(matchId, winner) {
    const r = await fetch(`${API_BASE}/api/history/result`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ match_id: matchId, winner }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  async checkHealth() {
    try {
      const r = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
      return r.ok;
    } catch { return false; }
  },
};

function getScoreClass(score) {
  if (score == null) return "none";
  if (score >= 72) return "high";
  if (score >= 58) return "medium";
  return "low";
}

function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skel-line" style={{ height: 14, width: "30%" }} />
      <div className="skel-line" style={{ height: 22, width: "60%" }} />
      <div className="skel-line" style={{ height: 14, width: "80%", opacity: 0.5 }} />
    </div>
  );
}

function MatchCard({ match, onRecordResult }) {
  const pred = match.prediction;
  const score = pred?.score ?? null;
  const sc = getScoreClass(score);

  const scoreLabel = { high: "FORTE", medium: "MEDIO", low: "BASSO", none: "—" }[sc];

  return (
    <div className={`match-card ${sc}`}>
      <div className="match-top">
        <div style={{ flex: 1 }}>
          <div className="match-meta">
            <span className="badge badge-neutral">{match.tournament}</span>
            <span className={`badge badge-${match.surface}`}>{match.surface.toUpperCase()}</span>
            {match.round && <span className="badge badge-neutral">{match.round}</span>}
            <span className="badge badge-neutral">{match.match_date}</span>
          </div>

          <div className="players">
            <div className="player">
              <span className="player-name favorite">{match.favorite || match.player1}</span>
              <span className="player-rank">ATP #{match.fav_rank ?? "?"}</span>
            </div>
            <span className="vs-sep">vs</span>
            <div className="player">
              <span className="player-name">{match.underdog || match.player2}</span>
              <span className="player-rank">ATP #{match.und_rank ?? "?"}</span>
            </div>
          </div>

          <div className="tags">
            {match.rank_gap != null && <span className="tag">Gap ranking: {match.rank_gap}</span>}
            {match.h2h && <span className="tag">H2H: {match.h2h}</span>}
          </div>
        </div>

        <div className="score-block">
          <div className={`score-circle ${sc}`}>{score ?? "—"}</div>
          <span className={`score-label ${sc}`}>{scoreLabel}</span>
        </div>
      </div>

      {pred && (
        <>
          <div className="rating-bars">
            <div className="rating-item">
              <span className="rating-label">RANKING GAP</span>
              <div className="rating-bar-bg">
                <div className="rating-bar-fill bar-green" style={{ width: `${pred.factor_ranking}%` }} />
              </div>
            </div>
            <div className="rating-item">
              <span className="rating-label">SUPERFICIE</span>
              <div className="rating-bar-bg">
                <div className="rating-bar-fill bar-blue" style={{ width: `${pred.factor_surface}%` }} />
              </div>
            </div>
            <div className="rating-item">
              <span className="rating-label">FORMA RECENTE</span>
              <div className="rating-bar-bg">
                <div className="rating-bar-fill bar-yellow" style={{ width: `${pred.factor_form}%` }} />
              </div>
            </div>
            <div className="rating-item">
              <span className="rating-label">H2H + RISCHIO</span>
              <div className="rating-bar-bg">
                <div className="rating-bar-fill bar-purple" style={{ width: `${pred.factor_h2h}%` }} />
              </div>
            </div>
          </div>

          {pred.analysis_text && (
            <div className="analysis-box">
              <div className="analysis-title">Analisi AI · {pred.model_version}</div>
              <div className="analysis-text">{pred.analysis_text}</div>
            </div>
          )}

          <div className="record-result">
            <span className="record-label">REGISTRA RISULTATO:</span>
            <button className="btn-winner" onClick={() => onRecordResult(match.id, match.favorite || match.player1)}>
              {match.favorite || match.player1} vince
            </button>
            <button className="btn-winner" onClick={() => onRecordResult(match.id, match.underdog || match.player2)}>
              {match.underdog || match.player2} vince
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default function App() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState({ pct: 0, done: 0, total: 0 });
  const [filter, setFilter] = useState("ALL");
  const [accuracy, setAccuracy] = useState(null);
  const [online, setOnline] = useState(null);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  // Controlla se il backend è online
  useEffect(() => {
    API.checkHealth().then(setOnline);
  }, []);

  // Carica match e accuratezza all'avvio
  useEffect(() => {
    if (online === false) return;
    loadMatches();
    API.getAccuracy().then(setAccuracy).catch(() => {});
  }, [online]);

  async function loadMatches(minScore = 0) {
    setLoading(true);
    setError(null);
    try {
      const data = await API.getMatches(minScore);
      setMatches(data);
    } catch (e) {
      setError("Impossibile connettersi al backend. Assicurati che sia avviato su localhost:8000.");
    } finally {
      setLoading(false);
    }
  }

  async function startAnalysis() {
    setAnalyzing(true);
    setProgress({ pct: 0, done: 0, total: 0 });
    try {
      await API.runAnalysis();
      // Poll status ogni 2 secondi
      pollRef.current = setInterval(async () => {
        const status = await API.getAnalysisStatus();
        setProgress({ pct: status.pct, done: status.progress, total: status.total });
        if (status.done || !status.running) {
          clearInterval(pollRef.current);
          setAnalyzing(false);
          await loadMatches();
          API.getAccuracy().then(setAccuracy).catch(() => {});
        }
      }, 2000);
    } catch (e) {
      setAnalyzing(false);
      setError("Errore nell'avviare l'analisi: " + e.message);
    }
  }

  async function handleRecordResult(matchId, winner) {
    try {
      await API.recordResult(matchId, winner);
      API.getAccuracy().then(setAccuracy);
      // Feedback visivo semplice
      setMatches(prev => prev.map(m => m.id === matchId
        ? { ...m, _resultRecorded: winner }
        : m
      ));
    } catch (e) {
      console.error("Errore registrazione risultato:", e);
    }
  }

  const scored    = matches.filter(m => m.prediction != null);
  const highConf  = scored.filter(m => m.prediction.score >= 72).length;
  const avgScore  = scored.length > 0
    ? Math.round(scored.reduce((s, m) => s + m.prediction.score, 0) / scored.length)
    : 0;

  const filtered = matches.filter(m => {
    if (!m.prediction) return filter === "ALL";
    const s = m.prediction.score;
    if (filter === "HIGH")   return s >= 72;
    if (filter === "MEDIUM") return s >= 58 && s < 72;
    if (filter === "LOW")    return s < 58;
    return true;
  });

  const today = new Date().toLocaleDateString("it-IT", {
    weekday: "long", day: "numeric", month: "long", year: "numeric"
  });

  return (
    <>
      <style>{FONTS + CSS}</style>
      <div className="app">
        <header className="header">
          <div className="logo">
            <div className="logo-dot" />
            TENNIS·SCOUT
          </div>
          <div className="header-right">
            <span className="live-badge">AI POWERED</span>
            <span>
              <span className={`status-dot ${online === false ? "offline" : ""}`} />
              {online === null ? "…" : online ? "backend online" : "backend offline"}
            </span>
            <span>{today}</span>
          </div>
        </header>

        <main className="main">
          {/* Stats */}
          <div className="stats-row">
            <div className="stat-card accent">
              <div className="stat-label">Match analizzati</div>
              <div className="stat-value">{scored.length}</div>
              <div className="stat-sub">di {matches.length} trovati</div>
            </div>
            <div className="stat-card warn">
              <div className="stat-label">Score medio</div>
              <div className="stat-value">{scored.length > 0 ? avgScore : "—"}</div>
              <div className="stat-sub">confidenza AI / 100</div>
            </div>
            <div className="stat-card accent">
              <div className="stat-label">Alta confidenza</div>
              <div className="stat-value">{highConf}</div>
              <div className="stat-sub">score ≥ 72</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Accuratezza storica</div>
              <div className="stat-value" style={{ color: "#3de89b", fontSize: accuracy ? 26 : 18 }}>
                {accuracy?.accuracy_pct != null ? `${accuracy.accuracy_pct}%` : "—"}
              </div>
              <div className="stat-sub">
                {accuracy ? `${accuracy.correct}/${accuracy.total_results} corrette` : "nessun dato"}
              </div>
            </div>
          </div>

          {/* Accuracy panel */}
          {accuracy && accuracy.total_results > 0 && (
            <div className="accuracy-panel">
              <div className="section-title">Accuratezza predizioni — storico</div>
              <div className="acc-grid">
                <div className="acc-item">
                  <div className="acc-value" style={{ color: "#3de89b" }}>{accuracy.accuracy_pct}%</div>
                  <div className="acc-label">Accuratezza totale</div>
                </div>
                <div className="acc-item">
                  <div className="acc-value" style={{ color: "#f5c842" }}>{accuracy.high_confidence_accuracy}%</div>
                  <div className="acc-label">Alta conf. (≥72)</div>
                </div>
                <div className="acc-item">
                  <div className="acc-value">{accuracy.avg_score}</div>
                  <div className="acc-label">Score medio</div>
                </div>
              </div>
            </div>
          )}

          {/* Section header */}
          <div className="section-header">
            <span className="section-title">
              Partite settimana corrente — {matches.length} match
            </span>
            <div className="btn-row">
              <button className="btn-secondary" onClick={() => loadMatches()} disabled={loading}>
                ↻ Aggiorna
              </button>
              <button
                className="btn-primary"
                onClick={startAnalysis}
                disabled={analyzing || loading || online === false}
              >
                {analyzing ? (
                  <><div className="spinner" /> Analisi in corso... {progress.pct}%</>
                ) : (
                  <><span>⚡</span> {scored.length > 0 ? "Rianalizza" : "Analizza settimana"}</>
                )}
              </button>
            </div>
          </div>

          {/* Progress bar */}
          {analyzing && (
            <div className="progress-bar-wrap">
              <div className="progress-bar-label">
                <span>Scraping + analisi AI in corso...</span>
                <span>{progress.done}/{progress.total} match</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${progress.pct}%` }} />
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div style={{
              background: "#2a1010", border: "1px solid #e85555",
              borderRadius: 10, padding: "14px 20px",
              fontSize: 13, color: "#e89999", marginBottom: 20
            }}>
              ⚠ {error}
            </div>
          )}

          {/* Filters */}
          {scored.length > 0 && (
            <div className="filters">
              <span style={{ fontSize: 11, fontFamily: "'Space Mono',monospace", color: "#4a5568", marginRight: 4, letterSpacing: "0.8px" }}>FILTRA:</span>
              {[
                { key: "ALL",    label: "Tutti" },
                { key: "HIGH",   label: "Alta conf. ≥72" },
                { key: "MEDIUM", label: "Media 58–72" },
                { key: "LOW",    label: "Bassa <58" },
              ].map(f => (
                <button key={f.key} className={`filter-btn ${filter === f.key ? "active" : ""}`} onClick={() => setFilter(f.key)}>
                  {f.label}
                </button>
              ))}
            </div>
          )}

          {/* Match list */}
          <div className="matches-grid">
            {loading ? (
              [1,2,3].map(i => <SkeletonCard key={i} />)
            ) : error ? null : matches.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🎾</div>
                <div className="empty-title">
                  {online === false ? "BACKEND OFFLINE" : "NESSUN MATCH"}
                </div>
                <div className="empty-sub">
                  {online === false
                    ? "Avvia il backend con:\ncd backend && uvicorn main:app --reload"
                    : <>Premi <strong style={{ color: "#3de89b" }}>Analizza settimana</strong> per avviare lo scraping e l'analisi AI.</>
                  }
                </div>
              </div>
            ) : (
              filtered.map(match => (
                <MatchCard
                  key={match.id}
                  match={match}
                  onRecordResult={handleRecordResult}
                />
              ))
            )}
          </div>

          {scored.length > 0 && (
            <div style={{
              marginTop: 24, padding: "14px 20px",
              background: "#0d1520", border: "1px solid #1a2535",
              borderRadius: 10, fontSize: 12, color: "#4a5568",
              fontFamily: "'Space Mono',monospace", lineHeight: 1.7
            }}>
              ⚠ Strumento a scopo informativo e di studio. Le previsioni AI non garantiscono risultati. Gioca responsabilmente.
            </div>
          )}
        </main>
      </div>
    </>
  );
}
