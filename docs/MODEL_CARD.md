# Model card

## What it does

Classifies a single hand pose from a webcam frame into one of 41 signs: the 26 letters of the American Sign Language alphabet and 15 gesture phrases (HELLO, THANK YOU, YES, NO and others). The app turns a stream of these predictions into text.

Two models are trained from the same data:

- `artifacts/model.joblib`: an RBF support vector machine, used by the Python app.
- `web/model.json`: a small neural network (85 → 128 → 64 → 41), used by the browser demo because it is easy to run in JavaScript.

Both take 85 features computed from the 21 hand landmarks that MediaPipe Hands returns (see `asl/features.py`).

## Intended use

A learning project and demo of fingerspelling recognition. It is not a sign language translator. ASL is a full language with grammar, facial expressions and movement, and almost none of that is captured by single-hand static poses.

## Training data

- 4,100 webcam images, 100 per sign, recorded by one person in one session per sign.
- MediaPipe found a hand in 4,091 of them.
- Each image is turned into landmarks and features once (`python -m asl.dataset`). During training, two randomly rotated copies (up to ±25°) of every training sample are added.

## Evaluation

Images were recorded as runs of consecutive frames, which are near-duplicates. To avoid testing on copies of training frames, each run is cut into blocks of 20 frames, and whole blocks are held out. One block in five (813 samples) is the test set, and model selection uses cross-validation over the other blocks.

| Measure | Result |
|---|---|
| SVM accuracy on held-out blocks | 100.0% |
| Browser network accuracy on held-out blocks | 98.8% |
| Cross-validated macro-F1, all five model types | 99.5% to 99.9% |
| Time per frame: hand tracking / features + SVM | about 9.6 ms / 0.9 ms on one CPU core |

These numbers come from the same signer, camera and room as the training data, so they say little about other people. The robustness benchmark (`python -m asl.benchmark`) applies geometric changes to the held-out landmarks to estimate how the model copes with a different setup:

| Change to test frames | Original 42-distance features | Current features with augmentation |
|---|---|---|
| Hand 40% smaller (further from camera) | 25.7% | 100% |
| Hand 40% larger | 66.3% | 100% |
| 16:9 camera instead of 4:3 | 95.7% | 100% |
| Other hand | 99.4% | 100% |
| Wrist tilted 40° | 91.4% | 99.8% |

Lighting, skin tone, hand size and signing style of other people are not covered by this benchmark.

## Rejecting poses that aren't signs

A classifier always picks one of its classes, so a hand at rest would otherwise be typed as some letter. `asl/novelty.py` measures the distance from a pose to the nearest of 8 prototypes per sign and ignores poses that are further away than 97% of genuine held-out signs.

To test it, each sign in turn was left out of the detector's training, and we checked how often that never-seen sign was rejected:

| Threshold | Genuine signs accepted (per frame) | Never-seen signs rejected |
|---|---|---|
| 99% | 99.5% | 35.6% |
| 97% (used) | 96.6% | 79.1% |
| 95% | 95.6% | 89.9% |
| 90% | 90.2% | 99.6% |

Rejection is per frame. Predictions are smoothed over frames, so a few rejected frames while holding a real sign only slow it down slightly.

## Known limitations

- One signer. Expect lower accuracy for other people until more recording sessions from different people are added.
- J and Z are motion signs; only their final pose is recognised.
- One hand only, so two-handed signs are not supported.
- Some phrases share a hand shape with a letter (NO and C, OKAY and O, THANK YOU and Y, PEACE and V, INFINITE VOID and R). The app tells them apart only through the letter/phrase mode switch.
- "THANK YOU" and several other phrases are signed with movement in ASL; the dataset records a single pose for them.
