"""Frame-by-frame recognition logic, independent of the camera and UI.

SignRecognizer  model probabilities -> mode-aware, smoothed, thresholded label
WordBuilder     stable labels -> text (hold-to-add, auto-space, manual edits)

Both are pure Python + NumPy so they can be unit-tested without a webcam.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from asl import config
from asl.features import FEATURE_VERSION, landmark_features
from asl.labels import LETTER, MODES, PHRASE, mode_outputs, output_label


@dataclass
class Prediction:
    label: str | None          # None = no hand, or not confident enough
    confidence: float          # smoothed probability of `label` (or of the best guess)
    best_guess: str | None     # top label even when below the threshold
    top3: list[tuple[str, float]] = field(default_factory=list)


class SignRecognizer:
    def __init__(self, model_path: Path | str = config.MODEL_PATH, bundle: dict | None = None,
                 smoothing: float = config.SMOOTHING, min_confidence: float = config.MIN_CONFIDENCE):
        if bundle is None:
            import joblib
            path = Path(model_path)
            if not path.exists():
                raise FileNotFoundError(f"{path} not found. Train a model first: python -m asl.dataset && python -m asl.train")
            bundle = joblib.load(path)
        if bundle.get("feature_version") != FEATURE_VERSION:
            raise ValueError("Model was trained with different features; retrain with python -m asl.train")
        self.model = bundle["model"]
        self.classes = [int(c) for c in bundle["classes"]]
        self.smoothing = smoothing
        self.min_confidence = min_confidence
        # Per mode: a matrix that sums class probabilities into output labels.
        self._labels: dict[str, list[str]] = {}
        self._merge: dict[str, np.ndarray] = {}
        for mode in MODES:
            labels = [lab for lab in mode_outputs(mode) if any(output_label(c, mode) == lab for c in self.classes)]
            m = np.zeros((len(self.classes), len(labels)))
            for i, c in enumerate(self.classes):
                lab = output_label(c, mode)
                if lab in labels:
                    m[i, labels.index(lab)] = 1.0
            self._labels[mode], self._merge[mode] = labels, m
        self._state: np.ndarray | None = None
        self._state_mode: str | None = None

    def reset(self) -> None:
        self._state = None

    def class_probabilities(self, points: np.ndarray, handedness: str) -> np.ndarray:
        x = landmark_features(points, handedness)[None, :]
        return self.model.predict_proba(x)[0]

    def mode_probabilities(self, class_probs: np.ndarray, mode: str) -> np.ndarray:
        """Merge look-alike classes into the labels valid in `mode`.

        Deliberately *not* renormalised: if the hand shows a letter while in
        PHRASE mode, the phrase probabilities stay low and nothing is added,
        instead of the least-unlikely phrase being blown up to high confidence.
        """
        return class_probs @ self._merge[mode]

    def update(self, points: np.ndarray | None, handedness: str = "Right", mode: str = LETTER) -> Prediction:
        if points is None:
            self.reset()
            return Prediction(None, 0.0, None)
        p = self.mode_probabilities(self.class_probabilities(points, handedness), mode)
        if self._state is None or self._state_mode != mode or len(self._state) != len(p):
            self._state, self._state_mode = p, mode
        else:  # exponential moving average over frames
            self._state = self.smoothing * self._state + (1 - self.smoothing) * p
        labels = self._labels[mode]
        order = np.argsort(self._state)[::-1]
        top3 = [(labels[i], float(self._state[i])) for i in order[:3]]
        best, conf = top3[0]
        return Prediction(best if conf >= self.min_confidence else None, conf, best, top3)


class WordBuilder:
    """Builds text from a stream of stable predictions.

    * Holding a sign for `hold_seconds` adds it once. To add the same letter
      twice ("LL" in HELLO) lower the hand or change sign in between. (The old
      app refused any repeated letter, so HELLO could not be spelled.)
    * No hand for `space_seconds` adds a single space.
    * Phrases are added as whole words.
    """

    def __init__(self, hold_seconds: float = config.HOLD_SECONDS, space_seconds: float = config.SPACE_SECONDS,
                 auto_commit: bool = config.AUTO_COMMIT):
        self.hold_seconds, self.space_seconds, self.auto_commit = hold_seconds, space_seconds, auto_commit
        self.text = ""
        self._candidate: str | None = None
        self._since: float | None = None
        self._armed = True          # may the current candidate be committed?
        self._no_hand_since: float | None = None
        self._space_added = False

    def hold_progress(self, now: float) -> float:
        if self._candidate is None or self._since is None or not self._armed:
            return 0.0
        return min(1.0, (now - self._since) / self.hold_seconds)

    def add(self, label: str) -> None:
        if len(label) > 1:  # phrase
            if self.text and not self.text.endswith(" "):
                self.text += " "
            self.text += label + " "
        else:
            self.text += label
        self._space_added = False

    def update(self, label: str | None, hand_present: bool, now: float) -> str | None:
        """Feed one frame. Returns the label that was just added, if any."""
        if not hand_present:
            self._candidate, self._since, self._armed = None, None, True
            if self._no_hand_since is None:
                self._no_hand_since = now
            elif (self.auto_commit and not self._space_added and self.text and not self.text.endswith(" ")
                  and now - self._no_hand_since >= self.space_seconds):
                self.text += " "
                self._space_added = True
            return None
        self._no_hand_since = None
        if label != self._candidate:
            self._candidate, self._since, self._armed = label, now, True
            return None
        if (self.auto_commit and label is not None and self._armed
                and now - self._since >= self.hold_seconds):
            self.add(label)
            self._armed = False
            return label
        return None

    def commit(self, label: str | None) -> bool:
        """Manual add (ENTER)."""
        if not label:
            return False
        self.add(label)
        self._armed = False
        return True

    def space(self) -> None:
        if self.text and not self.text.endswith(" "):
            self.text += " "

    def backspace(self) -> None:
        self.text = self.text[:-1]

    def clear(self) -> None:
        self.text = ""
        self._candidate, self._since, self._armed = None, None, True


__all__ = ["Prediction", "SignRecognizer", "WordBuilder", "LETTER", "PHRASE"]
