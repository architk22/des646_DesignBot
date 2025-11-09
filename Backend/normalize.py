# Backend/normalize.py
import pandas as pd
from typing import List
import os

# --- Speedy & robust fuzzy matching ---
try:
    # Prefer rapidfuzz (faster, no Levenshtein warning)
    from rapidfuzz import process, fuzz
    _USE_RF = True
except Exception:
    # Fallback to fuzzywuzzy if rapidfuzz not installed
    try:
        from fuzzywuzzy import process, fuzz  # type: ignore
        _USE_RF = False
    except Exception:
        process = None
        fuzz = None
        _USE_RF = False

def _pick_col(cols, candidates: List[str]):
    """Return the first matching column from candidates (case-insensitive)."""
    cl = {c.lower(): c for c in cols}
    for name in candidates:
        if name.lower() in cl:
            return cl[name.lower()]
    return None

class Normalizer:
    def __init__(self, synonyms_csv: str):
        if not os.path.exists(synonyms_csv):
            raise FileNotFoundError(f"synonyms file not found: {synonyms_csv}")

        # Try to read with headers; if fails or headers wrong, read without header
        df = pd.read_csv(synonyms_csv, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]

        # Try to detect alias/canonical columns by common names
        alias_col = _pick_col(df.columns, ["alias","synonym","name","drug","term","variant"])
        canon_col = _pick_col(df.columns, ["canonical","preferred","standard","root","normalized","map_to","canonical_name"])

        if alias_col is None or canon_col is None:
            # Maybe file has no headers; re-read as no-header and take first two columns
            df2 = pd.read_csv(synonyms_csv, dtype=str, header=None)
            if df2.shape[1] < 2:
                raise ValueError("synonyms CSV must have at least 2 columns (alias, canonical).")
            df2 = df2.iloc[:, :2].copy()
            df2.columns = ["alias","canonical"]
            df = df2
            alias_col, canon_col = "alias", "canonical"
        else:
            # Standardize to alias/canonical
            df = df[[alias_col, canon_col]].copy()
            df.columns = ["alias","canonical"]

        # Clean
        df["alias"] = df["alias"].astype(str).str.strip().str.lower()
        df["canonical"] = df["canonical"].astype(str).str.strip().str.lower()
        df = df.dropna(subset=["alias","canonical"])
        df = df[df["alias"] != ""]
        df = df[df["canonical"] != ""]

        # Keep a unique alias->canonical mapping (last one wins)
        self.alias2can = dict(zip(df["alias"], df["canonical"]))

        # Build suggestion vocabulary (unique aliases)
        self._aliases = sorted(set(self.alias2can.keys()))

        # If no fuzzy libs, we’ll fall back to substring filter inside suggestions()
        self._has_fuzzy = process is not None and fuzz is not None

    def canonical(self, name: str) -> str:
        if not isinstance(name, str):
            return ""
        k = name.strip().lower()
        return self.alias2can.get(k, k)

    def suggestions(self, query: str, limit: int = 8, threshold: int = 70) -> List[str]:
        q = (query or "").strip().lower()
        if not q:
            return []
        if self._has_fuzzy:
            matches = process.extract(q, self._aliases, scorer=fuzz.ratio, limit=limit)
            # rapidfuzz returns list of (choice, score, idx); fuzzywuzzy returns (choice, score)
            out = []
            for m in matches:
                choice = m[0]
                score = m[1]
                if score >= threshold:
                    out.append(choice)
            return out
        # Fallback: simple startswith then substring
        starts = [a for a in self._aliases if a.startswith(q)]
        if starts:
            return starts[:limit]
        subs = [a for a in self._aliases if q in a]
        return subs[:limit]

    def hash_pair(self, a: str, b: str) -> str:
        a = (a or "").strip().lower()
        b = (b or "").strip().lower()
        return "::".join(sorted([a, b]))
