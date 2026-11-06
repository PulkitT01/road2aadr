"""Rule baseline: link a pair when name_score >= t_name AND distance_km <= t_dist.

Thresholds are tuned for F1 inside each training fold (stratified 5-fold CV), and precision/recall
are computed on the pooled held-out predictions. Scored labels: same / different. unsure, broader
and exclude are left out and counted. A sensitivity run maps broader to different, then to same.
Also gives a population-weighted estimate, since the gold pairs are a stratified sample.
"""
import itertools
import math

import pandas as pd
from sklearn.model_selection import StratifiedKFold

SEED, FOLDS = 7, 5
NAME_GRID = range(50, 101, 5)
DIST_GRID = [1, 2, 5, 10, 15, 25]
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def predict(df, t_name, t_dist):
    return (df.name_score >= t_name) & (df.distance_km <= t_dist)


def counts(y, p, w=None):
    w = 1.0 if w is None else w
    tp = (w * (y & p)).sum()
    fp = (w * (~y & p)).sum()
    fn = (w * (y & ~p)).sum()
    return tp, fp, fn


def prf(tp, fp, fn):
    pr = tp / (tp + fp) if tp + fp else float("nan")
    rc = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return pr, rc, f1


def tune(train):
    y = train.y.to_numpy()
    best = max(itertools.product(NAME_GRID, DIST_GRID),
               key=lambda t: prf(*counts(y, predict(train, *t).to_numpy()))[2])
    return best


def fmt_ci(k, n):
    lo, hi = wilson(k, n)
    return f"{k / n:.2f} [{lo:.2f}, {hi:.2f}]" if n else "n/a"


def evaluate(df, title):
    df = df.reset_index(drop=True)
    y = df.y.to_numpy()
    oof = pd.Series(False, index=df.index)
    chosen = []
    for tr, te in StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y):
        t = tune(df.iloc[tr])
        chosen.append(t)
        oof.iloc[te] = predict(df.iloc[te], *t).to_numpy()
    p = oof.to_numpy()
    tp, fp, fn = counts(y, p)
    say(f"### {title}")
    say(f"scored pairs: {len(df)} ({y.sum()} same, {(~y).sum()} different)")
    say(f"held-out precision {fmt_ci(int(tp), int(tp + fp))} (TP={int(tp)}, FP={int(fp)})")
    say(f"held-out recall    {fmt_ci(int(tp), int(tp + fn))} (TP={int(tp)}, FN={int(fn)})")
    say(f"held-out F1 {prf(tp, fp, fn)[2]:.2f}; thresholds per fold (name, km): {chosen}")

    # population-weighted: each gold pair stands for stratum_size / scored_in_stratum candidate pairs
    w = df.weight.to_numpy()
    wp, wr, wf = prf(*counts(y, p, w))
    say(f"population-weighted estimate (no CI): precision {wp:.2f}, recall {wr:.2f}, F1 {wf:.2f}")
    full = tune(df)
    say(f"thresholds tuned on all scored pairs (descriptive only, not held out): name>={full[0]}, km<={full[1]}")
    say()
    return df.assign(pred=p)


def gold_frame():
    """Gold pairs with features, labels, stratum, and the candidate count per stratum."""
    lab = pd.read_csv("data/gold/to_label.csv")[["pair_id", "label"]]
    feat = pd.read_csv("data/gold/pair_features.csv")
    cand = pd.read_csv("data/interim/candidates.csv")
    cand = cand[cand.distance_km <= 25]

    def strata(d):  # same cuts as make_gold_sheet.py
        return (pd.cut(d.name_score, [-1, 50, 85, 101], labels=False).astype(str) + "/"
                + pd.cut(d.distance_km, [-1, 5, 25], labels=False).astype(str))

    df = feat.merge(lab, on="pair_id")
    df["stratum"] = strata(df)
    return df, strata(cand).value_counts()


def scored(df, pop, mapping):
    """Rows whose label is in mapping, with a boolean y and a population weight."""
    d = df[df.label.isin(mapping)].copy()
    d["y"] = d.label.map(mapping).astype(bool)
    d["weight"] = d.stratum.map(pop) / d.groupby("stratum").stratum.transform("size")
    return d


def main():
    df, pop = gold_frame()

    say("# Baseline results (rule: name_score and distance thresholds)")
    say()
    say("Label counts: " + ", ".join(f"{k}={v}" for k, v in df.label.value_counts().items()))
    say("unsure, broader and exclude are left out of the main run.")
    say()

    runs = {"Main: same vs different": {"same": True, "different": False},
            "Sensitivity: broader counted as different": {"same": True, "different": False, "broader": False},
            "Sensitivity: broader counted as same": {"same": True, "different": False, "broader": True}}
    for i, (title, mapping) in enumerate(runs.items()):
        res = evaluate(scored(df, pop, mapping), title)
        if i == 0:
            res[["pair_id", "label", "name_score", "distance_km", "pred"]].to_csv(
                "data/out/baseline_predictions.csv", index=False)

    with open("data/out/baseline_results.md", "w") as f:
        f.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
