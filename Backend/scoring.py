import re, math

ANCHOR = {"Minor":0.25, "Moderate":0.60, "Major":0.85, "Contraindicated":1.00}
BANDS  = {"Minor":(0.10,0.40), "Moderate":(0.40,0.80), "Major":(0.70,0.95), "Contraindicated":(0.95,1.00)}

RX_OUTCOME = re.compile(r"(bleeding|hemorrhag|haemorrhag|inr\s*(increase|elevat)|torsade|qt\s*prolong|arrhythmia|serotonin\s+syndrome|nms|rhabdomyolysis|hyperkalemi|anaphylaxis)", re.I)
RX_ACTION  = re.compile(r"(avoid|do\s*not\s*use|contraindicat|boxed\s*warning)", re.I)
RX_NEG     = re.compile(r"(does\s+not\s+(increase|decrease|affect)|no\s+clinically\s+significant)", re.I)

RX_CYP_STRONG   = re.compile(r"(strong|potent).{0,8}(inhibit|induc).{0,12}(cyp|p-?gp|bcrp|oatp|ugt)", re.I)
RX_CYP_MODERATE = re.compile(r"(moderate).{0,8}(inhibit|induc).{0,12}(cyp|p-?gp|bcrp|oatp|ugt)", re.I)
RX_CYP_WEAK     = re.compile(r"(weak|mild).{0,8}(inhibit|induc).{0,12}(cyp|p-?gp|bcrp|oatp|ugt)", re.I)

RX_PK_INC = re.compile(r"(serum\s+concentration|exposure|auc|cmax).{0,6}(increase|raised|elevat|higher|↑)", re.I)
RX_PK_DEC = re.compile(r"(serum\s+concentration|exposure|auc|cmax).{0,6}(decrease|lower|reduc|↓)", re.I)

RX_MAGN = re.compile(r"(\b\d+(\.\d+)?-fold\b|\b\d{1,3}%\b|\bmarked(ly)?\b|\bsignificant(ly)?\b|\bsubstantial(ly)?\b)", re.I)

def bucket_norm(x:str)->str:
    x=str(x).strip().lower()
    if x.startswith("contra"): return "Contraindicated"
    if x.startswith("maj"): return "Major"
    if x.startswith("mod"): return "Moderate"
    if x.startswith("min"): return "Minor"
    return "Moderate"

def _mech_strength(txt:str)->float:
    if RX_CYP_STRONG.search(txt): return 1.0
    if RX_CYP_MODERATE.search(txt): return 0.6
    if RX_CYP_WEAK.search(txt): return 0.3
    return 0.0

def _pk_change(txt:str)->float:
    inc = 1.0 if RX_PK_INC.search(txt) else 0.0
    dec = 1.0 if RX_PK_DEC.search(txt) else 0.0
    return inc*0.8 + dec*0.5

def _magnitude(txt:str)->float:
    hits = len(RX_MAGN.findall(txt))
    return min(1.0, math.log1p(hits)/math.log(1+3))

def clamp_band(bucket:str, s:float)->float:
    lo, hi = BANDS[bucket];  return max(lo, min(hi, s))

def continuous_severity_score(bucket:str, description:str, matched_pattern:str=""):
    b = ANCHOR[bucket]
    txt = f"{description or ''} {matched_pattern or ''}"

    outcome = 1.0 if RX_OUTCOME.search(txt) else 0.0
    action  = 1.0 if RX_ACTION.search(txt)   else 0.0
    neg     = 1.0 if RX_NEG.search(txt)      else 0.0

    mech  = _mech_strength(txt)
    pkchg = _pk_change(txt)
    magn  = _magnitude(txt)

    matches = (1 if outcome else 0) + (1 if action else 0) + (1 if mech>0 else 0) + (1 if pkchg>0 else 0) + (1 if magn>0 else 0)

    w_outcome, w_action, w_mech, w_pk, w_magn, w_count, w_neg = 0.12, 0.08, 0.08, 0.08, 0.05, 0.03, 0.10
    s_raw = b + w_outcome*outcome + w_action*action + w_mech*mech + w_pk*pkchg + w_magn*magn + w_count*math.log1p(matches) - w_neg*neg
    return round(clamp_band(bucket, s_raw), 2)
