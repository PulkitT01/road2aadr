"""LLM judge (local Ollama model) for ROAD-AADR pairs, plus comparison with the rule baseline.

Judges all 100 gold pairs (resumable, every prompt and answer goes to data/out/llm_log.jsonl), then scores
three systems on the same/different gold pairs:
  baseline  - rule from baseline.py, held-out predictions
  judge     - the LLM decides every pair
  hybrid    - auto-same if name_score >= 95 and distance <= 2 km; auto-different if name_score < 50;
              the LLM decides the rest. These cut-offs were fixed before looking at judge results and
              not tuned on the gold set.
A judge answer of unsure, broader or invalid counts as "not linked".
"""
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

from baseline import counts, fmt_ci, gold_frame, prf, scored

MODEL = "qwen3.5:9b-mlx"
URL = "http://localhost:11434/api/chat"
LOG = Path("data/out/llm_log.jsonl")
LABELS = {"same", "different", "broader", "unsure"}

PROMPT = """You decide whether two database records refer to the same physical archaeological site.
Record A comes from ROAD, a database of Palaeolithic sites. Record B is a place name from AADR, a database of ancient genomes. You have no web access; use only the facts below and what you know.

Record A (ROAD): {road_locality}, {road_country}; lat {road_lat:.4f}, lon {road_lon:.4f}; site age range {road_age_max:.0f} to {road_age_min:.0f} years BP.
Record B (AADR): {aadr_locality}, {aadr_country}; lat {aadr_lat:.4f}, lon {aadr_lon:.4f}; {aadr_n_samples} genomes dated {aadr_date_max:.0f} to {aadr_date_min:.0f} years BP.
Distance between the two coordinates: {distance_km:.1f} km.

Labels:
- same: at least one AADR genome in record B comes from the ROAD site in record A.
- different: the genomes come from somewhere else, or the names are unrelated with nothing linking them.
- broader: one record is a broader area (a town, city or region) and the specific source site cannot be determined.
- unsure: the evidence is unclear.
Different dates do not mean different sites: caves are reused over time. Answer with ONLY a JSON object: {{"label": "same|different|broader|unsure", "reason": "one sentence"}}"""


def ask(prompt):
    t = time.time()
    r = requests.post(URL, json={"model": MODEL, "stream": False, "think": False,
                                 "options": {"temperature": 0, "seed": 7},
                                 "messages": [{"role": "user", "content": prompt}]}, timeout=300)
    r.raise_for_status()
    return r.json()["message"]["content"], round(time.time() - t, 1)


def parse(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        d = json.loads(m.group(0))
        return (d["label"], d.get("reason", "")) if d["label"] in LABELS else ("invalid", raw)
    except (AttributeError, KeyError, ValueError, TypeError):
        return "invalid", raw


def judge_all(feat):
    done = {json.loads(l)["pair_id"] for l in LOG.read_text().splitlines()} if LOG.exists() else set()
    sheet = pd.read_csv("data/gold/to_label.csv").merge(feat[["pair_id", "distance_km"]], on="pair_id", suffixes=("_x", ""))
    for i, row in enumerate(sheet.itertuples(index=False), 1):
        if row.pair_id in done:
            continue
        prompt = PROMPT.format(**row._asdict())
        raw, secs = ask(prompt)
        label, reason = parse(raw)
        with LOG.open("a") as f:
            f.write(json.dumps({"pair_id": row.pair_id, "model": MODEL, "prompt": prompt, "raw": raw,
                                "label": label, "reason": reason, "seconds": secs}) + "\n")
        print(f"{i}/{len(sheet)} {row.pair_id} -> {label} ({secs}s)", flush=True)


def main():
    df, pop = gold_frame()
    judge_all(df)
    log = pd.DataFrame([json.loads(l) for l in LOG.read_text().splitlines()]).drop_duplicates("pair_id", keep="last")
    df = df.merge(log[["pair_id", "label", "seconds"]].rename(columns={"label": "judge", "seconds": "judge_s"}), on="pair_id")
    base = pd.read_csv("data/out/baseline_predictions.csv")[["pair_id", "pred"]].rename(columns={"pred": "baseline"})

    d = scored(df, pop, {"same": True, "different": False}).merge(base, on="pair_id")
    d["judge_same"] = d.judge == "same"
    auto_same = (d.name_score >= 95) & (d.distance_km <= 2)
    auto_diff = d.name_score < 50
    d["hybrid"] = d.judge_same.mask(auto_same, True).mask(auto_diff, False)
    routed = ~auto_same & ~auto_diff

    out = ["# LLM judge results", "",
           f"Model: {MODEL} via Ollama, temperature 0, no web access. Judged {len(df)} pairs in {df.judge_s.sum() / 60:.1f} min total.",
           "Judge answer counts: " + ", ".join(f"{k}={v}" for k, v in df.judge.value_counts().items()), "",
           f"Scored on {len(d)} same/different gold pairs ({d.y.sum()} same). Hybrid sent {routed.sum()} of {len(d)} pairs to the LLM.",
           "Gold labels were made by Claude Opus 5.5 with web search, not a human expert (see README).", "",
           "| System | Precision (95% CI) | Recall (95% CI) | F1 | Pop.-weighted P / R |", "|---|---|---|---|---|"]
    y = d.y.to_numpy()
    for name, col in [("baseline (held-out)", "baseline"), ("LLM judge alone", "judge_same"), ("hybrid", "hybrid")]:
        p = d[col].to_numpy().astype(bool)
        tp, fp, fn = counts(y, p)
        wp, wr, _ = prf(*counts(y, p, d.weight.to_numpy()))
        out.append(f"| {name} | {fmt_ci(int(tp), int(tp + fp))} | {fmt_ci(int(tp), int(tp + fn))} | "
                   f"{prf(tp, fp, fn)[2]:.2f} | {wp:.2f} / {wr:.2f} |")
    out += ["", "Judge vs gold label (all 100 pairs, rows = gold, columns = judge):", "", "```", pd.crosstab(df.label, df.judge).to_string(), "```"]
    Path("data/out/llm_results.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
