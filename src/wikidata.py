"""Reconcile ROAD localities and AADR sites to Wikidata QIDs, then join pairs on shared QID.

For each site: wbsearchentities on the cleaned name, fetch coordinates (P625) of the hits,
keep the best hit whose label is similar and whose coordinates are within MAX_KM of the site.
Only sites that appear in a <=25 km candidate pair are looked up. Responses are cached.

usage: uv run python src/wikidata.py [--limit N]
"""
import json
import math
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from rapidfuzz import fuzz

from candidates import norm

API = "https://www.wikidata.org/w/api.php"
HEADERS = {"User-Agent": "road2aadr/0.1 (research project; ROAD-AADR linking)"}
CACHE = Path("data/interim/wikidata_cache.json")
MAX_KM, MIN_LABEL_SCORE, PAIR_KM = 10, 85, 25

cache = json.loads(CACHE.read_text()) if CACHE.exists() else {"search": {}, "coords": {}}


def get(params):
    for attempt in range(8):
        r = requests.get(API, params={**params, "format": "json"}, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()
        # 429 carries Retry-After; honour it, otherwise back off
        time.sleep(min(int(r.headers.get("retry-after", 2 ** attempt)) + 1, 120))
    r.raise_for_status()


def search(name):
    if name not in cache["search"]:
        res = get({"action": "wbsearchentities", "search": name, "language": "en", "limit": 10})
        cache["search"][name] = [{"id": h["id"], "label": h.get("label", ""),
                                  "match": h.get("match", {}).get("text", ""),
                                  "desc": h.get("description", "")} for h in res.get("search", [])]
        time.sleep(0.5)
    return cache["search"][name]


def fetch_coords(qids):
    todo = [q for q in dict.fromkeys(qids) if q not in cache["coords"]]
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        res = get({"action": "wbgetentities", "ids": "|".join(chunk), "props": "claims"})
        for q in chunk:
            claims = res.get("entities", {}).get(q, {}).get("claims", {}).get("P625", [])
            v = claims[0]["mainsnak"].get("datavalue", {}).get("value") if claims else None
            cache["coords"][q] = [v["latitude"], v["longitude"]] if v else None


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def reconcile(name, lat, lon):
    query = re.sub(r"\(.*?\)", " ", name).strip()
    hits = search(query)
    fetch_coords([h["id"] for h in hits])
    best = None
    for h in hits:
        c = cache["coords"].get(h["id"])
        if not c:
            continue
        d = km(lat, lon, *c)
        score = max(fuzz.token_set_ratio(norm(query), norm(h["label"])),
                    fuzz.token_set_ratio(norm(query), norm(h["match"])))
        if d <= MAX_KM and score >= MIN_LABEL_SCORE and (best is None or (score, -d) > (best[2], -best[3])):
            best = (h["id"], h["label"], score, d)
    return best


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    c = pd.read_csv("data/interim/candidates.csv")
    c = c[c.distance_km <= PAIR_KM]
    road = c.drop_duplicates("road_locality")[["road_locality", "road_lat", "road_lon"]]
    aadr = c.drop_duplicates(["aadr_locality", "aadr_lat", "aadr_lon"])[["aadr_locality", "aadr_lat", "aadr_lon"]]
    sites = ([("road", n, la, lo) for n, la, lo in road.itertuples(index=False)]
             + [("aadr", n, la, lo) for n, la, lo in aadr.itertuples(index=False)])
    if limit:
        sites = sites[:limit]
    print(f"{len(sites)} sites to reconcile", flush=True)

    rows = []
    for i, (kind, name, lat, lon) in enumerate(sites, 1):
        b = reconcile(name, lat, lon)
        rows.append({"kind": kind, "name": name, "lat": lat, "lon": lon,
                     "qid": b[0] if b else None, "wd_label": b[1] if b else None,
                     "label_score": b[2] if b else None, "wd_dist_km": round(b[3], 2) if b else None})
        if i % 50 == 0:
            CACHE.write_text(json.dumps(cache))
            print(f"{i}/{len(sites)}", flush=True)
    CACHE.write_text(json.dumps(cache))

    rec = pd.DataFrame(rows)
    rec.to_csv("data/out/wikidata_reconciled.csv", index=False)
    print(rec.groupby("kind").qid.agg(total="size", matched="count"))

    r = rec[rec.kind == "road"].set_index("name").qid
    a = rec[rec.kind == "aadr"].drop_duplicates("name").set_index("name").qid
    c = c.assign(road_qid=c.road_locality.map(r), aadr_qid=c.aadr_locality.map(a))
    links = c[c.road_qid.notna() & (c.road_qid == c.aadr_qid)]
    links.to_csv("data/out/wikidata_links.csv", index=False)
    print(f"{len(links)} pairs share a QID, of {len(c)} candidate pairs")


if __name__ == "__main__":
    main()
