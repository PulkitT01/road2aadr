"""Sample ~100 candidate pairs (<=25 km), stratified by distance x name score, for hand labelling.

Writes a shuffled sheet (distance shown, name score hidden) and a features file keyed by pair_id for later joins.
"""
import pandas as pd

N, SEED, MAX_KM = 100, 7, 25

c = pd.read_csv("data/interim/candidates.csv")
c = c[c.distance_km <= MAX_KM].reset_index(drop=True)
c["name_band"] = pd.cut(c.name_score, [-1, 50, 85, 101], labels=["low", "mid", "high"])
c["dist_band"] = pd.cut(c.distance_km, [-1, 5, MAX_KM], labels=["<=5km", ">5km"])

cap = N // 6  # equal share per stratum, topped up from leftovers
picked = pd.concat([g.sample(min(len(g), cap), random_state=SEED)
                    for _, g in c.groupby(["name_band", "dist_band"], observed=True)])
extra = c.drop(picked.index).sample(N - len(picked), random_state=SEED)
gold = pd.concat([picked, extra]).sample(frac=1, random_state=SEED).reset_index(drop=True)
gold.insert(0, "pair_id", [f"P{i:03d}" for i in range(1, len(gold) + 1)])

gold.drop(columns=["name_band", "dist_band"]).to_csv("data/gold/pair_features.csv", index=False)
show = ["pair_id", "road_locality", "road_country", "road_lat", "road_lon", "road_age_min", "road_age_max",
        "aadr_locality", "aadr_country", "aadr_lat", "aadr_lon", "distance_km", "aadr_n_samples", "aadr_date_min", "aadr_date_max"]
sheet = gold[show].copy()
sheet["label"] = ""  # same / different / unsure
sheet["notes"] = ""
sheet.to_csv("data/gold/to_label.csv", index=False)
print(f"{len(sheet)} pairs from {len(c)} candidates")
print(gold.groupby(["name_band", "dist_band"], observed=True).size())
