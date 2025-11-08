import pandas as pd
from rapidfuzz import process

class Normalizer:
    def __init__(self, synonyms_csv: str, threshold: int = 90):
        s = pd.read_csv(synonyms_csv)
        self.map = {}
        for _, r in s.iterrows():
            self.map[str(r["synonym"]).strip().lower()] = str(r["canonical"]).strip().lower()
        self.known = sorted(set(self.map.values()))
        self.threshold = threshold

    def normalize(self, name: str):
        q = name.strip().lower()
        if q in self.map:
            return self.map[q], {"method":"exact","score":100,"input":name}
        cand, score, _ = process.extractOne(q, self.known)
        if score >= self.threshold:
            return cand, {"method":"fuzzy","score":int(score),"input":name}
        return q, {"method":"fallback","score":0,"input":name}
