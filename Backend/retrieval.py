import pandas as pd
from collections import defaultdict
from Backend.scoring import bucket_norm, continuous_severity_score
from fuzzywuzzy import process  # For fuzzy matching

SEV_RANK = {"Contraindicated": 3, "Major": 2, "Moderate": 1, "Minor": 0}

class InteractionIndex:
    def __init__(self, csv_path: str, synonyms_csv: str = "Backend/data/synonyms_identity.csv"):
        # Load the main data
        df = pd.read_csv(csv_path)
        df["drug_a"] = df["drug_a"].astype(str).str.strip().str.lower()
        df["drug_b"] = df["drug_b"].astype(str).str.strip().str.lower()
        df["description"] = df["description"].astype(str)

        if "matched_pattern" not in df.columns:
            df["matched_pattern"] = ""

        # Mapping severity to normalized values
        df["severity_norm"] = df["severity"].map(bucket_norm)
        df["severity_score"] = [
            continuous_severity_score(b, d, m)
            for b, d, m in zip(df["severity_norm"], df["description"], df["matched_pattern"])
        ]

        # Store rows and initialize index
        self.rows = df
        self.idx = defaultdict(lambda: defaultdict(list))
        for i, r in df.iterrows():
            a, b = r["drug_a"], r["drug_b"]
            self.idx[a][b].append(i)
            self.idx[b][a].append(i)

        # Load synonyms for fuzzy matching
        self.synonyms_df = pd.read_csv(synonyms_csv)
    
    # Lookup function for exact drug pairs
    def lookup(self, a: str, b: str):
        a = a.strip().lower()
        b = b.strip().lower()
        return self.idx.get(a, {}).get(b, [])

    # Fuzzy matching function to find closest drug name matches
    def fuzzy_match(self, query: str) -> str:
        query = query.strip().lower()
        matches = process.extract(query, self.synonyms_df["alias"].tolist(), limit=3, scorer=fuzz.ratio)
        best_match = matches[0][0] if matches[0][1] > 70 else query
        return best_match

    # Aggregate data for a given set of row IDs (best severity and severity score)
    def aggregate(self, row_ids):
        if not row_ids:
            return None
        rows = self.rows.loc[row_ids].copy()
        rows["sev_rank"] = rows["severity_norm"].map(lambda x: SEV_RANK.get(x, 1))
        rows = rows.sort_values(["sev_rank", "severity_score"], ascending=[False, False])
        best = rows.iloc[0]

        sources = [{"source_id": str(x["source_id"]) if "source_id" in rows.columns else "DBI",
                    "last_reviewed": str(x["last_reviewed"]) if "last_reviewed" in rows.columns else ""}
                   for _, x in rows.iterrows()]

        return {
            "severity": str(best["severity_norm"]),
            "severity_score": float(best["severity_score"]),
            "description": str(best["description"]),
            "management": str(best["management"]) if "management" in rows.columns else "",
            "sources": sources,
            "row_ids": list(map(int, row_ids))
        }
    
    # Function to search and return results based on fuzzy matching
    def search_drug_pair(self, query_a: str, query_b: str):
        # Use fuzzy matching for drug names
        matched_a = self.fuzzy_match(query_a)
        matched_b = self.fuzzy_match(query_b)
        
        # Find rows based on the matched drug names
        row_ids = self.lookup(matched_a, matched_b)
        
        # Aggregate and return results for the best match
        return self.aggregate(row_ids) if row_ids else None
