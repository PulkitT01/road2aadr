# LLM judge results

Model: qwen3.5:9b-mlx via Ollama, temperature 0, no web access. Judged 100 pairs in 7.3 min total.
Judge answer counts: same=60, different=38, broader=2

Scored on 91 same/different gold pairs (15 same). Hybrid sent 53 of 91 pairs to the LLM.
Gold labels were made by Claude Opus 5.5 with web search, not a human expert (see README).

| System | Precision (95% CI) | Recall (95% CI) | F1 | Pop.-weighted P / R |
|---|---|---|---|---|
| baseline (held-out) | 0.87 [0.62, 0.96] | 0.87 [0.62, 0.96] | 0.87 | 0.90 / 0.95 |
| LLM judge alone | 0.28 [0.18, 0.42] | 1.00 [0.80, 1.00] | 0.44 | 0.16 / 1.00 |
| hybrid | 0.37 [0.24, 0.52] | 1.00 [0.80, 1.00] | 0.54 | 0.55 / 1.00 |

Judge vs gold label (all 100 pairs, rows = gold, columns = judge):

```
judge      broader  different  same
label                              
broader          0          1     3
different        1         37    38
exclude          1          0     0
same             0          0    15
unsure           0          0     4
```
