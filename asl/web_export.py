"""Export a trained MLP pipeline to JSON for the browser demo (web/).

The browser runs MediaPipe's hand landmarker, computes the same features in
JavaScript (web/features.js), and evaluates this network with plain matrix
maths. `parity_cases` holds a few landmark sets with the probabilities Python
computes for them; tests/test_web_parity.py checks the JavaScript gives the
same numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from asl.atlas import load as load_atlas
from asl.features import FEATURE_VERSION, landmark_features
from asl.labels import CLASSES, LETTER, PHRASE, output_label
from asl.novelty import NoveltyDetector


def _r(a, nd=6):
    return np.round(np.asarray(a, dtype=np.float64), nd).tolist()


def export(pipeline, novelty: NoveltyDetector | None, out: Path, metrics: dict | None = None,
           parity_points: list[tuple[np.ndarray, str]] | None = None) -> dict:
    scaler, mlp = pipeline.steps[0][1], pipeline.steps[-1][1]
    if mlp.activation != "relu" or mlp.out_activation_ != "softmax":
        raise ValueError("web export supports ReLU MLPs with a softmax output")
    classes = [int(c) for c in mlp.classes_]
    if parity_points is None:
        from asl.synthetic import hand_points
        rng = np.random.default_rng(1)
        parity_points = [(hand_points(rng.uniform(0, 1, 5), rng.uniform(-1, 1), rng=rng, noise=0.01,
                                      left=bool(i % 2)), "Left" if i % 2 else "Right") for i in range(4)]
    cases = []
    for pts, hand in parity_points:
        pts = np.round(np.asarray(pts, dtype=np.float64), 4)  # exactly what the JSON stores
        x = landmark_features(pts, hand)
        cases.append({"points": _r(pts, 4), "handedness": hand, "features": _r(x),
                      "probs": _r(pipeline.predict_proba(x[None, :])[0]),
                      "novelty": float(novelty.score(x)[0]) if novelty is not None else None})
    data = {
        "feature_version": FEATURE_VERSION,
        "scaler": {"mean": _r(scaler.mean_), "scale": _r(scaler.scale_)},
        "layers": [{"W": _r(W.T), "b": _r(b)} for W, b in zip(mlp.coefs_, mlp.intercepts_)],  # W: out x in
        "classes": classes,
        "labels": {mode: [output_label(c, mode) for c in classes] for mode in (LETTER, PHRASE)},
        "names": {str(c): CLASSES[c].name for c in classes},
        "novelty": novelty.to_dict() if novelty is not None else None,
        "atlas": {k: _r(v, 3) for k, v in load_atlas().items()},
        "metrics": {k: metrics[k] for k in ("web_model_test_accuracy", "n_samples", "n_classes")
                    if metrics and k in metrics},
        "parity_cases": cases,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, separators=(",", ":")))
    words = Path(__file__).resolve().parent / "assets" / "words.txt"
    if words.exists():  # word list for the demo's suggestions
        (out.parent / "words.txt").write_text(words.read_text())
    return data
