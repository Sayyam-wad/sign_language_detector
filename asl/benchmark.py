"""Robustness benchmark: how do the features hold up when conditions change?

    python -m asl.benchmark [--features artifacts/features.npz]

A single-session dataset (one recording per sign) is easy: almost any model
scores ~100% on held-out frames from the same recording. What breaks in real
use is a *change*: you stand further back, use a different camera, sign with
the other hand, or tilt your wrist. This script trains on the clean training
groups and tests on held-out groups whose landmarks have been transformed to
simulate each change, comparing:

  v1  the original 42 wrist/fingertip distances on MediaPipe's [0,1] coordinates
  v2      the current features (asl.features)
  v2+aug  v2 trained with rotated copies of each sample (asl.augment), which
          is what `python -m asl.train` does by default

Same model (RBF SVM) and same split for both, so only the features differ.
Writes artifacts/report/robustness.{json,md}.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from asl import config
from asl.augment import augment, rotate_landmarks
from asl.features import landmark_features
from asl.train import group_split


# ── v1: the original feature extractor, reproduced exactly ────────────────────
def legacy_features(norm_xy: np.ndarray) -> np.ndarray:
    """42 Euclidean distances on normalised [0,1] image coordinates (create_dataset.py v1)."""
    p = norm_xy
    d = lambda i, j: float(np.hypot(*(p[i] - p[j])))  # noqa: E731
    f = [d(0, i) for i in range(1, 21)]
    tips, mcps = [4, 8, 12, 16, 20], [5, 9, 13, 17]
    f += [d(a, b) for k, a in enumerate(tips) for b in tips[k + 1:]]
    f += [d(a, b) for k, a in enumerate(mcps) for b in mcps[k + 1:]]
    f += [d(a, b) for a, b in [(4, 5), (8, 9), (12, 13), (16, 17), (20, 17), (4, 17)]]
    return np.asarray(f, dtype=np.float32)


# ── simulated condition changes (applied to pixel-space landmarks) ────────────
def _about_centre(pts, fn):
    c = pts[:, :2].mean(axis=0)
    out = pts.copy()
    out[:, :2] = fn(pts[:, :2] - c) + c
    return out


def scale(pts, factor):
    """Closer/further from the camera: MediaPipe's relative depth z scales with x and y."""
    out = _about_centre(pts, lambda q: q * factor)
    out[:, 2] = pts[:, 2] * factor
    return out


def rotate(pts, degrees):
    return rotate_landmarks(pts, degrees)


SCENARIOS = {
    # name: (description, fn(points, (w, h), handedness) -> (points, (w, h), handedness))
    "same conditions": ("held-out frames, unchanged", lambda p, s, h: (p, s, h)),
    "hand 40% smaller": ("standing further from the camera",
                         lambda p, s, h: (scale(p, 0.6), s, h)),
    "hand 40% larger": ("closer to the camera", lambda p, s, h: (scale(p, 1.4), s, h)),
    "16:9 camera": ("same hand on a 854x480 widescreen camera",
                    lambda p, s, h: (p, (round(s[1] * 16 / 9), s[1]), h)),
    "other hand": ("signing with the other hand (mirror image)",
                   lambda p, s, h: (np.c_[s[0] - p[:, 0], p[:, 1:]], s, "Left" if h == "Right" else "Right")),
    "wrist tilted 15°": ("hand rotated 15 degrees", lambda p, s, h: (rotate(p, 15), s, h)),
    "wrist tilted 25°": ("hand rotated 25 degrees", lambda p, s, h: (rotate(p, -25), s, h)),
    "wrist tilted 40°": ("beyond the augmentation range", lambda p, s, h: (rotate(p, 40), s, h)),
}


def featurize(points, sizes, hands, version: str) -> np.ndarray:
    if version == "v1":
        return np.stack([legacy_features(p[:, :2] / np.asarray(s, dtype=np.float64)) for p, s in zip(points, sizes)])
    return np.stack([landmark_features(p, h) for p, h in zip(points, hands)])  # v2 and v2+aug


def _plot(results: dict, path: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    names = list(results)
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for i, (key, label, color) in enumerate([("v1", "original features", "#c0c0c0"),
                                             ("v2+aug", "new features + augmentation", "#2f6db5")]):
        vals = [results[n][key] * 100 for n in names]
        bars = ax.bar(x + (i - 0.5) * 0.38, vals, 0.38, label=label, color=color)
        ax.bar_label(bars, fmt="%.0f", fontsize=8, padding=2)
    ax.set_xticks(x, [n.replace(" ", "\n", 1) for n in names], fontsize=9)
    ax.set_ylabel("accuracy (%)")
    ax.set_ylim(0, 112)
    ax.set_title("Accuracy on held-out frames under simulated condition changes", fontsize=11)
    ax.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run(features_path: Path, report_dir: Path) -> dict:
    d = np.load(features_path)
    if "landmarks" not in d.files:
        raise SystemExit("Feature file has no raw landmarks; rebuild it with `python -m asl.dataset`.")
    pts, sizes, hands = d["landmarks"], d["image_size"], d["handedness"]
    y, groups = d["y"].astype(int), d["groups"]
    tr, te = group_split(y, groups)
    print(f"train {len(tr)} / test {len(te)} samples (held-out groups)\n")

    results = {}
    for version in ("v1", "v2", "v2+aug"):
        model = make_pipeline(StandardScaler(), SVC(C=10, gamma="scale"))
        Xtr, ytr = featurize(pts[tr], sizes[tr], hands[tr], version), y[tr]
        if version == "v2+aug":
            Xa, ya = augment(pts[tr], hands[tr], y[tr])
            Xtr, ytr = np.vstack([Xtr, Xa]), np.concatenate([ytr, ya])
        model.fit(Xtr, ytr)
        for name, (_, fn) in SCENARIOS.items():
            moved = [fn(p.astype(np.float64), tuple(s), h) for p, s, h in zip(pts[te], sizes[te], hands[te])]
            Xt = featurize([m[0] for m in moved], [m[1] for m in moved], [m[2] for m in moved], version)
            acc = float((model.predict(Xt) == y[te]).mean())
            results.setdefault(name, {})[version] = acc
    print(f"{'scenario':<20}{'v1 (old)':>10}{'v2':>10}{'v2+aug':>10}")
    for name, r in results.items():
        print(f"{name:<20}{r['v1']:>10.1%}{r['v2']:>10.1%}{r['v2+aug']:>10.1%}")

    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "robustness.json").write_text(json.dumps(results, indent=2))
    lines = ["# Robustness benchmark", "",
             "Trained on clean training groups; tested on held-out groups with simulated changes "
             "(same SVM and split for both feature sets).", "",
             "| Scenario | What it simulates | v1: original 42 distances | v2: new features | v2 + rotation augmentation |",
             "|---|---|---|---|---|"]
    for name, r in results.items():
        lines.append(f"| {name} | {SCENARIOS[name][0]} | {r['v1']:.1%} | {r['v2']:.1%} | {r['v2+aug']:.1%} |")
    (report_dir / "robustness.md").write_text("\n".join(lines) + "\n")
    _plot(results, report_dir / "robustness.png")
    print(f"\nSaved {report_dir / 'robustness.md'}")
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--features", type=Path, default=config.FEATURES_PATH)
    p.add_argument("--report-dir", type=Path, default=config.REPORT_DIR)
    a = p.parse_args(argv)
    run(a.features, a.report_dir)


if __name__ == "__main__":
    main()
