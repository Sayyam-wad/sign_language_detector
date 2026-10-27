# Robustness benchmark

Trained on clean training groups; tested on held-out groups with simulated changes (same SVM and split for both feature sets).

| Scenario | What it simulates | v1: original 42 distances | v2: new features | v2 + rotation augmentation |
|---|---|---|---|---|
| same conditions | held-out frames, unchanged | 99.4% | 100.0% | 100.0% |
| hand 40% smaller | standing further from the camera | 25.7% | 100.0% | 100.0% |
| hand 40% larger | closer to the camera | 66.3% | 100.0% | 100.0% |
| 16:9 camera | same hand on a 854x480 widescreen camera | 95.7% | 100.0% | 100.0% |
| other hand | signing with the other hand (mirror image) | 99.4% | 100.0% | 100.0% |
| wrist tilted 15° | hand rotated 15 degrees | 99.4% | 89.2% | 100.0% |
| wrist tilted 25° | hand rotated 25 degrees | 98.5% | 95.7% | 100.0% |
| wrist tilted 40° | beyond the augmentation range | 91.4% | 38.7% | 99.8% |
