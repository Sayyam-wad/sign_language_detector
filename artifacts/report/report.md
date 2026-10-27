# Evaluation report

- Samples: 4091 (3278 train / 813 test), 41 classes, 5 groups
- Model: **svm** (chosen by grouped CV macro-F1); augmentation: 2 rotated copies per sample

| Metric | Value |
|---|---|
| Test accuracy (grouped split) | 100.00% |
| Test macro-F1 (grouped split) | 100.00% |
| Letter-mode accuracy (look-alikes merged) | 100.00% |
| Phrase-mode accuracy (look-alikes merged) | 100.00% |
| Accuracy with a random frame-level split (leaky) | 100.00% |
| Inference latency (model only, per frame) | 0.47 ms |

## Model comparison (grouped CV on the training split)

| Model | Macro-F1 (mean ± sd) |
|---|---|
| svm | 0.999 ± 0.001 |
| logreg | 0.998 ± 0.004 |
| rf | 0.999 ± 0.001 |
| mlp | 0.995 ± 0.007 |
| knn | 0.998 ± 0.003 |

## Most frequent confusions

| True | Predicted | Count |
|---|---|---|
| – | – | – |

## Per-class results

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| A | 1.00 | 1.00 | 1.00 | 19 |
| B | 1.00 | 1.00 | 1.00 | 20 |
| L | 1.00 | 1.00 | 1.00 | 20 |
| I LOVE YOU | 1.00 | 1.00 | 1.00 | 20 |
| YES | 1.00 | 1.00 | 1.00 | 20 |
| NO | 1.00 | 1.00 | 1.00 | 20 |
| OKAY | 1.00 | 1.00 | 1.00 | 20 |
| THANK YOU | 1.00 | 1.00 | 1.00 | 20 |
| RESTROOM | 1.00 | 1.00 | 1.00 | 20 |
| INFINITE VOID | 1.00 | 1.00 | 1.00 | 20 |
| HELLO | 1.00 | 1.00 | 1.00 | 20 |
| PEACE | 1.00 | 1.00 | 1.00 | 20 |
| GOOD | 1.00 | 1.00 | 1.00 | 20 |
| BAD | 1.00 | 1.00 | 1.00 | 20 |
| TAKE CARE | 1.00 | 1.00 | 1.00 | 20 |
| HOPE | 1.00 | 1.00 | 1.00 | 20 |
| I HATE YOU | 1.00 | 1.00 | 1.00 | 20 |
| BYE | 1.00 | 1.00 | 1.00 | 20 |
| C | 1.00 | 1.00 | 1.00 | 20 |
| D | 1.00 | 1.00 | 1.00 | 20 |
| E | 1.00 | 1.00 | 1.00 | 20 |
| F | 1.00 | 1.00 | 1.00 | 20 |
| G | 1.00 | 1.00 | 1.00 | 20 |
| H | 1.00 | 1.00 | 1.00 | 20 |
| I | 1.00 | 1.00 | 1.00 | 20 |
| J | 1.00 | 1.00 | 1.00 | 20 |
| K | 1.00 | 1.00 | 1.00 | 20 |
| M | 1.00 | 1.00 | 1.00 | 20 |
| N | 1.00 | 1.00 | 1.00 | 20 |
| O | 1.00 | 1.00 | 1.00 | 20 |
| P | 1.00 | 1.00 | 1.00 | 17 |
| Q | 1.00 | 1.00 | 1.00 | 18 |
| R | 1.00 | 1.00 | 1.00 | 20 |
| S | 1.00 | 1.00 | 1.00 | 20 |
| T | 1.00 | 1.00 | 1.00 | 20 |
| U | 1.00 | 1.00 | 1.00 | 20 |
| V | 1.00 | 1.00 | 1.00 | 20 |
| W | 1.00 | 1.00 | 1.00 | 20 |
| X | 1.00 | 1.00 | 1.00 | 20 |
| Y | 1.00 | 1.00 | 1.00 | 19 |
| Z | 1.00 | 1.00 | 1.00 | 20 |
