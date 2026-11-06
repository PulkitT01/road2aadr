"""Cross-check the gold labels against Wikidata IDs (QIDs) found by src/wikidata.py.

Same QID on both sides supports "same"; two different QIDs support "different"; a missing QID on either
side says nothing. Disagreements are listed for a human to look at. This is a partial check: coverage is
limited, and the QIDs were found with name similarity and coordinates, so it is not fully independent.
"""
import pandas as pd

rec = pd.read_csv("data/out/wikidata_reconciled.csv")
road_q = rec[rec.kind == "road"].drop_duplicates("name").set_index("name").qid
rec["key"] = rec.name + "|" + rec.lat.round(5).astype(str) + "|" + rec.lon.round(5).astype(str)
aadr_q = rec[rec.kind == "aadr"].drop_duplicates("key").set_index("key").qid

g = pd.read_csv("data/gold/to_label.csv")
g["road_qid"] = g.road_locality.map(road_q)
g["aadr_qid"] = g.aadr_locality + "|" + g.aadr_lat.round(5).astype(str) + "|" + g.aadr_lon.round(5).astype(str)
g["aadr_qid"] = g.aadr_qid.map(aadr_q)


def status(r):
    if pd.isna(r.road_qid) or pd.isna(r.aadr_qid):
        return "no_info"
    return "same_qid" if r.road_qid == r.aadr_qid else "different_qid"


g["wikidata"] = g.apply(status, axis=1)
g["check"] = "no_info"
g.loc[(g.wikidata == "same_qid") & (g.label == "same"), "check"] = "agrees"
g.loc[(g.wikidata == "different_qid") & (g.label == "different"), "check"] = "agrees"
g.loc[(g.wikidata == "same_qid") & (g.label == "different"), "check"] = "CONFLICT"
g.loc[(g.wikidata == "different_qid") & (g.label == "same"), "check"] = "CONFLICT"
g.loc[g.wikidata.ne("no_info") & g.label.isin(["unsure", "broader", "exclude"]), "check"] = "not_checkable"

cols = ["pair_id", "road_locality", "aadr_locality", "distance_km", "label", "road_qid", "aadr_qid", "wikidata", "check"]
g[cols].to_csv("data/out/label_check_wikidata.csv", index=False)

lab = g[g.label.isin(["same", "different"])]
lines = ["# Gold labels vs Wikidata", "",
         f"Pairs with a QID on both sides: {(g.wikidata != 'no_info').sum()} of {len(g)}. "
         f"Of the {len(lab)} same/different pairs: "
         f"{(lab.check == 'agrees').sum()} agree, {(lab.check == 'CONFLICT').sum()} conflict, "
         f"{(lab.check == 'no_info').sum()} have no Wikidata information.", "",
         "```", pd.crosstab(g.label, g.check).to_string(), "```", ""]
conflicts = g[g.check == "CONFLICT"]
lines += ["Conflicts to review by hand:", "", "```",
          conflicts[cols].to_string(index=False) if len(conflicts) else "none", "```"]
open("data/out/label_check_wikidata.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
