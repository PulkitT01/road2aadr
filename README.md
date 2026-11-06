# road2aadr

I link sites in the [ROCEEH Out of Africa Database (ROAD)](https://www.roceeh.uni-tuebingen.de/roadweb/) to ancient genomes in the [Allen Ancient DNA Resource (AADR)](https://doi.org/10.7910/DVN/FFIDCW), publish the linked dataset, and evaluate how well different linking methods work against a hand-checkable gold standard.

**Viewer:** <https://pulkitt01.github.io/road2aadr/>. A map of the linked sites confirmed by Wikidata, and for each site a timeline with ROAD's archaeological layers next to the AADR genome dates. Many caves have old layers in ROAD and much younger genomes in AADR, which is the pattern the timeline makes visible.

## What the viewer shows

- **Map:** each dot is a ROAD site, an archaeological site that has a matching place in AADR, the database of ancient genomes. I only show sites where both databases point to the same Wikidata entry, so I can be fairly sure the match is right. Bigger dots have more genomes.
- **Site picker and panel:** click a dot or pick a site from the list. The panel names the matching AADR place and how far apart the two records are.
- **Timeline:** the orange dots are genomes, placed at the age of the individual. The grey bars are the layers ROAD records at that site, each spanning the years that layer covers. Hover over either for details.
- **Time axis:** ages are in years before 1950, so 10k means about 10,000 years ago. The scale is squeezed for very old dates so that recent and ancient things fit on one chart.
- **What to look for:** many genomes are much younger than the site's oldest layers. That usually means people used the cave again long after the old layers formed, not that the link is wrong.

## What is in the linked dataset

- 58 linked pairs: 54 ROAD sites and 51 AADR sites, covering 180 genomes (`data/out/road_aadr_links.csv`, one row per site pair, and `data/out/road_aadr_samples.csv`, one row per genome with its ID, date and publication).
- A pair is linked if a name-and-distance rule says so (name score of at least 95 and at most 10 km apart) or if both sites share a Wikidata item. The `evidence` column says which: 31 rule only, 25 rule plus Wikidata, 2 Wikidata only.
- The viewer shows only the links confirmed by a shared Wikidata item: 27 pairs, 26 ROAD sites and 100 genomes. The CSVs keep every link, so you can filter on the `evidence` column; the gold label, where there is one, is in `gold_label`.
- 38 of the 58 linked pairs are not in the gold set, so their quality is only estimated by the evaluation below.

## What ROAD already says about ancient DNA

ROAD records ancient DNA only as a category code in its human-remains table: `S`, sediment containing human aDNA. That is 8 rows at 5 sites (Chagyrskaya, Denisova Central chamber, Denisova East chamber, El Sidrón, Trou Al Wesse), all Neanderthal or Denisovan sediment DNA. ROAD has no sample IDs, dates or publications for them, so it can say a site has DNA evidence but cannot point to the AADR genome records. That link is what this project adds. Notes: `data/out/road_adna_findings.md`.

## Method

1. **ROAD:** pulled with the `roadDB` R package (snapshot of 2026-11-06): 2,127 localities, all with coordinates. The locality ID is the site name.
2. **AADR:** v66.p1, `v66.p1_1240K.aadr.PUB.anno`, checked against the published md5. 22,305 of 23,089 individuals have coordinates; they fall into 3,960 distinct sites.
3. **Candidates:** every ROAD site and AADR site within 25 km of each other, 1,543 pairs, each with a name similarity score (`src/candidates.py`).
4. **Gold standard:** 100 pairs labeled (see below).
5. **Methods compared:** a rule baseline, a join through shared Wikidata items, and a local LLM judge.

## How the gold-standard labels were made

**The labels in `data/gold/to_label.csv` were not made by a human expert.** I had Claude Opus 5.5, a large frontier language model, label the 100 candidate pairs with web search enabled and high reasoning effort. I did not label them myself, and no domain expert checked them. Treat them as model-assisted labels, not ground truth.

What this means for the evaluation:

- The labels can be wrong, especially where the model had to look up which excavation area a genome came from. Its own notes flag several pairs as depending on the exact sample ID (for example P040 and P074, Dolní Věstonice II vs III).
- I evaluate an LLM judge (Qwen 3.5 9B, run locally through Ollama, no web access) against these labels. Because an LLM produced the labels, the two can share blind spots, so agreement may look better than it really is. The judge is from a different model family than the labeller, which should reduce that, but not remove it.
- The label set extends my original `same / different / unsure` scheme with `broader` and `exclude`, which the model used.

| Label | Meaning |
|---|---|
| `same` | At least one AADR genome in the entry comes from this ROAD site. |
| `different` | Evidence shows the genomes come from somewhere else, or the names are unrelated with nothing linking them. |
| `broader` | One side is a broader area and the specific source could not be found. |
| `unsure` | The evidence is unclear. |
| `exclude` | The AADR entry is not a usable site (for example present-day samples at 0 BP). Not in my original definitions. |

How the labels are scored: `unsure` pairs are left out of scoring and their count is reported. `broader` and `exclude` are my call, not confirmed by anyone else: I also leave them out of the headline numbers, and `src/baseline.py` shows a sensitivity check with `broader` treated as `different` and as `same`.

**How the 100 pairs were chosen.** I drew them from the 1,543 candidates, stratified by distance (5 km or less, over 5 km) and name similarity (low, mid, high), with a fixed seed (`src/make_gold_sheet.py`). This is not a random sample, so the baseline script also reports population-weighted estimates, which have no confidence interval.

## Results

All numbers use the 91 gold pairs labeled `same` or `different` (15 `same`), so the confidence intervals (Wilson, 95%) are wide. The gold labels are model-made (see above). Details are in `data/out/`.

| Method | Precision | Recall |
|---|---|---|
| Rule baseline (name and distance thresholds, held-out in 5-fold cross-validation) | 0.87 [0.62, 0.96] | 0.87 [0.62, 0.96] |
| Wikidata join | 1.00 [0.70, 1.00] | 0.60 [0.36, 0.80] |
| Local LLM judge, first prompt (Qwen 3.5 9B) | 0.28 [0.18, 0.42] | 1.00 [0.80, 1.00] |

- **Baseline:** every cross-validation fold picked the same thresholds (name score at least 95, at most 10 km). Counting the four `broader` pairs as `different` drops precision to 0.68, so how `broader` is scored matters.
- **Wikidata:** 243 of 659 ROAD sites (37%) and 232 of 620 AADR sites (37%) in the candidate pairs got an item, using name similarity and coordinates (`src/wikidata.py`). 27 candidate pairs share an item. It never linked wrongly on the gold set, but it misses matches because many sites have no Wikidata item. It also found links the rule cannot, such as Grotte des Pigeons and Taforalt Cave, one site under two names.
- **Wikidata as a check on the labels:** 22 of the 100 gold pairs have an item on both sides; of the 91 scored pairs, 20 agree with Wikidata and none conflict (`data/out/label_check_wikidata.md`). This supports the labels but does not prove them: the items were found with name similarity and coordinates, the same signals the baseline uses.
- **LLM judge:** it found all 15 true matches but also called 38 of the 76 `different` pairs `same`, treating a nearby location as proof of identity. My prompt told it that caves are reused over time, and it quoted that line to justify wrong answers. This is the first prompt, reported as it came out and not tuned on the gold set. A hybrid that sent only unclear pairs to the judge reached precision 0.37 and recall 1.00 (`data/out/llm_results.md`).

## Limitations

- The gold labels come from one model, with no human expert and no inter-annotator agreement.
- Only 15 gold pairs are true matches, so every number has a wide interval.
- Recall is only relative to the 25 km candidate radius. A true match with a badly wrong coordinate is never considered. AADR individuals without coordinates (3.4%) are excluded.
- The rule thresholds were chosen on the same gold set that scores them (cross-validated for the table, but the published links use the thresholds picked on all of it).
- ROAD covers about 3 million years to 20,000 years ago, while most AADR genomes are far younger, so true overlaps are few and the linked set is small.
- ROAD layer ages and AADR dates come from different dating conventions (see the note under each timeline), so the timelines compare them only roughly.

## Related work

The technique is not new; the ROAD to AADR link and the evaluation against a rule baseline are what this project adds. [Poseidon](https://elifesciences.org/reviewed-preprints/98317) (Schmid et al.) is a framework for managing archaeogenetic data together with its archaeological context, and its linked-data conversion, [poseidon2lod](https://github.com/archaeonatural-cloud/poseidon2lod), matches Poseidon sites to GeoNames and Wikidata using coordinates, which is the same kind of site matching I do against a different target. [XRONOS](https://boris.unibe.ch/180863) is an open repository of radiocarbon and other chronometric data that has described work on reconciling duplicate records and on embedding its data in linked open data. Existing AADR viewers include the [AADR Visualizer](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12413226/) (an ArcGIS Online map) and [DORA](https://academic.oup.com/nar/article/52/W1/W54/7671306) (Data Overlays for Research in Archaeogenomics), which map AADR samples but do not link them to ROAD's archaeological layers. Poseidon and XRONOS both point toward linking through shared identifiers instead of one-off joins, which is why I included the Wikidata join.

## Reproduce

Needs [uv](https://docs.astral.sh/uv/), R with the `roadDB` package, and (for the judge step) Ollama with `qwen3.5:9b-mlx`.

```
uv sync
Rscript r/export_road.R            # ROAD tables to data/raw/
uv run python src/fetch_aadr.py    # AADR annotation file, md5 checked
uv run python src/candidates.py
uv run python src/make_gold_sheet.py   # writes the sheet; the committed labels are in data/gold/to_label.csv
uv run python src/baseline.py
uv run python src/wikidata.py          # slow: Wikidata rate-limits; responses are cached
uv run python src/check_labels_wikidata.py
uv run python src/llm_judge.py
uv run python src/export_links.py
uv run python src/export_site.py       # writes docs/data/sites.json
python3 -m http.server -d docs         # then open http://localhost:8000
```

`make_gold_sheet.py` rewrites `data/gold/to_label.csv` and would erase the labels, so do not rerun it on a labeled sheet.

## Data and license

ROAD data is licensed CC BY-SA 4.0, so I share the linked dataset under CC BY-SA 4.0 too. The dataset contains AADR sample metadata only (IDs, dates, publication abbreviations and DOIs). If you use it, cite the AADR release (v66.p1, <https://doi.org/10.7910/DVN/FFIDCW>), the original publication for each genome, and ROAD. I have not checked AADR's own terms of use, so check them before reusing the AADR fields.

## Future work

- A second judge prompt, tuned on part of the gold set and reported on the rest, and a stronger judge model.
- Expert labels, or at least a spot-check of the model's labels by someone who knows the sites.
- A larger gold set, so the intervals narrow.
- Wikidata reconciliation through SPARQL instead of name search, for better coverage.
