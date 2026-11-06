# road2aadr

Linking sites in the ROCEEH Out of Africa Database (ROAD) to ancient genomes in the Allen Ancient DNA Resource (AADR), and evaluating how well different linking methods work. This README is a work in progress; the full write-up comes at the end.

## How the gold-standard labels were made

**The labels in `data/gold/to_label.csv` were not made by a human expert.** I had a large frontier language model with web search label the 100 candidate pairs. I did not label them myself, and no domain expert checked them. Treat them as model-assisted labels, not ground truth.

What this means for the evaluation:

- The labels can be wrong, especially where the model had to look up which excavation area a genome came from. Its own notes flag several pairs as depending on the exact sample ID (for example P040 and P074, Dolní Věstonice II vs III).
- I will evaluate an LLM judge against these labels. Because an LLM produced the labels, the two can share blind spots, so agreement may look better than it really is. I will say this next to every precision and recall number I report.
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
