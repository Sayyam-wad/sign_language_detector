"""Train and honestly evaluate the sign classifier.

    python -m asl.train [--features artifacts/features.npz] [--models svm logreg rf mlp knn]

Evaluation protocol
  1. Hold out ~20% of the data as a test set *by group* (recording session, or a
     block of consecutive frames), so near-duplicate frames never sit on both
     sides of the split.
  2. Choose the model by grouped cross-validation on the remaining 80%
     (macro-F1). The test set is used once, for the final numbers only. (The
     original script picked the model with the best *test* score.)
  3. For comparison, also report what a random frame-level split would have
     claimed: the gap between the two is the leakage.
  4. Refit the chosen model on all data and save it with its metadata.

Outputs: artifacts/model.joblib, artifacts/report/{metrics.json,report.md,confusion_matrix.png}
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from asl import config
from asl.augment import augment
from asl.features import FEATURE_VERSION
from asl.labels import LETTER, PHRASE, name_of, output_label

SEED = config.RANDOM_STATE


def candidate_models() -> dict:
    return {
        "svm": make_pipeline(StandardScaler(), SVC(kernel="rbf", C=10, gamma="scale", probability=True,
                                                   class_weight="balanced", random_state=SEED)),
        "logreg": make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced")),
        "rf": RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced",
                                     n_jobs=-1, random_state=SEED),
        "mlp": make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(128, 64), alpha=1e-3,
                                                             early_stopping=True, max_iter=600, random_state=SEED)),
        "knn": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5, weights="distance")),
    }


def group_split(y, groups, test_fraction: float = 0.2):
    n_splits = max(2, round(1 / test_fraction))
    n_groups = len(np.unique(groups))
    if n_groups < n_splits:
        raise SystemExit(f"Only {n_groups} groups: need at least {n_splits} for a grouped split. "
                         "Collect more sessions or lower --block-size in asl.dataset.")
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    train_idx, test_idx = next(sgkf.split(np.zeros(len(y)), y, groups))
    return train_idx, test_idx


def mode_accuracy(y_true, y_pred, mode: str) -> float | None:
    """Accuracy after mapping classes to what the app would display in `mode`
    (look-alike letter/phrase classes are merged there)."""
    pairs = [(output_label(t, mode), output_label(p, mode)) for t, p in zip(y_true, y_pred)]
    pairs = [(t, p) for t, p in pairs if t is not None]
    return float(np.mean([t == p for t, p in pairs])) if pairs else None


def top_confusions(cm: np.ndarray, labels: list[int], k: int = 10) -> list[dict]:
    off = cm.copy()
    np.fill_diagonal(off, 0)
    out = []
    for flat in np.argsort(off, axis=None)[::-1][:k]:
        i, j = np.unravel_index(flat, off.shape)
        if off[i, j] == 0:
            break
        out.append({"true": name_of(labels[i]), "predicted": name_of(labels[j]), "count": int(off[i, j])})
    return out


def save_confusion_png(cm: np.ndarray, labels: list[int], path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    names = [name_of(c) for c in labels]
    norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    size = max(6, 0.32 * len(names))
    fig, ax = plt.subplots(figsize=(size, size))
    ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(names)), names, rotation=90, fontsize=7)
    ax.set_yticks(range(len(names)), names, fontsize=7)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion matrix on held-out groups (row-normalised)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def write_markdown(m: dict, path: Path) -> None:
    lines = [
        "# Evaluation report", "",
        f"- Samples: {m['n_samples']} ({m['n_train']} train / {m['n_test']} test), "
        f"{m['n_classes']} classes, {m['n_groups']} groups",
        f"- Model: **{m['best_model']}** (chosen by grouped CV macro-F1); augmentation: {m['augmentation']}", "",
        "| Metric | Value |", "|---|---|",
        f"| Test accuracy (grouped split) | {m['test']['accuracy']:.2%} |",
        f"| Test macro-F1 (grouped split) | {m['test']['macro_f1']:.2%} |",
    ]
    if m["test"].get("letter_mode_accuracy") is not None:
        lines.append(f"| Letter-mode accuracy (look-alikes merged) | {m['test']['letter_mode_accuracy']:.2%} |")
    if m["test"].get("phrase_mode_accuracy") is not None:
        lines.append(f"| Phrase-mode accuracy (look-alikes merged) | {m['test']['phrase_mode_accuracy']:.2%} |")
    if m.get("random_split_accuracy") is not None:
        lines.append(f"| Accuracy with a random frame-level split (leaky) | {m['random_split_accuracy']:.2%} |")
    lines.append(f"| Inference latency (model only, per frame) | {m['latency_ms']:.2f} ms |")
    lines += ["", "## Model comparison (grouped CV on the training split)", "",
              "| Model | Macro-F1 (mean ± sd) |", "|---|---|"]
    for name, s in m["cv"].items():
        lines.append(f"| {name} | {s['mean']:.3f} ± {s['std']:.3f} |")
    lines += ["", "## Most frequent confusions", "", "| True | Predicted | Count |", "|---|---|---|"]
    lines += [f"| {c['true']} | {c['predicted']} | {c['count']} |" for c in m["top_confusions"]] or ["| – | – | – |"]
    lines += ["", "## Per-class results", "", "| Class | Precision | Recall | F1 | Support |", "|---|---|---|---|---|"]
    for c in m["per_class"]:
        lines.append(f"| {c['class']} | {c['precision']:.2f} | {c['recall']:.2f} | {c['f1']:.2f} | {c['support']} |")
    path.write_text("\n".join(lines) + "\n")


def train(features_path: Path, model_names: list[str], cv_folds: int = 4, refit_all: bool = True,
          out_model: Path = config.MODEL_PATH, report_dir: Path = config.REPORT_DIR,
          augment_copies: int = 2) -> dict:
    import joblib
    import sklearn

    from asl.dataset import load
    d = load(features_path)
    X, y, groups = d["X"], d["y"].astype(int), d["groups"]
    print(f"{len(y)} samples, {len(np.unique(y))} classes, {len(np.unique(groups))} groups")
    can_augment = augment_copies > 0 and "landmarks" in d

    def fit(model, idx):
        """Fit on samples `idx`, plus rotated copies of them (never of test samples)."""
        Xf, yf = X[idx], y[idx]
        if can_augment:
            Xa, ya = augment(d["landmarks"][idx], d["handedness"][idx], y[idx], copies=augment_copies)
            Xf, yf = np.vstack([Xf, Xa]), np.concatenate([yf, ya])
        return clone(model).fit(Xf, yf)

    tr, te = group_split(y, groups)
    models = {k: v for k, v in candidate_models().items() if k in model_names}
    folds = min(cv_folds, len(np.unique(groups[tr])))
    cv = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=SEED)

    cv_scores = {}
    for name, model in models.items():
        t0 = time.time()
        s = np.array([f1_score(y[tr][b], fit(model, tr[a]).predict(X[tr][b]), average="macro")
                      for a, b in cv.split(X[tr], y[tr], groups[tr])])
        cv_scores[name] = {"mean": float(s.mean()), "std": float(s.std())}
        print(f"  {name:<7} CV macro-F1 {s.mean():.3f} ± {s.std():.3f}  ({time.time() - t0:.1f}s)")
    # Ties (within 0.002 macro-F1) go to the earlier, simpler/smaller model in the list.
    top = max(v["mean"] for v in cv_scores.values())
    best = next(k for k in cv_scores if cv_scores[k]["mean"] >= top - 0.002)
    print(f"Best by CV: {best}")

    model = fit(models[best], tr)
    pred = model.predict(X[te])
    labels = sorted(np.unique(y))
    p, r, f, s = precision_recall_fscore_support(y[te], pred, labels=labels, zero_division=0)
    cm = confusion_matrix(y[te], pred, labels=labels)

    t0 = time.perf_counter()
    for row in X[te][:200]:
        model.predict_proba(row[None, :])
    latency_ms = (time.perf_counter() - t0) / min(200, len(te)) * 1000

    # What a random frame-level split reports (for comparison only).
    rs_tr, rs_te = train_test_split(np.arange(len(y)), test_size=0.2, stratify=y, random_state=SEED)
    random_acc = accuracy_score(y[rs_te], fit(models[best], rs_tr).predict(X[rs_te]))

    metrics = {
        "feature_version": FEATURE_VERSION,
        "n_samples": int(len(y)), "n_train": int(len(tr)), "n_test": int(len(te)),
        "n_classes": int(len(labels)), "n_groups": int(len(np.unique(groups))),
        "augmentation": f"{augment_copies} rotated copies per sample" if can_augment else "none",
        "cv": cv_scores, "best_model": best,
        "test": {
            "accuracy": float(accuracy_score(y[te], pred)),
            "macro_f1": float(f1_score(y[te], pred, average="macro")),
            "letter_mode_accuracy": mode_accuracy(y[te], pred, LETTER),
            "phrase_mode_accuracy": mode_accuracy(y[te], pred, PHRASE),
        },
        "random_split_accuracy": float(random_acc),
        "latency_ms": float(latency_ms),
        "per_class": [{"class": name_of(c), "precision": float(pi), "recall": float(ri), "f1": float(fi),
                       "support": int(si)} for c, pi, ri, fi, si in zip(labels, p, r, f, s)],
        "top_confusions": top_confusions(cm, labels),
    }
    t = metrics["test"]
    print(f"\nHeld-out test (grouped): accuracy {t['accuracy']:.2%}, macro-F1 {t['macro_f1']:.2%}")
    print(f"Random frame-level split would report: {random_acc:.2%}")

    if refit_all:
        model = fit(models[best], np.arange(len(y)))
    out_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "classes": [int(c) for c in model.classes_], "feature_version": FEATURE_VERSION,
                 "metrics": metrics, "sklearn_version": sklearn.__version__, "python": platform.python_version(),
                 "trained_on": "all data" if refit_all else "train split"}, out_model)

    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    write_markdown(metrics, report_dir / "report.md")
    if save_confusion_png(cm, labels, report_dir / "confusion_matrix.png"):
        print(f"Confusion matrix: {report_dir / 'confusion_matrix.png'}")
    print(f"Saved model to {out_model} and report to {report_dir}/")
    return metrics


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--features", type=Path, default=config.FEATURES_PATH)
    p.add_argument("--models", nargs="+", default=list(candidate_models()), choices=list(candidate_models()))
    p.add_argument("--cv-folds", type=int, default=4)
    p.add_argument("--no-refit", action="store_true", help="save the model trained on the train split only")
    p.add_argument("--augment", type=int, default=2, help="rotated copies per training sample (0 = off)")
    p.add_argument("--out", type=Path, default=config.MODEL_PATH)
    p.add_argument("--report-dir", type=Path, default=config.REPORT_DIR)
    a = p.parse_args(argv)
    train(a.features, a.models, a.cv_folds, not a.no_refit, a.out, a.report_dir, a.augment)


if __name__ == "__main__":
    main()
