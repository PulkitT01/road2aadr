"""Candidate ROAD locality x AADR locality pairs within a radius, scored by name similarity."""
import re
import unicodedata

import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from sklearn.neighbors import BallTree

AADR = "data/raw/v66.p1_1240K.aadr.PUB.anno"
EARTH_KM = 6371.0088
RADIUS_KM = 50  # widest radius; narrower ones are filtered from distance_km
STOP = {"cave", "grotte", "grotta", "cueva", "site", "rockshelter", "shelter", "abri", "the", "of", "de", "la", "le"}


def norm(s, drop_parens=False):
    s = str(s)
    if drop_parens:
        s = re.sub(r"\(.*?\)", " ", s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    words = re.findall(r"[a-z0-9]+", s)
    return " ".join(w for w in words if w not in STOP)


def load_aadr():
    d = pd.read_csv(AADR, sep="\t", low_memory=False)
    c = d.columns
    out = pd.DataFrame({
        "genetic_id": d[c[0]], "master_id": d[c[2]], "group_id": d["Group ID"],
        "locality": d["Locality"], "country": d["Political Entity"],
        "lat": pd.to_numeric(d["Latitude"], errors="coerce"),
        "lon": pd.to_numeric(d["Longitude"], errors="coerce"),
        "date_bp": pd.to_numeric(d[c[10]], errors="coerce"),
        "date_sd": pd.to_numeric(d[c[11]], errors="coerce"),
        "full_date": d[c[12]], "publication": d["Publication abbreviation"], "doi": d[c[7]],
    })
    n = len(out)
    out = out.dropna(subset=["lat", "lon", "locality"])
    print(f"AADR: {n} individuals, {len(out)} with coordinates ({len(out)/n:.1%})")
    return out


def main():
    road = pd.read_csv("data/raw/localities.csv").rename(columns={"coord_x": "lon", "coord_y": "lat"})
    road = road[["locality_id", "country", "lat", "lon", "locality_age_min", "locality_age_max"]]
    aadr = load_aadr()

    # one row per AADR site (name + coordinates), with the sample date range
    sites = (aadr.groupby(["locality", "lat", "lon"], as_index=False)
             .agg(country=("country", "first"), n_samples=("genetic_id", "size"),
                  date_min=("date_bp", "min"), date_max=("date_bp", "max")))
    print(f"AADR sites: {len(sites)}")

    tree = BallTree(np.radians(sites[["lat", "lon"]].to_numpy()), metric="haversine")
    idx, dist = tree.query_radius(np.radians(road[["lat", "lon"]].to_numpy()),
                                  r=RADIUS_KM / EARTH_KM, return_distance=True)
    rows = []
    for i, (js, ds) in enumerate(zip(idx, dist)):
        r = road.iloc[i]
        for j, dkm in zip(js, ds * EARTH_KM):
            s = sites.iloc[j]
            rows.append({
                "road_locality": r.locality_id, "road_country": r.country,
                "road_lat": r.lat, "road_lon": r.lon,
                "road_age_min": r.locality_age_min, "road_age_max": r.locality_age_max,
                "aadr_locality": s.locality, "aadr_country": s.country,
                "aadr_lat": s.lat, "aadr_lon": s.lon, "aadr_n_samples": s.n_samples,
                "aadr_date_min": s.date_min, "aadr_date_max": s.date_max,
                "distance_km": round(dkm, 2),
                "name_score": fuzz.token_set_ratio(norm(r.locality_id), norm(s.locality, drop_parens=True)),
                "date_overlap": bool(s.date_min <= r.locality_age_max and s.date_max >= r.locality_age_min),
            })
    cand = pd.DataFrame(rows)
    cand.to_csv("data/interim/candidates.csv", index=False)
    for km in (10, 25, 50):
        sub = cand[cand.distance_km <= km]
        print(f"<= {km:>2} km: {len(sub):>5} pairs, {sub.road_locality.nunique():>4} ROAD sites, "
              f"{(sub.name_score >= 80).sum():>4} with name_score>=80, {sub.date_overlap.sum():>4} with date overlap")


if __name__ == "__main__":
    main()
