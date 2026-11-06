# Baseline results (rule: name_score and distance thresholds)

Label counts: different=76, same=15, broader=4, unsure=4, exclude=1
unsure, broader and exclude are left out of the main run.

### Main: same vs different
scored pairs: 91 (15 same, 76 different)
held-out precision 0.87 [0.62, 0.96] (TP=13, FP=2)
held-out recall    0.87 [0.62, 0.96] (TP=13, FN=2)
held-out F1 0.87; thresholds per fold (name, km): [(95, 10), (95, 10), (95, 10), (95, 10), (95, 10)]
population-weighted estimate (no CI): precision 0.90, recall 0.95, F1 0.93
thresholds tuned on all scored pairs (descriptive only, not held out): name>=95, km<=10

### Sensitivity: broader counted as different
scored pairs: 95 (15 same, 80 different)
held-out precision 0.68 [0.46, 0.85] (TP=13, FP=6)
held-out recall    0.87 [0.62, 0.96] (TP=13, FN=2)
held-out F1 0.76; thresholds per fold (name, km): [(85, 10), (95, 10), (95, 10), (95, 10), (95, 10)]
population-weighted estimate (no CI): precision 0.72, recall 0.95, F1 0.82
thresholds tuned on all scored pairs (descriptive only, not held out): name>=95, km<=10

### Sensitivity: broader counted as same
scored pairs: 95 (19 same, 76 different)
held-out precision 0.88 [0.66, 0.97] (TP=15, FP=2)
held-out recall    0.79 [0.57, 0.91] (TP=15, FN=4)
held-out F1 0.83; thresholds per fold (name, km): [(95, 10), (95, 10), (95, 10), (95, 10), (95, 10)]
population-weighted estimate (no CI): precision 0.91, recall 0.73, F1 0.81
thresholds tuned on all scored pairs (descriptive only, not held out): name>=95, km<=10

