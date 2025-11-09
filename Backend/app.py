from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from pathlib import Path
import json
from datetime import datetime, timezone

# === Local modules ===
from Backend.normalize import Normalizer
from Backend.retrieval import InteractionIndex

# ---------- Config ----------
BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INTERACTIONS_CSV = DATA_DIR / "interactions_processed.csv"
SYNONYMS_CSV = DATA_DIR / "synonyms_identity.csv"
VISITS_JSON = DATA_DIR / "visits.json"

# ---------- App ----------
app = FastAPI(title="DDI Checker API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ---------- Models ----------
class CheckRequest(BaseModel):
    new_drug: str
    current: List[str]
    patient_name: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    doctor_name: str | None = None

class Alert(BaseModel):
    pair: List[str]
    severity: str
    severity_score: float
    description: str
    management: str | None = None
    proof: Dict[str, Any] | None = None
    sources: List[Dict[str, Any]] = []

# ---------- Services ----------
norm = Normalizer(str(SYNONYMS_CSV))
index = InteractionIndex(str(INTERACTIONS_CSV))

def _now_iso() -> str:
    # UTC ISO timestamp with seconds
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _load_visits() -> list:
    if VISITS_JSON.exists():
        try:
            return json.loads(VISITS_JSON.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def _save_visits(rows: list):
    # keep file from growing unbounded
    rows = rows[-500:]  # retain latest 500
    VISITS_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Endpoints ----------
@app.get("/")
def root():
    return {"ok": True, "msg": "DDI API up"}

@app.get("/autocomplete")
def autocomplete(query: str = Query(..., min_length=1), limit: int = 8):
    sugs = norm.suggestions(query, limit=limit)
    if not sugs:
        # do not error—return empty list, but 200
        return {"suggestions": []}
    return {"suggestions": sugs[:limit]}

@app.post("/check")
def check(req: CheckRequest):
    new_can = norm.canonical(req.new_drug)
    if not new_can:
        raise HTTPException(status_code=400, detail=f"Unknown new_drug: {req.new_drug}")

    pairs = []
    for s in req.current:
        can = norm.canonical(s)
        if not can:
            pairs.append({"pair": [new_can, s.strip().lower()], "not_found": True})
        else:
            pairs.append({"pair": [new_can, can], "not_found": False})

    alerts: List[Dict[str, Any]] = []
    misses: List[Dict[str, Any]] = []

    for p in pairs:
        a, b = p["pair"]
        rows = index.lookup(a, b)
        if not rows:
            misses.append({"pair": [a, b]})
            continue
        agg = index.aggregate(rows)
        alerts.append({
            "pair": [a, b],
            "severity": agg["severity"],
            "severity_score": agg["severity_score"],
            "description": agg["description"],
            "management": agg.get("management", ""),
            "proof": {"canonical_pair": [a, b], "row_ids": agg["row_ids"], "policy": "max_severity_v0+cont_score_v1"},
            "sources": agg["sources"],
        })

    # persist visit with timestamp
    visit_row = {
        "created_at": _now_iso(),                 # <-- DATE+TIME stored
        "patient_name": req.patient_name or "",
        "age": req.age,
        "doctor_name": req.doctor_name or "",
        "new_drug": new_can,
        "current": [norm.canonical(x) or x.strip().lower() for x in req.current],
        "summary": [{"pair": a["pair"], "severity": a["severity"], "score": a["severity_score"]} for a in alerts],
    }
    visits = _load_visits()
    visits.append(visit_row)
    _save_visits(visits)

    return {"alerts": alerts, "not_found": misses}

@app.get("/visits")
def visits(limit: int = 10):
    rows = _load_visits()
    # newest first
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return {"visits": rows[:max(1, min(limit, 100))]}
