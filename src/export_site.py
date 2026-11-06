"""Build docs/data/sites.json for the viewer: one entry per linked ROAD site with layers and AADR genomes.

Pairs the gold set labelled "different" (known wrong links) are left out of the viewer, not out of the CSVs.
"""
import json

import numpy as np
import pandas as pd

links = pd.read_csv("data/out/road_aadr_links.csv")
samples = pd.read_csv("data/out/road_aadr_samples.csv")
asm = pd.read_csv("data/raw/assemblages.csv")

links = links[links.gold_label != "different"]
samples = samples.merge(links[["road_locality", "aadr_locality", "aadr_lat", "aadr_lon"]].round(6),
                        on=["road_locality", "aadr_locality", "aadr_lat", "aadr_lon"])

asm["label"] = asm.archlayer.fillna(asm.geolayer).fillna(asm.assemblage_name)
layer_cols = ["label", "age_min", "age_max", "cultural_period"]


def clean(v):
    if isinstance(v, (float, np.floating)) and np.isnan(v):
        return None
    return v.item() if isinstance(v, np.generic) else v


sites = []
for name, g in links.groupby("road_locality"):
    layers = (asm[asm.locality_id == name].dropna(subset=["age_min", "age_max"])
              .groupby(layer_cols, dropna=False).size().reset_index(name="n_assemblages")
              .sort_values("age_max"))
    s = samples[samples.road_locality == name]
    first = g.iloc[0]
    sites.append({
        "name": name, "country": first.road_country, "lat": first.road_lat, "lon": first.road_lon,
        "links": [{k: clean(r[k]) for k in ["aadr_locality", "distance_km", "name_score", "evidence", "wikidata_qid"]}
                  for _, r in g.iterrows()],
        "layers": [{k: clean(r[k]) for k in layer_cols + ["n_assemblages"]} for _, r in layers.iterrows()],
        "genomes": [{"id": clean(r.genetic_id), "date_bp": clean(r.date_bp), "sd": clean(r.date_sd),
                     "pub": clean(r.publication), "doi": clean(r.doi), "aadr_locality": r.aadr_locality}
                    for _, r in s.iterrows()],
    })

with open("docs/data/sites.json", "w") as f:
    json.dump(sites, f, separators=(",", ":"))
print(f"{len(sites)} sites, {sum(len(s['layers']) for s in sites)} layers, {sum(len(s['genomes']) for s in sites)} genomes")
print("sites with no dated layers:", [s["name"] for s in sites if not s["layers"]])
