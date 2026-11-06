# road2aadr

Linking sites in the ROCEEH Out of Africa Database (ROAD) to ancient genomes in the Allen Ancient DNA Resource (AADR), and evaluating how well different linking methods work. This README is a work in progress; the full write-up comes at the end.

## How the gold-standard labels were made

**The labels in `data/gold/to_label.csv` were not made by a human expert.** I had Claude Opus 5.5, a large frontier language model, label the 100 candidate pairs with web search enabled and high reasoning effort. I did not label them myself, and no domain expert checked them. Treat them as model-assisted labels, not ground truth.

What this means for the evaluation:

- The labels can be wrong, especially where the model had to look up which excavation area a genome came from. Its own notes flag several pairs as depending on the exact sample ID (for example P040 and P074, Dolní Věstonice II vs III).
- I evaluate an LLM judge (Qwen 3.5 9B, run locally through Ollama, no web access) against these labels. Because an LLM produced the labels, the two can share blind spots, so agreement may look better than it really is. The judge is from a different model family than the labeller, which should reduce that, but not remove it. I will say this next to every precision and recall number I report.
- The label set extends my original `same / different / unsure` scheme with `broader` and `exclude`, which the model used.

Label definitions I am using:

| Label | Meaning |
|---|---|
| `same` | At least one AADR genome in the entry comes from this ROAD site. |
| `different` | Evidence shows the genomes come from somewhere else, or the names are unrelated with nothing linking them. |
| `broader` | One side is a broader area and the specific source could not be found. |
| `unsure` | The evidence is unclear. |
| `exclude` | The AADR entry is not a usable site (for example present-day samples at 0 BP). Not in my original definitions. |

How the labels are scored:

- `unsure` pairs are left out of scoring and their count is reported.
- `broader` and `exclude` are my call, not yet confirmed: I also leave them out of the headline numbers and report their counts, and I show a sensitivity check with `broader` treated as `different` and as `same`.

## How the 100 pairs were chosen

A pair is one ROAD locality and one AADR site (name plus coordinates) within 25 km of each other, which gives 1,543 candidate pairs. I drew 100 of them stratified by distance (5 km or less, over 5 km) and name similarity (low, mid, high), with a fixed seed. This is not a random sample, so population-level precision and recall need to be reweighted by stratum. The generating script is `src/make_gold_sheet.py`.

## Data versions

- ROAD through the `roadDB` R package, snapshot pulled on 2026-11-06.
- AADR v66.p1, `v66.p1_1240K.aadr.PUB.anno`, checked against the published md5.

## Results so far

All numbers use the 91 gold pairs labeled `same` or `different` (15 `same`), so the confidence intervals are wide. The gold labels are model-made, not expert-made (see above). Details are in `data/out/`.

### Wikidata matching

I matched sites to Wikidata items using name similarity and coordinates (`src/wikidata.py`). 243 of 659 ROAD sites (37%) and 232 of 620 AADR sites (37%) in the candidate pairs got an item. 27 of the 1,543 candidate pairs share an item (`data/out/wikidata_links.csv`).

I used the shared item as a third linking method, and also as a partial check on the gold labels (`src/check_labels_wikidata.py`, results in `data/out/label_check_wikidata.md`):

- 22 of the 100 gold pairs have a Wikidata item on both sides. Of the 91 `same`/`different` pairs, 20 agree with Wikidata and none conflict. The other 71 have no Wikidata information and are still unchecked.
- This supports the labels but does not prove them. I found the items with name similarity and coordinates, the same signals the baseline uses, so agreement on easy pairs is partly circular. The uncertain pairs (`broader`, `unsure`) are exactly where Wikidata has no answer.
- As a linking method, a shared item gives precision 1.00 [0.70, 1.00] and recall 0.60 [0.36, 0.80] (9 correct links, no wrong links, 6 misses). It is cautious: it never linked wrongly, but it misses matches because many sites have no Wikidata item.

### Method comparison

| Method | Precision (95% CI) | Recall (95% CI) |
|---|---|---|
| Rule baseline (name and distance thresholds, held-out) | 0.87 [0.62, 0.96] | 0.87 [0.62, 0.96] |
| Wikidata join | 1.00 [0.70, 1.00] | 0.60 [0.36, 0.80] |
| Local LLM judge, first prompt (Qwen 3.5 9B) | 0.28 [0.18, 0.42] | 1.00 [0.80, 1.00] |

The LLM judge over-links: it found all 15 true matches but also called 38 of the 76 `different` pairs `same`, treating a nearby location as proof of identity. My prompt told it that caves are reused over time, and it quoted that line to justify wrong answers. This is the first prompt, reported as it came out; I have not tuned it on the gold set yet.
