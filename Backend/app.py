from fastapi import FastAPI
from Backend.schema import CheckRequest, Alert
from Backend.normalize import Normalizer
from Backend.retrieval import InteractionIndex
from pathlib import Path
import hashlib

# -----------------------------
# Initialize FastAPI app
# -----------------------------
app = FastAPI(title="Drug–Drug Interaction Checker")

# -----------------------------
# Define data paths
# -----------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SYN_PATH = DATA_DIR / "synonyms_identity.csv"
INT_PATH = DATA_DIR / "interactions_processed.csv"

# Check files exist before loading
assert SYN_PATH.exists(), f"Missing file: {SYN_PATH}"
assert INT_PATH.exists(), f"Missing file: {INT_PATH}"

# -----------------------------
# Initialize normalization + index
# -----------------------------
norm = Normalizer(str(SYN_PATH))
index = InteractionIndex(str(INT_PATH))


# -----------------------------
# Root route for quick check
# -----------------------------
@app.get("/")
def root():
    return {"message": "DDI Checker API running!"}

def alert_id(a, b, sev, sev_score):
    s = f"{a}|{b}|{sev}|{sev_score}|heuristic_v0_2025-11-03"
    return hashlib.sha1(s.encode()).hexdigest()[:12]

@app.post("/check")
def check(req: CheckRequest):
    new_can, nlog_new = norm.normalize(req.new_drug)
    result = []
    logs = {"new": nlog_new, "current": []}
    for c in req.current:
        can, nlog = norm.normalize(c)
        logs["current"].append(nlog)
        rows = index.lookup(new_can, can)
        agg = index.aggregate(rows)
        if agg:
            aid = alert_id(new_can, can, agg["severity"], agg["severity_score"])
            result.append({
                "id": aid,
                "pair": [new_can, can],
                "severity": agg["severity"],
                "severity_score": agg["severity_score"],
                "description": agg["description"],
                "management": agg["management"],
                "sources": agg["sources"],
                "proof": {"canonical_pair":[new_can, can],"row_ids":agg["row_ids"],"policy":"max_severity_v0+cont_score_v1"}
            })
    order = {"Contraindicated":3, "Major":2, "Moderate":1, "Minor":0}
    result.sort(key=lambda x: (order.get(x["severity"], -1), x["severity_score"]), reverse=True)
    return {"alerts": result, "normalization": logs}