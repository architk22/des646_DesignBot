import pandas as pd
from collections import defaultdict
from Backend.scoring import bucket_norm, continuous_severity_score

SEV_RANK = {"Contraindicated":3,"Major":2,"Moderate":1,"Minor":0}

class InteractionIndex:
    def __init__(self, csv_path: str):
        df = pd.read_csv(csv_path)
        df["drug_a"] = df["drug_a"].astype(str).str.strip().str.lower()
        df["drug_b"] = df["drug_b"].astype(str).str.strip().str.lower()
        df["description"] = df["description"].astype(str)
        if "matched_pattern" not in df.columns:
            df["matched_pattern"] = ""

        df["severity_norm"] = df["severity"].map(bucket_norm)
        df["severity_score"] = [
            continuous_severity_score(b, d, m)
            for b, d, m in zip(df["severity_norm"], df["description"], df["matched_pattern"])
        ]

        self.rows = df
        self.idx = defaultdict(lambda: defaultdict(list))
        for i, r in df.iterrows():
            a, b = r["drug_a"], r["drug_b"]
            self.idx[a][b].append(i); self.idx[b][a].append(i)

    def lookup(self, a: str, b: str): return self.idx.get(a, {}).get(b, [])

    def aggregate(self, row_ids):
        if not row_ids: return None
        rows = self.rows.loc[row_ids].copy()
        rows["sev_rank"] = rows["severity_norm"].map(lambda x: SEV_RANK.get(x,1))
        rows = rows.sort_values(["sev_rank","severity_score"], ascending=[False, False])
        best = rows.iloc[0]
        sources = [{"source_id": str(x["source_id"]) if "source_id" in rows.columns else "DBI",
                    "last_reviewed": str(x["last_reviewed"]) if "last_reviewed" in rows.columns else ""} for _, x in rows.iterrows()]
        return {
            "severity": str(best["severity_norm"]),
            "severity_score": float(best["severity_score"]),
            "description": str(best["description"]),
            "management": str(best["management"]) if "management" in rows.columns else "",
            "sources": sources,
            "row_ids": list(map(int, row_ids))
        }
