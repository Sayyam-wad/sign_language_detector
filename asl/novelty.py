"""Reject hand poses that don't look like any trained sign.

A classifier always picks *some* class, so a resting or random hand gets
forced into the nearest letter. This detector measures how far a sample is
from the training data (distance to the nearest of a few prototypes per
class, in standardised feature space) and flags it as "no sign" when it is
further than almost all genuine held-out signs.

The threshold is the `quantile` (default 99%) of distances measured on
held-out groups, so about 1% of real signs are rejected by design.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans


class NoveltyDetector:
    def __init__(self, prototypes_per_class: int = 8, quantile: float = 0.99, seed: int = 0):
        self.k, self.quantile, self.seed = prototypes_per_class, quantile, seed
        self.mean_: np.ndarray | None = None
        self.scale_: np.ndarray | None = None
        self.prototypes_: np.ndarray | None = None
        self.threshold_: float = np.inf

    def _std(self, X: np.ndarray) -> np.ndarray:
        return (np.asarray(X, dtype=np.float64) - self.mean_) / self.scale_

    def fit(self, X: np.ndarray, y: np.ndarray) -> NoveltyDetector:
        self.mean_ = X.mean(0)
        self.scale_ = X.std(0) + 1e-6
        Z = self._std(X)
        protos = []
        for c in np.unique(y):
            Zc = Z[y == c]
            k = min(self.k, len(Zc))
            protos.append(KMeans(k, n_init=3, random_state=self.seed).fit(Zc).cluster_centers_)
        self.prototypes_ = np.vstack(protos)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        """Distance to the nearest prototype (bigger = more unusual)."""
        Z = self._std(np.atleast_2d(X))
        d2 = (Z ** 2).sum(1)[:, None] - 2 * Z @ self.prototypes_.T + (self.prototypes_ ** 2).sum(1)[None, :]
        return np.sqrt(np.maximum(d2.min(1), 0))

    def calibrate(self, held_out_scores: np.ndarray) -> NoveltyDetector:
        self.threshold_ = float(np.quantile(held_out_scores, self.quantile))
        return self

    def is_novel(self, X: np.ndarray) -> np.ndarray:
        return self.score(X) > self.threshold_

    def to_dict(self) -> dict:
        return {"mean": self.mean_.tolist(), "scale": self.scale_.tolist(),
                "prototypes": np.round(self.prototypes_, 4).tolist(), "threshold": self.threshold_}
