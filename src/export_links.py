"""Build the published linked dataset from candidates, the rule baseline, the Wikidata join and the gold labels.

road_aadr_links.csv   one row per linked ROAD locality x AADR site pair
road_aadr_samples.csv the AADR individuals behind each link (IDs, dates, publication)
A pair is published only if both sites share a Wikidata item. The name-and-distance rule is not used to
select links (it was tuned on the gold set and is only about 0.87 precise); the evidence column records
whether the rule also agreed.
"""
import pandas as pd

from candidates import load_aadr

RULE_NAME, RULE_KM = 95, 10
KEY = ["road_locality", "aadr_locality", "aadr_lat", "aadr_lon"]


def keyed(df):
    df = df.copy()
    df[["aadr_lat", "aadr_lon"]] = df[["aadr_lat", "aadr_lon"]].round(6)
    return df


c = keyed(pd.read_csv("data/interim/candidates.csv"))
c = c[c.distance_km <= 25]
c["link_rule"] = (c.name_score >= RULE_NAME) & (c.distance_km <= RULE_KM)

wd = keyed(pd.read_csv("data/out/wikidata_links.csv"))[KEY + ["road_qid"]].rename(columns={"road_qid": "wikidata_qid"})
c = c.merge(wd, on=KEY, how="left")
c["link_wikidata"] = c.wikidata_qid.notna()

gold = pd.read_csv("data/gold/to_label.csv")
gold = keyed(gold.rename(columns={"label": "gold_label"}))[KEY + ["gold_label"]]
c = c.merge(gold, on=KEY, how="left")

links = c[c.link_wikidata].copy()
links["evidence"] = links.apply(
    lambda r: "rule+wikidata" if r.link_rule and r.link_wikidata else "rule" if r.link_rule else "wikidata", axis=1)
cols = ["road_locality", "road_country", "road_lat", "road_lon", "road_age_min", "road_age_max",
        "aadr_locality", "aadr_country", "aadr_lat", "aadr_lon", "aadr_n_samples", "distance_km", "name_score",
        "evidence", "wikidata_qid", "gold_label"]
links[cols].sort_values(["road_locality", "distance_km"]).to_csv("data/out/road_aadr_links.csv", index=False)

aadr = keyed(load_aadr().rename(columns={"locality": "aadr_locality", "lat": "aadr_lat", "lon": "aadr_lon"}))
samples = links[["road_locality", "aadr_locality", "aadr_lat", "aadr_lon"]].merge(aadr, on=["aadr_locality", "aadr_lat", "aadr_lon"])
samples = samples.drop(columns=["country"]).sort_values(["road_locality", "date_bp"])
samples.to_csv("data/out/road_aadr_samples.csv", index=False)

print(f"{len(links)} linked pairs ({links.road_locality.nunique()} ROAD sites, {links.aadr_locality.nunique()} AADR sites), {len(samples)} genomes")
print(links.evidence.value_counts().to_string())
print("gold labels among linked pairs:", links.gold_label.value_counts(dropna=False).to_dict())
